#!/usr/bin/env python3
"""
Script de inicialização do Simulador SMSC
Permite configuração via linha de comando e diferentes modos de operação
"""

import argparse
import sys
import os
import threading
import signal
import time
from config import get_config, SMSCConfig
from smsc_simulator import SMSCSimulator
import logging

def setup_logging(config_class):
    """Configura sistema de logging"""
    handlers = []
    
    # Handler para arquivo
    if config_class.LOG_FILE:
        file_handler = logging.FileHandler(config_class.LOG_FILE)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        handlers.append(file_handler)
    
    # Handler para console
    if config_class.ENABLE_CONSOLE_LOG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        handlers.append(console_handler)
    
    logging.basicConfig(
        level=getattr(logging, config_class.LOG_LEVEL.upper()),
        handlers=handlers,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def create_ssl_certificates(cert_file='server.crt', key_file='server.key'):
    """Cria certificados SSL auto-assinados se não existirem"""
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return True
    
    try:
        # Tenta importar cryptography para gerar certificados
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        
        # Gera chave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Cria certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "SP"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Sao Paulo"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SMSC Simulator"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Salva certificado
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Salva chave privada
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✓ SSL certificates created: {cert_file}, {key_file}")
        return True
        
    except ImportError:
        print("⚠ cryptography library not available. SSL certificates not created.")
        print("  Install with: pip install cryptography")
        return False
    except Exception as e:
        print(f"✗ Error creating SSL certificates: {e}")
        return False

def signal_handler(signum, frame, simulator):
    """Handler para sinais do sistema"""
    print("\n🛑 Shutting down SMSC Simulator...")
    simulator.stop()
    sys.exit(0)

def run_http_server(simulator):
    """Executa servidor HTTP em thread separada"""
    try:
        simulator.start_http_server()
    except Exception as e:
        logging.error(f"HTTP server error: {e}")

def run_https_server(simulator, cert_file, key_file):
    """Executa servidor HTTPS em thread separada"""
    try:
        simulator.start_https_server(cert_file, key_file)
    except Exception as e:
        logging.error(f"HTTPS server error: {e}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='SMSC Simulator - Simulador de Centro de Mensagens SMS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_simulator.py                          # Modo desenvolvimento (porta 8080)
  python run_simulator.py --port 80 --host 0.0.0.0 # Produção
  python run_simulator.py --https --port 8080 --https-port 8443
  python run_simulator.py --env production         # Configuração de produção
  python run_simulator.py --test                   # Modo teste
        """
    )
    
    parser.add_argument('--host', default='localhost',
                       help='Host do servidor (default: localhost)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Porta HTTP (default: 8080)')
    parser.add_argument('--https-port', type=int, default=8443,
                       help='Porta HTTPS (default: 8443)')
    parser.add_argument('--https', action='store_true',
                       help='Habilita servidor HTTPS')
    parser.add_argument('--cert', default='server.crt',
                       help='Arquivo de certificado SSL (default: server.crt)')
    parser.add_argument('--key', default='server.key',
                       help='Arquivo de chave SSL (default: server.key)')
    parser.add_argument('--env', choices=['development', 'production', 'test'],
                       default='development',
                       help='Ambiente de execução (default: development)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Nível de log (sobrescreve configuração)')
    parser.add_argument('--create-certs', action='store_true',
                       help='Cria certificados SSL auto-assinados')
    parser.add_argument('--test', action='store_true',
                       help='Executa em modo teste (porta 9080)')
    parser.add_argument('--version', action='version', version='SMSC Simulator 1.0.0')
    
    args = parser.parse_args()
    
    # Configuração baseada no ambiente
    config_class = get_config(args.env)
    
    # Sobrescreve configurações com argumentos da linha de comando
    if args.test:
        config_class = get_config('test')
        args.port = 9080
        args.https_port = 9443
    
    if args.log_level:
        config_class.LOG_LEVEL = args.log_level
    
    # Valida configuração
    if not config_class.validate_config():
        print("✗ Invalid configuration. Exiting.")
        sys.exit(1)
    
    # Configura logging
    setup_logging(config_class)
    logger = logging.getLogger(__name__)
    
    # Cria certificados SSL se solicitado
    if args.create_certs or args.https:
        create_ssl_certificates(args.cert, args.key)
    
    # Cria simulador
    simulator = SMSCSimulator(
        host=args.host,
        http_port=args.port,
        https_port=args.https_port
    )
    
    # Configura handler para sinais
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, simulator))
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, simulator))
    
    # Informações de inicialização
    print("🚀 SMSC Simulator Starting...")
    print(f"📊 Environment: {args.env}")
    print(f"🌐 HTTP Server: http://{args.host}:{args.port}")
    
    if args.https:
        print(f"🔒 HTTPS Server: https://{args.host}:{args.https_port}")
    
    print("\n📡 Available endpoints:")
    for name, path in config_class.ENDPOINTS.items():
        print(f"  - {name.title()}: http://{args.host}:{args.port}{path}")
    
    print(f"\n📝 Logs: {config_class.LOG_FILE}")
    print("\n⚡ Press Ctrl+C to stop\n")
    
    try:
        # Inicia servidores
        threads = []
        
        # Servidor HTTP
        http_thread = threading.Thread(
            target=run_http_server,
            args=(simulator,),
            daemon=True
        )
        http_thread.start()
        threads.append(http_thread)
        
        # Servidor HTTPS (se habilitado)
        if args.https:
            if os.path.exists(args.cert) and os.path.exists(args.key):
                https_thread = threading.Thread(
                    target=run_https_server,
                    args=(simulator, args.cert, args.key),
                    daemon=True
                )
                https_thread.start()
                threads.append(https_thread)
            else:
                logger.warning(f"SSL certificates not found: {args.cert}, {args.key}")
                logger.warning("HTTPS server not started. Use --create-certs to generate certificates.")
        
        # Aguarda threads
        for thread in threads:
            thread.join()
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down SMSC Simulator...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        simulator.stop()
        print("✅ SMSC Simulator stopped")

if __name__ == "__main__":
    main()