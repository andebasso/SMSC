#!/usr/bin/env python3
"""
Script para iniciar apenas o servidor HTTP na porta 80
Requer privilégios administrativos no Windows
"""

import sys
import os
import threading
import time
from smsc_simulator import SMSCSimulator, load_server_config, logger

def main():
    try:
        # Carregar configurações
        config = load_server_config()
        
        # Criar simulador
        simulator = SMSCSimulator(
            host=config['host'],
            web_port=config['web_port'],
            sms_port=config['sms_port'],
            http_port=config['http_port'],
            https_port=config['https_port']
        )
        
        print(f"\n=== SMSC HTTP Server (Port 80) v{config['version']} ===")
        print(f"Host: {config['host']}")
        print(f"HTTP Port: {config['http_port']}")
        print(f"\nEndpoint disponível:")
        print(f"  - SMS Handler: http://{config['host']}/cgi-bin/smshandler.pl?submit=$(sms_submit)")
        print(f"\nNOTA: Este servidor requer privilégios administrativos para usar a porta 80")
        print(f"Execute como administrador no Windows ou com sudo no Linux/Mac")
        print("\nPressione Ctrl+C para parar o servidor\n")
        
        # Iniciar servidor HTTP
        simulator.start_http_server()
        
    except PermissionError:
        print("\n❌ ERRO: Permissão negada para usar a porta 80")
        print("Execute este script como administrador (Windows) ou com sudo (Linux/Mac)")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Parando servidor HTTP...")
        simulator.stop()
        print("✅ Servidor HTTP parado com sucesso")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor HTTP: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()