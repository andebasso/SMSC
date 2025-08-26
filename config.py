#!/usr/bin/env python3
"""
Configuração do Simulador SMSC
"""

import os
from typing import Dict, Any

class SMSCConfig:
    """Configurações do simulador SMSC"""
    
    # Configurações do servidor
    HOST = os.getenv('SMSC_HOST', 'localhost')
    HTTP_PORT = int(os.getenv('SMSC_HTTP_PORT', '8080'))
    HTTPS_PORT = int(os.getenv('SMSC_HTTPS_PORT', '8443'))
    
    # Configurações SSL/TLS
    SSL_CERT_FILE = os.getenv('SMSC_SSL_CERT', 'server.crt')
    SSL_KEY_FILE = os.getenv('SMSC_SSL_KEY', 'server.key')
    ENABLE_HTTPS = os.getenv('SMSC_ENABLE_HTTPS', 'false').lower() == 'true'
    
    # Configurações de logging
    LOG_LEVEL = os.getenv('SMSC_LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('SMSC_LOG_FILE', 'smsc_simulator.log')
    ENABLE_CONSOLE_LOG = os.getenv('SMSC_CONSOLE_LOG', 'true').lower() == 'true'
    
    # Configurações de resposta SMS
    DEFAULT_RESPONSE_CODE = '00'  # Sucesso
    ERROR_RESPONSE_CODE = 'FF'    # Erro genérico
    
    # Configurações de simulação
    SIMULATE_DELAYS = os.getenv('SMSC_SIMULATE_DELAYS', 'false').lower() == 'true'
    MIN_DELAY_MS = int(os.getenv('SMSC_MIN_DELAY', '100'))
    MAX_DELAY_MS = int(os.getenv('SMSC_MAX_DELAY', '1000'))
    
    # Configurações de armazenamento
    STORE_MESSAGES = os.getenv('SMSC_STORE_MESSAGES', 'true').lower() == 'true'
    MAX_STORED_MESSAGES = int(os.getenv('SMSC_MAX_MESSAGES', '1000'))
    
    # Códigos de resposta APDU
    APDU_RESPONSE_CODES = {
        'SUCCESS': '00',
        'INVALID_MESSAGE_FORMAT': '01',
        'INVALID_COMMAND_LENGTH': '02',
        'INVALID_COMMAND_ID': '03',
        'INVALID_BIND_STATUS': '04',
        'ALREADY_BOUND': '05',
        'INVALID_PRIORITY_FLAG': '06',
        'INVALID_REGISTERED_DELIVERY_FLAG': '07',
        'SYSTEM_ERROR': '08',
        'INVALID_SOURCE_ADDRESS': '0A',
        'INVALID_DESTINATION_ADDRESS': '0B',
        'MESSAGE_LENGTH_INVALID': '0C',
        'EXPECTED_RESPONSE_TIMEOUT': '0D',
        'INVALID_MESSAGE_STATE': '0E',
        'UNKNOWN_ERROR': 'FF'
    }
    
    # Configurações de endpoints
    ENDPOINTS = {
        'sms_handler': '/cgi-bin/smshandler.pl',
        'status': '/status',
        'statistics': '/stats',
        'health': '/health',
        'messages': '/messages',
        'config': '/config'
    }
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Retorna configuração como dicionário"""
        return {
            'server': {
                'host': cls.HOST,
                'http_port': cls.HTTP_PORT,
                'https_port': cls.HTTPS_PORT,
                'enable_https': cls.ENABLE_HTTPS
            },
            'ssl': {
                'cert_file': cls.SSL_CERT_FILE,
                'key_file': cls.SSL_KEY_FILE
            },
            'logging': {
                'level': cls.LOG_LEVEL,
                'file': cls.LOG_FILE,
                'console': cls.ENABLE_CONSOLE_LOG
            },
            'simulation': {
                'simulate_delays': cls.SIMULATE_DELAYS,
                'min_delay_ms': cls.MIN_DELAY_MS,
                'max_delay_ms': cls.MAX_DELAY_MS
            },
            'storage': {
                'store_messages': cls.STORE_MESSAGES,
                'max_messages': cls.MAX_STORED_MESSAGES
            },
            'endpoints': cls.ENDPOINTS,
            'response_codes': cls.APDU_RESPONSE_CODES
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valida configurações"""
        try:
            # Valida portas
            if not (1 <= cls.HTTP_PORT <= 65535):
                raise ValueError(f"Invalid HTTP port: {cls.HTTP_PORT}")
            
            if not (1 <= cls.HTTPS_PORT <= 65535):
                raise ValueError(f"Invalid HTTPS port: {cls.HTTPS_PORT}")
            
            # Valida delays
            if cls.MIN_DELAY_MS < 0 or cls.MAX_DELAY_MS < 0:
                raise ValueError("Delays cannot be negative")
            
            if cls.MIN_DELAY_MS > cls.MAX_DELAY_MS:
                raise ValueError("Min delay cannot be greater than max delay")
            
            # Valida max messages
            if cls.MAX_STORED_MESSAGES <= 0:
                raise ValueError("Max stored messages must be positive")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation error: {e}")
            return False

# Configurações específicas para diferentes ambientes
class DevelopmentConfig(SMSCConfig):
    """Configurações para desenvolvimento"""
    HTTP_PORT = 8080
    HTTPS_PORT = 8443
    LOG_LEVEL = 'DEBUG'
    SIMULATE_DELAYS = True
    MIN_DELAY_MS = 50
    MAX_DELAY_MS = 500

class ProductionConfig(SMSCConfig):
    """Configurações para produção"""
    HTTP_PORT = 80
    HTTPS_PORT = 443
    LOG_LEVEL = 'INFO'
    SIMULATE_DELAYS = False
    ENABLE_HTTPS = True

class TestConfig(SMSCConfig):
    """Configurações para testes"""
    HTTP_PORT = 9080
    HTTPS_PORT = 9443
    LOG_LEVEL = 'DEBUG'
    SIMULATE_DELAYS = False
    STORE_MESSAGES = True
    MAX_STORED_MESSAGES = 100

# Função para obter configuração baseada no ambiente
def get_config(environment: str = 'development'):
    """Retorna configuração baseada no ambiente"""
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'test': TestConfig
    }
    
    return configs.get(environment.lower(), DevelopmentConfig)