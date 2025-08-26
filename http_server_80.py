#!/usr/bin/env python3
"""
Servidor HTTP para porta 80 - SMSC Simulator
Este servidor roda separadamente com privilégios administrativos
"""

import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SHARED_MESSAGES_FILE = 'shared_messages.json'
MAX_MESSAGES = 100

class SMSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/cgi-bin/smshandler.pl':
                self._handle_sms_request(parsed_url.query)
            else:
                self._send_error_response(404, "Not Found")
                
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self._send_error_response(500, "Internal Server Error")
    
    def _handle_sms_request(self, query_string):
        """Process SMS request and save to shared file"""
        try:
            # Parse query parameters
            params = parse_qs(query_string)
            
            # Extract message content
            submit_param = params.get('submit', [''])[0]
            
            # Create message object
            message = {
                'id': f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                'timestamp': datetime.now().isoformat(),
                'content': submit_param,
                'source': 'http_port_80',
                'processed_parameters': {
                    'sms_submit': 'submit' in params,
                    'sms_submit_ud': 'sms_submit_ud' in params,
                    'sms_submit_da': 'sms_submit_da' in params,
                    'sms_submit_pid': 'sms_submit_pid' in params,
                    'sms_submit_dcs': 'sms_submit_dcs' in params
                }
            }
            
            # Save message to shared file
            self._save_message_to_shared_file(message)
            
            # Send success response
            response = {
                "status": "success",
                "message": "SMS received and processed successfully",
                "timestamp": message['timestamp'],
                "processed_parameters": message['processed_parameters']
            }
            
            self._send_json_response(200, response)
            logger.info(f"SMS message processed: {submit_param}")
            
        except Exception as e:
            logger.error(f"Error processing SMS request: {e}")
            self._send_error_response(500, "Error processing SMS")
    
    def _save_message_to_shared_file(self, message):
        """Save message to shared JSON file"""
        try:
            messages = []
            
            # Load existing messages if file exists
            if os.path.exists(SHARED_MESSAGES_FILE):
                try:
                    with open(SHARED_MESSAGES_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        messages = data.get('messages', [])
                except (json.JSONDecodeError, KeyError):
                    logger.warning("Invalid shared messages file, starting fresh")
                    messages = []
            
            # Add new message
            messages.append(message)
            
            # Keep only the last MAX_MESSAGES
            if len(messages) > MAX_MESSAGES:
                messages = messages[-MAX_MESSAGES:]
            
            # Save back to file
            data = {
                'messages': messages,
                'total_count': len(messages),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(SHARED_MESSAGES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Message saved to shared file. Total messages: {len(messages)}")
            
        except Exception as e:
            logger.error(f"Error saving message to shared file: {e}")
    
    def _send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error_response(self, status_code, message):
        """Send error response"""
        response = {
            "status": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self._send_json_response(status_code, response)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """Start HTTP server on port 80"""
    try:
        server = HTTPServer(('localhost', 80), SMSHandler)
        logger.info("Starting HTTP server on port 80...")
        logger.info("Server endpoint: http://localhost/cgi-bin/smshandler.pl?submit=<message>")
        logger.info("Press Ctrl+C to stop the server")
        
        server.serve_forever()
        
    except PermissionError:
        logger.error("Permission denied. Please run as administrator.")
    except OSError as e:
        if e.errno == 10048:
            logger.error("Port 80 is already in use. Please stop other services using port 80.")
        else:
            logger.error(f"OS Error: {e}")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()