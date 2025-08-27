#!/usr/bin/env python3
"""
SMSC (Short Message Service Center) Simulator
Simula um centro de mensagens SMS para testes locais
"""

import http.server
import socketserver
import urllib.parse
import json
import logging
import ssl
import os
import mimetypes
import sys
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

# Global configuration
CONFIG_FILE = 'server_config.json'
server_config = {}

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smsc_simulator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_server_config():
    """Load server configuration from JSON file"""
    global server_config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                server_config = json.load(f)
                logger.info(f"Configuration loaded from {CONFIG_FILE}")
        else:
            # Default configuration
            server_config = {
                "host": "localhost",
                "port": 8080,
                "web_port": 8080,
                "sms_port": 8081,
                "https_port": 8443,
                "timeout": 30,
                "max_connections": 100,
                "version": "1.0.0",
                "log_level": "INFO"
            }
            save_server_config()
            logger.info("Default configuration created")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        # Use default values if loading fails
        server_config = {
            "host": "localhost",
            "port": 8080,
            "web_port": 8080,
            "sms_port": 8081,
            "https_port": 8443,
            "timeout": 30,
            "max_connections": 100,
            "version": "1.0.0",
            "log_level": "INFO"
        }
    
    return server_config

def save_server_config():
    """Save server configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(server_config, f, indent=4, ensure_ascii=False)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")

class APDUParser:
    """Parser para comandos APDU (Application Protocol Data Unit)"""
    
    @staticmethod
    def parse_hex_string(hex_data: str) -> Dict:
        """Parse dados hexadecimais do comando SMS"""
        try:
            # Remove espaços e converte para maiúsculas
            hex_clean = hex_data.replace(' ', '').upper()
            
            # Estrutura básica do APDU
            result = {
                'raw_data': hex_data,
                'hex_clean': hex_clean,
                'length': len(hex_clean) // 2,
                'timestamp': datetime.now().isoformat(),
                'parsed': True
            }
            
            # Análise básica do APDU (simplificada)
            if len(hex_clean) >= 4:
                result['message_type'] = hex_clean[:2]
                result['message_reference'] = hex_clean[2:4]
            
            # Extrai informações do número de telefone se presente
            if '91' in hex_clean:  # Indicador de número internacional
                idx = hex_clean.find('91')
                result['number_type'] = 'international'
                result['number_indicator_pos'] = idx
            
            logger.info(f"APDU parsed successfully: {len(hex_clean)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing APDU: {e}")
            return {
                'raw_data': hex_data,
                'parsed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

class SMSHandler:
    """Handler para processar mensagens SMS"""
    
    def __init__(self):
        self.message_counter = 0
        self.processed_messages = []
        self.successful_messages = 0
        self.failed_messages = 0
        self.start_time = datetime.now()
    
    def process_sms(self, apdu_data: Dict, msisdn: str = "") -> Dict:
        """Processa uma mensagem SMS"""
        self.message_counter += 1
        
        response = {
            'message_id': self.message_counter,
            'status': 'received',
            'msisdn': msisdn,
            'apdu_info': apdu_data,
            'processed_at': datetime.now().isoformat(),
            'response_code': '00'  # Sucesso
        }
        
        # Store message for statistics
        message_data = {
            'id': self.message_counter,
            'msisdn': msisdn,
            'timestamp': datetime.now().isoformat(),
            'status': 'success' if response['response_code'] == '00' else 'failed',
            'apdu_info': apdu_data,
            'apdu_hex': apdu_data.get('raw_data', ''),
            'direction': 'received'  # Mensagem recebida do software externo
        }
        self.processed_messages.append(message_data)
        
        # Update counters
        if response['response_code'] == '00':
            self.successful_messages += 1
        else:
            self.failed_messages += 1
        
        # Keep only last 100 messages
        if len(self.processed_messages) > 100:
            self.processed_messages.pop(0)
        
        logger.info(f"SMS processed - ID: {self.message_counter}, MSISDN: {msisdn}")
        
        return response
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do simulador"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Get last message time
        last_message_time = None
        if self.processed_messages:
            last_msg = self.processed_messages[-1]
            if isinstance(last_msg, dict) and 'timestamp' in last_msg:
                last_message_time = last_msg['timestamp']
            elif hasattr(last_msg, 'get'):
                last_message_time = last_msg.get('timestamp')
        
        return {
            'total_messages': self.message_counter,
            'successful_messages': self.successful_messages,
            'failed_messages': self.failed_messages,
            'uptime_seconds': int(uptime),
            'messages_per_minute': round((self.message_counter / max(uptime / 60, 1)), 2),
            'last_processed': self.processed_messages[-1] if self.processed_messages else None,
            'last_message_time': last_message_time,
            'start_time': self.start_time.isoformat()
        }
    
    def clear_messages(self):
        """Clear all processed messages and reset counters"""
        self.processed_messages.clear()
        self.message_counter = 0
        self.successful_messages = 0
        self.failed_messages = 0
        logger.info("All messages and statistics cleared")
    
    def reset_statistics(self):
        """Reset all statistics and counters"""
        self.processed_messages.clear()
        self.message_counter = 0
        self.successful_messages = 0
        self.failed_messages = 0
        self.start_time = datetime.now()
        logger.info("Statistics reset successfully")
    
    def add_message(self, sms_data: Dict):
        """Adiciona uma mensagem processada via HTTP"""
        self.message_counter += 1
        
        # Criar entrada de mensagem padronizada
        message_data = {
            'id': self.message_counter,
            'timestamp': sms_data.get('timestamp', datetime.now().isoformat()),
            'status': 'success',
            'source': sms_data.get('source', 'http'),
            'format': sms_data.get('format', 'unknown'),
            'raw_data': sms_data.get('raw_data', ''),
            'user_data': sms_data.get('user_data', ''),
            'destination_address': sms_data.get('destination_address', ''),
            'protocol_identifier': sms_data.get('protocol_identifier', ''),
            'data_coding_scheme': sms_data.get('data_coding_scheme', ''),
            'query_params': sms_data.get('query_params', {}),
            'direction': 'received'  # Mensagem recebida do software externo
        }
        
        self.processed_messages.append(message_data)
        self.successful_messages += 1
        
        # Manter apenas as últimas 100 mensagens
        if len(self.processed_messages) > 100:
            self.processed_messages.pop(0)
        
        # Salvar mensagem em arquivo compartilhado para sincronização entre processos
        self._save_message_to_shared_file(message_data)
        
        logger.info(f"HTTP SMS message added - ID: {self.message_counter}, Source: {message_data['source']}")
        
        return message_data
    
    def simulate_outgoing_message(self, destination_msisdn: str, message_text: str = "Mensagem de teste do simulador"):
        """Simula uma mensagem enviada pelo simulador para o software externo"""
        self.message_counter += 1
        
        message_data = {
            'id': self.message_counter,
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'source': 'simulator',
            'format': 'outgoing_simulation',
            'raw_data': f"SIMULATED_OUTGOING_{self.message_counter}",
            'user_data': message_text,
            'destination_address': destination_msisdn,
            'protocol_identifier': '00',
            'data_coding_scheme': '00',
            'query_params': {},
            'direction': 'sent'  # Mensagem enviada pelo simulador
        }
        
        self.processed_messages.append(message_data)
        self.successful_messages += 1
        
        # Manter apenas as últimas 100 mensagens
        if len(self.processed_messages) > 100:
            self.processed_messages.pop(0)
        
        # Salvar mensagem em arquivo compartilhado
        self._save_message_to_shared_file(message_data)
        
        logger.info(f"Simulated outgoing message - ID: {self.message_counter}, Destination: {destination_msisdn}")
        
        return message_data
    
    def _save_message_to_shared_file(self, message_data: Dict):
        """Salva mensagem em arquivo compartilhado"""
        try:
            import json
            import os
            
            shared_file = 'shared_messages.json'
            messages = []
            
            # Ler mensagens existentes
            if os.path.exists(shared_file):
                try:
                    with open(shared_file, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                except:
                    messages = []
            
            # Adicionar nova mensagem
            messages.append(message_data)
            
            # Manter apenas as últimas 100 mensagens
            if len(messages) > 100:
                messages = messages[-100:]
            
            # Salvar de volta
            with open(shared_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving message to shared file: {e}")
    
    def load_shared_messages(self):
        """Carrega mensagens do arquivo compartilhado"""
        try:
            import json
            import os
            
            shared_file = 'shared_messages.json'
            if os.path.exists(shared_file):
                with open(shared_file, 'r', encoding='utf-8') as f:
                    shared_messages = json.load(f)
                
                # Mesclar com mensagens locais, evitando duplicatas
                existing_ids = {msg.get('id') for msg in self.processed_messages}
                for msg in shared_messages:
                    if msg.get('id') not in existing_ids:
                        self.processed_messages.append(msg)
                
                # Manter apenas as últimas 100 mensagens
                if len(self.processed_messages) > 100:
                    self.processed_messages = self.processed_messages[-100:]
                    
        except Exception as e:
            logger.error(f"Error loading shared messages: {e}")

class SMSCRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handler para requisições HTTP do simulador SMSC"""
    
    def __init__(self, *args, apdu_parser=None, sms_handler=None, **kwargs):
        self.apdu_parser = apdu_parser or APDUParser()
        self.sms_handler = sms_handler or SMSHandler()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Processa requisições GET"""
        try:
            # Parse da URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            logger.info(f"Received request: {self.path}")
            
            # Verifica se é uma requisição para o smshandler
            if '/cgi-bin/smshandler.pl' in parsed_url.path:
                self._handle_sms_request(query_params)
            elif parsed_url.path == '/status':
                self._handle_status_request()
            elif parsed_url.path == '/stats':
                self._handle_stats_request()
            elif parsed_url.path == '/' or parsed_url.path == '/index.html':
                self._serve_static_file('static/index.html')
            elif parsed_url.path.startswith('/static/'):
                self._serve_static_file(parsed_url.path[1:])  # Remove leading slash
            elif parsed_url.path == '/messages':
                self._handle_messages_request()
            elif parsed_url.path == '/simulate-outgoing':
                self._handle_simulate_outgoing_request(parsed_url.query)
            elif parsed_url.path == '/config/reset-stats':
                self._handle_reset_stats_request()
            elif parsed_url.path == '/cgi-bin/smshandler.pl':
                self._handle_sms_request_port80(parsed_url.query)
            elif parsed_url.path == '/config':
                self._handle_config_request()
            else:
                self._handle_default_request()
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self._send_error_response(500, str(e))
    
    def _handle_sms_request(self, query_params: Dict):
        """Processa requisição SMS"""
        submit_data = query_params.get('submit', [''])[0]
        msisdn = query_params.get('MSISDN', [''])[0]
        
        if submit_data:
            # Parse do APDU
            apdu_info = self.apdu_parser.parse_hex_string(submit_data)
            
            # Processa SMS
            sms_response = self.sms_handler.process_sms(apdu_info, msisdn)
            
            # Resposta de sucesso
            response_data = {
                'status': 'OK',
                'message': 'SMS received and processed',
                'message_id': sms_response['message_id'],
                'response_code': '00'
            }
            
            self._send_json_response(200, response_data)
        else:
            self._send_error_response(400, "Missing submit parameter")
    
    def _handle_status_request(self):
        """Retorna status do simulador"""
        status_data = {
            'status': 'running',
            'service': 'SMSC Simulator',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }
        self._send_json_response(200, status_data)
    
    def _handle_stats_request(self):
        """Retorna estatísticas"""
        stats = self.sms_handler.get_statistics()
        self._send_json_response(200, stats)
    
    def _handle_config_request(self):
        """Retorna configurações atuais"""
        # Format uptime to show only days, hours, and minutes
        uptime_delta = datetime.now() - self.sms_handler.start_time
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            uptime_str = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        else:
            uptime_str = f"{minutes}m"
        
        config_data = {
            'host': server_config.get('host', 'localhost'),
            'web_port': server_config.get('web_port', 8080),
            'sms_port': server_config.get('sms_port', 8081),
            'https_port': server_config.get('https_port', 8443),
            'timeout': server_config.get('timeout', 30),
            'max_connections': server_config.get('max_connections', 100),
            'version': server_config.get('version', '1.0.0'),
            'log_level': server_config.get('log_level', 'INFO'),
            'total_messages': len(self.sms_handler.processed_messages),
            'successful_messages': self.sms_handler.successful_messages,
            'failed_messages': self.sms_handler.failed_messages,
            'uptime': uptime_str
        }
        self._send_json_response(200, config_data)
    
    def _handle_reset_stats_request(self):
        """Reseta as estatísticas"""
        self.sms_handler.reset_statistics()
        response_data = {
            'status': 'success',
            'message': 'Estatísticas resetadas com sucesso',
            'timestamp': datetime.now().isoformat()
        }
        self._send_json_response(200, response_data)
    
    def _handle_update_port_request(self):
        """Handle port update request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            new_port = data.get('port')
            if not new_port or not isinstance(new_port, int) or new_port < 1024 or new_port > 65535:
                self._send_json_response(400, {'error': 'Porta deve estar entre 1024 e 65535'})
                return
            
            # Update port in configuration and save
            server_config['port'] = new_port
            save_server_config()
            logger.info(f"Port updated to: {new_port}")
            
            response = {
                'success': True,
                'message': f'Porta atualizada para {new_port}. Reinicie o servidor para aplicar.',
                'new_port': new_port
            }
            self._send_json_response(200, response)
            
        except Exception as e:
            self._send_json_response(500, {'error': f'Erro interno: {str(e)}'})
            logger.error(f"Erro ao processar atualização de porta: {e}")
    
    def _handle_update_sms_port_request(self):
        """Handle SMS port update request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            new_port = data.get('sms_port')
            if not isinstance(new_port, int) or new_port < 1024 or new_port > 65535:
                self._send_json_response(400, {'error': 'Porta SMS deve ser um número entre 1024 e 65535'})
                return
            
            # Update SMS port in configuration and save
            server_config['sms_port'] = new_port
            save_server_config()
            logger.info(f"SMS port updated to: {new_port}")
            
            response = {
                'success': True,
                'message': f'Porta SMS atualizada para {new_port}. Reinicie o servidor para aplicar.',
                'new_sms_port': new_port
            }
            self._send_json_response(200, response)
            
        except Exception as e:
            self._send_json_response(500, {'error': f'Erro interno: {str(e)}'})
            logger.error(f"Erro ao processar atualização de porta SMS: {e}")
    
    def _handle_update_web_port_request(self):
        """Handle Web port update request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            new_port = data.get('web_port')
            if not isinstance(new_port, int) or new_port < 1024 or new_port > 65535:
                self._send_json_response(400, {'error': 'Porta Web deve ser um número entre 1024 e 65535'})
                return
            
            # Update Web port in configuration and save
            server_config['web_port'] = new_port
            save_server_config()
            logger.info(f"Web port updated to: {new_port}")
            
            response = {
                'success': True,
                'message': f'Porta Web atualizada para {new_port}. Reinicie o servidor para aplicar.',
                'new_web_port': new_port
            }
            self._send_json_response(200, response)
            
        except Exception as e:
            self._send_json_response(500, {'error': f'Erro interno: {str(e)}'})
            logger.error(f"Erro ao processar atualização de porta Web: {e}")
    
    def _handle_update_host_request(self):
        """Handle host update request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            new_host = data.get('host', '').strip()
            if not new_host:
                self._send_json_response(400, {'error': 'Host não pode estar vazio'})
                return
            
            # Update host in configuration and save
            server_config['host'] = new_host
            save_server_config()
            logger.info(f"Host updated to: {new_host}")
            
            response = {
                'success': True,
                'message': f'Host atualizado para {new_host}. Reinicie o servidor para aplicar.',
                'new_host': new_host
            }
            self._send_json_response(200, response)
            
        except Exception as e:
            self._send_json_response(500, {'error': f'Erro interno: {str(e)}'})
            logger.error(f"Erro ao processar atualização de host: {e}")
    
    def _handle_update_timeout_request(self):
        """Handle timeout update request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            new_timeout = data.get('timeout')
            if not isinstance(new_timeout, int) or new_timeout < 1 or new_timeout > 300:
                self._send_json_response(400, {'error': 'Timeout deve estar entre 1 e 300 segundos'})
                return
            
            # Update timeout in configuration and save
            server_config['timeout'] = new_timeout
            save_server_config()
            logger.info(f"Timeout updated to: {new_timeout}")
            
            response = {
                'success': True,
                'message': f'Timeout atualizado para {new_timeout} segundos',
                'new_timeout': new_timeout
            }
            self._send_json_response(200, response)
            
        except Exception as e:
            self._send_json_response(500, {'error': f'Erro interno: {str(e)}'})
            logger.error(f"Erro ao processar atualização de timeout: {e}")
    
    def _handle_update_max_connections_request(self):
        """Handle max connections update request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            new_max_connections = data.get('max_connections')
            if not isinstance(new_max_connections, int) or new_max_connections < 1 or new_max_connections > 1000:
                self._send_json_response(400, {'error': 'Máximo de conexões deve estar entre 1 e 1000'})
                return
            
            # Update max connections in configuration and save
            server_config['max_connections'] = new_max_connections
            save_server_config()
            logger.info(f"Max connections updated to: {new_max_connections}")
            
            response = {
                'success': True,
                'message': f'Máximo de conexões atualizado para {new_max_connections}',
                'new_max_connections': new_max_connections
            }
            self._send_json_response(200, response)
            
        except Exception as e:
            self._send_json_response(500, {'error': f'Erro interno: {str(e)}'})
            logger.error(f"Erro ao processar atualização de máximo de conexões: {e}")
    

    
    def _handle_update_log_level_request(self):
        """Handle log level update request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            new_log_level = data.get('log_level', '').upper()
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
            
            if new_log_level not in valid_levels:
                self._send_json_response(400, {'error': f'Nível de log deve ser um de: {valid_levels}'})
                return
            
            # Update log level in configuration and save
            server_config['log_level'] = new_log_level
            save_server_config()
            logger.info(f"Log level updated to: {new_log_level}")
            
            response = {
                'success': True,
                'message': f'Nível de log atualizado para {new_log_level}',
                'new_log_level': new_log_level
            }
            self._send_json_response(200, response)
            
        except Exception as e:
            self._send_json_response(500, {'error': f'Erro interno: {str(e)}'})
            logger.error(f"Erro ao processar atualização de nível de log: {e}")
    
    def _handle_restart_server_request(self):
        """Handle server restart request"""
        try:
            logger.info("Server restart requested")
            
            # Send success response first
            response_data = {
                'success': True,
                'message': 'Servidor será reiniciado em alguns segundos...'
            }
            self._send_json_response(200, response_data)
            
            # Schedule server restart in a separate thread
            def restart_server():
                time.sleep(2)  # Give time for response to be sent
                logger.info("Restarting server...")
                
                # Gracefully shutdown the current server
                if hasattr(self.server, 'shutdown'):
                    self.server.shutdown()
                
                # Start new process
                
                # Use subprocess to start a new instance
                if sys.platform.startswith('win'):
                    # Windows specific restart
                    subprocess.Popen([sys.executable] + sys.argv, 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # Unix/Linux restart
                    os.execv(sys.executable, ['python'] + sys.argv)
                
                # Exit current process
                os._exit(0)
            
            restart_thread = threading.Thread(target=restart_server)
            restart_thread.daemon = True
            restart_thread.start()
            
        except Exception as e:
            logger.error(f"Error handling restart server request: {e}")
            self._send_error_response(500, f"Internal server error: {str(e)}")
    
    def _handle_default_request(self):
        """Resposta padrão"""
        response_data = {
            'message': 'SMSC Simulator is running',
            'endpoints': {
                'sms_handler': '/cgi-bin/smshandler.pl',
                'status': '/status',
                'statistics': '/stats',
                'messages': '/messages',
                'dashboard': '/'
            }
        }
        self._send_json_response(200, response_data)
    
    def _send_json_response(self, status_code: int, data: Dict):
        """Envia resposta JSON"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error_response(self, status_code: int, message: str):
        """Envia resposta de erro"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        error_data = {
            'error': True,
            'message': message,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        
        json_data = json.dumps(error_data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            
            if parsed_url.path == '/config/update-port':
                self._handle_update_port_request()
            elif parsed_url.path == '/config/update-host':
                self._handle_update_host_request()
            elif parsed_url.path == '/config/update-timeout':
                self._handle_update_timeout_request()
            elif parsed_url.path == '/config/update-max-connections':
                self._handle_update_max_connections_request()

            elif parsed_url.path == '/config/update-log-level':
                self._handle_update_log_level_request()
            elif parsed_url.path == '/config/restart-server':
                self._handle_restart_server_request()
            elif parsed_url.path == '/cgi-bin/smshandler.pl':
                # Lê dados do corpo da requisição
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Parse dos dados POST
                post_params = urllib.parse.parse_qs(post_data)
                
                # Converte para o formato esperado pelo _handle_sms_request
                query_params = {}
                if 'apdu_hex' in post_params:
                    query_params['submit'] = post_params['apdu_hex']
                if 'msisdn' in post_params:
                    query_params['MSISDN'] = post_params['msisdn']
                
                self._handle_sms_request(query_params)
            elif parsed_url.path == '/sms-reply':
                self._handle_sms_reply_request()
            else:
                self._send_error_response(404, "Not Found")
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self._send_error_response(500, "Internal Server Error")
    
    def do_OPTIONS(self):
        """Processa requisições OPTIONS para CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_DELETE(self):
        """Processa requisições DELETE"""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            
            if parsed_url.path == '/messages':
                self._handle_clear_messages()
            else:
                self._send_error_response(404, 'Endpoint not found')
                
        except Exception as e:
            logger.error(f"Error processing DELETE request: {e}")
            self._send_error_response(500, str(e))
    
    def _serve_static_file(self, file_path: str):
        """Serve arquivos estáticos (HTML, CSS, JS)"""
        try:
            # Verificação de segurança - previne directory traversal
            if '..' in file_path or file_path.startswith('/'):
                self._send_error_response(403, 'Access denied')
                return
            
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                self._send_error_response(404, 'File not found')
                return
            
            # Determina o tipo de conteúdo
            content_type, _ = mimetypes.guess_type(full_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Lê e serve o arquivo
            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            logger.error(f"Error serving static file {file_path}: {e}")
            self._send_error_response(500, 'Internal server error')
    
    def _handle_messages_request(self):
        """Retorna mensagens processadas"""
        # Carregar mensagens compartilhadas de outros processos
        self.sms_handler.load_shared_messages()
        
        messages_data = {
            'messages': self.sms_handler.processed_messages,
            'total_count': len(self.sms_handler.processed_messages),
            'timestamp': datetime.now().isoformat()
        }
        self._send_json_response(200, messages_data)
    
    def _handle_simulate_outgoing_request(self, query_string: str):
        """Simula uma mensagem enviada pelo simulador"""
        try:
            from urllib.parse import parse_qs, unquote
            query_params = parse_qs(query_string)
            
            # Extrair parâmetros
            destination = query_params.get('destination', ['+5511999999999'])[0]
            message_text = query_params.get('message', ['Mensagem de teste do simulador'])[0]
            
            # Simular mensagem enviada
            message_data = self.sms_handler.simulate_outgoing_message(
                destination_msisdn=unquote(destination),
                message_text=unquote(message_text)
            )
            
            response = {
                'status': 'OK',
                'message': 'Outgoing message simulated successfully',
                'message_id': message_data['id'],
                'destination': destination,
                'text': message_text
            }
            
            self._send_json_response(200, response)
            
        except Exception as e:
            logger.error(f"Error simulating outgoing message: {e}")
            self._send_json_response(500, {'status': 'ERROR', 'message': str(e)})
    
    def _handle_sms_request_port80(self, query_string: str):
        """Simula o comportamento da porta 80 para SMS"""
        try:
            from urllib.parse import parse_qs, unquote
            query_params = parse_qs(query_string)
            
            # Extrair parâmetros SMS
            submit_data = query_params.get('submit', [''])[0]
            sms_submit = unquote(submit_data) if submit_data else ''
            
            # Variáveis especiais suportadas
            sms_submit_ud = query_params.get('sms_submit_ud', [''])[0]  # user data
            sms_submit_da = query_params.get('sms_submit_da', [''])[0]  # destination address
            sms_submit_pid = query_params.get('sms_submit_pid', [''])[0]  # protocol identifier
            sms_submit_dcs = query_params.get('sms_submit_dcs', [''])[0]  # data coding scheme
            
            # Verificar se pelo menos um parâmetro foi fornecido
            if not any([sms_submit, sms_submit_ud, sms_submit_da, sms_submit_pid, sms_submit_dcs]):
                self._send_error_response(400, "Missing SMS parameters")
                return
            
            # Processar e extrair informações do SMS
            sms_data = {
                'raw_data': sms_submit,
                'user_data': sms_submit_ud,
                'destination_address': sms_submit_da,
                'protocol_identifier': sms_submit_pid,
                'data_coding_scheme': sms_submit_dcs,
                'timestamp': datetime.now().isoformat(),
                'source': 'port_80_simulation',
                'format': 'sms_submit_variables',
                'query_params': dict(query_params)
            }
            
            # Armazenar mensagem
            self.sms_handler.add_message(sms_data)
            
            # Log detalhado da requisição
            log_parts = []
            if sms_submit:
                log_parts.append(f"SMS: {sms_submit[:50]}...")
            if sms_submit_ud:
                log_parts.append(f"UserData: {sms_submit_ud[:30]}...")
            if sms_submit_da:
                log_parts.append(f"DestAddr: {sms_submit_da}")
            if sms_submit_pid:
                log_parts.append(f"PID: {sms_submit_pid}")
            if sms_submit_dcs:
                log_parts.append(f"DCS: {sms_submit_dcs}")
            
            logger.info(f"SMS received via port 80 simulation - {', '.join(log_parts)}")
            
            # Resposta de sucesso
            response = {
                'status': 'success',
                'message': 'SMS received and processed successfully',
                'timestamp': datetime.now().isoformat(),
                'processed_parameters': {
                    'sms_submit': bool(sms_submit),
                    'sms_submit_ud': bool(sms_submit_ud),
                    'sms_submit_da': bool(sms_submit_da),
                    'sms_submit_pid': bool(sms_submit_pid),
                    'sms_submit_dcs': bool(sms_submit_dcs)
                }
            }
            
            self._send_json_response(200, response)
            
        except Exception as e:
            logger.error(f"Error processing SMS submit request: {e}")
            self._send_error_response(500, f'Error processing SMS: {str(e)}')
    
    def _handle_clear_messages(self):
        """Limpa todas as mensagens armazenadas"""
        try:
            self.sms_handler.clear_messages()
            
            response = {
                'status': 'success',
                'message': 'All messages cleared successfully',
                'timestamp': datetime.now().isoformat()
            }
            
            self._send_json_response(200, response)
            logger.info("Messages cleared via API")
            
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            self._send_error_response(500, f'Error clearing messages: {str(e)}')
    
    def _handle_sms_reply_request(self):
        """Processa resposta de SMS"""
        try:
            # Lê dados do corpo da requisição
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse dos dados POST
            post_params = urllib.parse.parse_qs(post_data)
            
            # Extrai parâmetros necessários
            msisdn = post_params.get('msisdn', [''])[0]
            message = post_params.get('message', [''])[0]
            original_message_id = post_params.get('original_message_id', [''])[0]
            
            if not msisdn or not message:
                self._send_error_response(400, "Missing required parameters: msisdn and message")
                return
            
            # Cria dados da mensagem de resposta
            reply_data = {
                'msisdn': msisdn,
                'message': message,
                'original_message_id': original_message_id,
                'timestamp': datetime.now().isoformat(),
                'direction': 'outgoing',
                'type': 'reply',
                'status': 'sent'
            }
            
            # Adiciona mensagem de resposta
            self.sms_handler.add_message(reply_data)
            
            # Log da resposta
            logger.info(f"SMS reply sent to {msisdn}: {message[:50]}...")
            
            # Resposta de sucesso
            response = {
                'status': 'success',
                'message': 'SMS reply sent successfully',
                'timestamp': datetime.now().isoformat(),
                'reply_to': msisdn,
                'original_message_id': original_message_id
            }
            
            self._send_json_response(200, response)
            
        except Exception as e:
            logger.error(f"Error processing SMS reply: {e}")
            self._send_error_response(500, f'Error processing SMS reply: {str(e)}')
    
    def log_message(self, format, *args):
        """Override para usar nosso logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def create_web_handler_class(apdu_parser, sms_handler):
    """Factory para criar classe de handler da interface web"""
    class WebRequestHandler(SMSCRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, apdu_parser=apdu_parser, sms_handler=sms_handler, **kwargs)
        
        def do_POST(self):
            """Handle POST requests - only web interface endpoints"""
            if self.path == '/config/update-port':
                self._handle_update_port_request()
            elif self.path == '/config/update-sms-port':
                self._handle_update_sms_port_request()
            elif self.path == '/config/update-web-port':
                self._handle_update_web_port_request()
            elif self.path == '/config/update-host':
                self._handle_update_host_request()
            elif self.path == '/config/update-timeout':
                self._handle_update_timeout_request()
            elif self.path == '/config/update-max-connections':
                self._handle_update_max_connections_request()
            elif self.path == '/config/update-log-level':
                self._handle_update_log_level_request()
            elif self.path == '/config/restart-server':
                self._handle_restart_server_request()
            elif self.path == '/test-sms':
                self._handle_sms_test_request()
            elif self.path == '/clear-messages':
                self._handle_clear_messages()
            elif self.path == '/reset-stats':
                self._handle_reset_stats_request()
            else:
                self._send_error_response(404, "Endpoint not found")
    
    return WebRequestHandler

def create_sms_handler_class(apdu_parser, sms_handler):
    """Factory para criar classe de handler do SMS"""
    class SMSRequestHandler(SMSCRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, apdu_parser=apdu_parser, sms_handler=sms_handler, **kwargs)
        
        def do_POST(self):
            """Handle POST requests - only SMS handler endpoint"""
            if self.path == '/cgi-bin/smshandler.pl':
                self._handle_sms_request()
            else:
                self._send_error_response(404, "SMS endpoint not found")
        
        def do_GET(self):
            """Handle GET requests - basic status only"""
            if self.path == '/status':
                self._handle_status_request()
            else:
                self._send_error_response(404, "Endpoint not found")
    
    return SMSRequestHandler

def create_http_handler_class(apdu_parser, sms_handler):
    """Factory para criar classe de handler HTTP na porta 80"""
    class HTTPRequestHandler(SMSCRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, apdu_parser=apdu_parser, sms_handler=sms_handler, **kwargs)
        
        def do_GET(self):
            """Handle GET requests - processa formato $(sms_submit)"""
            if self.path.startswith('/cgi-bin/smshandler.pl'):
                self._handle_sms_submit_request()
            elif self.path == '/status':
                self._handle_status_request()
            else:
                self._send_error_response(404, "Endpoint not found")
        
        def do_POST(self):
            """Handle POST requests - processa formato $(sms_submit)"""
            if self.path.startswith('/cgi-bin/smshandler.pl'):
                self._handle_sms_submit_request()
            else:
                self._send_error_response(404, "Endpoint not found")
        
        def _handle_sms_submit_request(self):
            """Processa requisições com formato $(sms_submit) e variáveis especiais"""
            try:
                # Parse da query string
                from urllib.parse import urlparse, parse_qs, unquote
                parsed_url = urlparse(self.path)
                query_params = parse_qs(parsed_url.query)
                
                # Extrair todos os parâmetros suportados
                submit_data = query_params.get('submit', [''])[0]
                sms_submit = unquote(submit_data) if submit_data else ''
                
                # Variáveis especiais suportadas
                sms_submit_ud = query_params.get('sms_submit_ud', [''])[0]  # user data
                sms_submit_da = query_params.get('sms_submit_da', [''])[0]  # destination address
                sms_submit_pid = query_params.get('sms_submit_pid', [''])[0]  # protocol identifier
                sms_submit_dcs = query_params.get('sms_submit_dcs', [''])[0]  # data coding scheme
                
                # Verificar se pelo menos um parâmetro foi fornecido
                if not any([sms_submit, sms_submit_ud, sms_submit_da, sms_submit_pid, sms_submit_dcs]):
                    self._send_error_response(400, "Missing SMS parameters")
                    return
                
                # Processar e extrair informações do SMS
                sms_data = {
                    'raw_data': sms_submit,
                    'user_data': sms_submit_ud,
                    'destination_address': sms_submit_da,
                    'protocol_identifier': sms_submit_pid,
                    'data_coding_scheme': sms_submit_dcs,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'http_port_80',
                    'format': 'sms_submit_variables',
                    'query_params': dict(query_params)
                }
                
                # Tentar extrair informações adicionais do SMS completo
                if sms_submit:
                    try:
                        # Simular parsing básico de SMS PDU (se aplicável)
                        sms_data['message_length'] = len(sms_submit)
                        sms_data['has_full_message'] = True
                    except:
                        pass
                
                # Armazenar mensagem
                self.sms_handler.add_message(sms_data)
                
                # Log detalhado da requisição
                log_parts = []
                if sms_submit:
                    log_parts.append(f"SMS: {sms_submit[:50]}...")
                if sms_submit_ud:
                    log_parts.append(f"UserData: {sms_submit_ud[:30]}...")
                if sms_submit_da:
                    log_parts.append(f"DestAddr: {sms_submit_da}")
                if sms_submit_pid:
                    log_parts.append(f"PID: {sms_submit_pid}")
                if sms_submit_dcs:
                    log_parts.append(f"DCS: {sms_submit_dcs}")
                
                logger.info(f"SMS received via HTTP port 80 - {', '.join(log_parts)}")
                
                # Resposta de sucesso
                response = {
                    'status': 'success',
                    'message': 'SMS received and processed successfully',
                    'timestamp': datetime.now().isoformat(),
                    'processed_parameters': {
                        'sms_submit': bool(sms_submit),
                        'sms_submit_ud': bool(sms_submit_ud),
                        'sms_submit_da': bool(sms_submit_da),
                        'sms_submit_pid': bool(sms_submit_pid),
                        'sms_submit_dcs': bool(sms_submit_dcs)
                    }
                }
                
                self._send_json_response(200, response)
                
            except Exception as e:
                logger.error(f"Error processing SMS submit request: {e}")
                self._send_error_response(500, f'Error processing SMS: {str(e)}')
    
    return HTTPRequestHandler

class SMSCSimulator:
    """Simulador principal SMSC"""
    
    def __init__(self, host='localhost', web_port=8080, sms_port=8081, http_port=80, https_port=443):
        self.host = host
        self.web_port = web_port
        self.sms_port = sms_port
        self.http_port = http_port
        self.https_port = https_port
        self.apdu_parser = APDUParser()
        self.sms_handler = SMSHandler()
        self.web_server = None
        self.sms_server = None
        self.http_server = None
        self.https_server = None
    
    def start_web_server(self):
        """Inicia servidor da interface web"""
        try:
            web_handler_class = create_web_handler_class(self.apdu_parser, self.sms_handler)
            self.web_server = socketserver.TCPServer((self.host, self.web_port), web_handler_class)
            
            logger.info(f"Starting Web Interface server on {self.host}:{self.web_port}")
            self.web_server.serve_forever()
            
        except Exception as e:
            logger.error(f"Error starting Web server: {e}")
            raise
    
    def start_sms_server(self):
        """Inicia servidor do SMS handler"""
        try:
            sms_handler_class = create_sms_handler_class(self.apdu_parser, self.sms_handler)
            self.sms_server = socketserver.TCPServer((self.host, self.sms_port), sms_handler_class)
            
            logger.info(f"Starting SMS Handler server on {self.host}:{self.sms_port}")
            self.sms_server.serve_forever()
            
        except Exception as e:
            logger.error(f"Error starting SMS server: {e}")
            raise
    
    def start_http_server(self):
        """Inicia servidor HTTP na porta 80"""
        try:
            http_handler_class = create_http_handler_class(self.apdu_parser, self.sms_handler)
            self.http_server = socketserver.TCPServer((self.host, self.http_port), http_handler_class)
            
            logger.info(f"Starting HTTP server on {self.host}:{self.http_port}")
            self.http_server.serve_forever()
            
        except OSError as e:
            if "10048" in str(e) or "permission" in str(e).lower():
                logger.warning(f"Cannot start HTTP server on port {self.http_port}: {e}")
                logger.warning("HTTP server on port 80 requires administrator privileges or port is in use")
            else:
                logger.error(f"Error starting HTTP server: {e}")
        except Exception as e:
            logger.error(f"Error starting HTTP server: {e}")
    
    def start_https_server(self, cert_file='server.crt', key_file='server.key'):
        """Inicia servidor HTTPS"""
        try:
            handler_class = create_request_handler_class(self.apdu_parser, self.sms_handler)
            self.https_server = socketserver.TCPServer((self.host, self.https_port), handler_class)
            
            # Configuração SSL
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert_file, key_file)
            self.https_server.socket = context.wrap_socket(self.https_server.socket, server_side=True)
            
            logger.info(f"Starting HTTPS server on {self.host}:{self.https_port}")
            self.https_server.serve_forever()
            
        except Exception as e:
            logger.error(f"Error starting HTTPS server: {e}")
            raise
    
    def stop(self):
        """Para os servidores"""
        if self.web_server:
            self.web_server.shutdown()
            logger.info("Web server stopped")
        
        if self.sms_server:
            self.sms_server.shutdown()
            logger.info("SMS server stopped")
        
        if self.http_server:
            self.http_server.shutdown()
            logger.info("HTTP server stopped")
        
        if self.https_server:
            self.https_server.shutdown()
            logger.info("HTTPS server stopped")

if __name__ == "__main__":
    import threading
    
    # Carregar configurações
    config = load_server_config()
    
    # Criar simulador com configurações carregadas
    simulator = SMSCSimulator(
        host=config['host'],
        web_port=config['web_port'],
        sms_port=config['sms_port'],
        http_port=config['http_port'],
        https_port=config['https_port']
    )
    
    print(f"\n=== SMSC Simulator v{config['version']} ===")
    print(f"Host: {config['host']}")
    print(f"Web Interface Port: {config['web_port']}")
    print(f"SMS Handler Port: {config['sms_port']}")
    print(f"HTTP Port: {config['http_port']}")
    print(f"HTTPS Port: {config['https_port']}")
    print(f"Timeout: {config['timeout']}s")
    print(f"Max Connections: {config['max_connections']}")
    print(f"Log Level: {config['log_level']}")
    print("\nAvailable endpoints:")
    print(f"  - Web Interface: http://{config['host']}:{config['web_port']}/")
    print(f"  - SMS Handler (Port 80): http://{config['host']}/cgi-bin/smshandler.pl?submit=$(sms_submit)")
    print(f"  - SMS Handler: http://{config['host']}:{config['sms_port']}/cgi-bin/smshandler.pl")
    print(f"  - Status (Web): http://{config['host']}:{config['web_port']}/status")
    print(f"  - Status (SMS): http://{config['host']}:{config['sms_port']}/status")
    print(f"  - Statistics: http://{config['host']}:{config['web_port']}/stats")
    print(f"  - Configuration: http://{config['host']}:{config['web_port']}/config")
    print("\nPress Ctrl+C to stop the servers\n")
    
    try:
        # Iniciar servidor SMS em thread separada
        sms_thread = threading.Thread(target=simulator.start_sms_server, daemon=True)
        sms_thread.start()
        
        # Iniciar servidor HTTP (porta 80) em thread separada
        http_thread = threading.Thread(target=simulator.start_http_server, daemon=True)
        http_thread.start()
        
        # Iniciar servidor web na thread principal
        simulator.start_web_server()
    except KeyboardInterrupt:
        print("\nServers stopped by user")
    except Exception as e:
        print(f"Server error: {e}")