#!/usr/bin/env python3
"""
Cliente de teste para o Simulador SMSC
Simula requisições de um simulador de telefone
"""

import urllib.request
import urllib.parse
import json
import time
from typing import Dict, Optional

class SMSCTestClient:
    """Cliente para testar o simulador SMSC"""
    
    def __init__(self, base_url: str = "http://localhost:9080"):
        self.base_url = base_url.rstrip('/')
    
    def send_sms_command(self, hex_data: str, msisdn: str = "") -> Dict:
        """Envia comando SMS hexadecimal para o simulador"""
        try:
            # Prepara parâmetros da requisição
            params = {
                'submit': hex_data.replace(' ', ''),  # Remove espaços
                'MSISDN': msisdn
            }
            
            # Constrói URL
            query_string = urllib.parse.urlencode(params)
            url = f"{self.base_url}/cgi-bin/smshandler.pl?{query_string}"
            
            print(f"Sending request to: {url}")
            
            # Faz requisição
            with urllib.request.urlopen(url, timeout=10) as response:
                response_data = response.read().decode('utf-8')
                return {
                    'status': 'success',
                    'status_code': response.getcode(),
                    'response': json.loads(response_data)
                }
                
        except urllib.error.HTTPError as e:
            error_data = e.read().decode('utf-8')
            try:
                error_json = json.loads(error_data)
            except:
                error_json = {'message': error_data}
            
            return {
                'status': 'http_error',
                'status_code': e.code,
                'error': error_json
            }
            
        except urllib.error.URLError as e:
            return {
                'status': 'connection_error',
                'error': str(e.reason)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_status(self) -> Dict:
        """Obtém status do simulador"""
        try:
            url = f"{self.base_url}/status"
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {'error': str(e)}
    
    def get_statistics(self) -> Dict:
        """Obtém estatísticas do simulador"""
        try:
            url = f"{self.base_url}/stats"
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {'error': str(e)}
    
    def test_connection(self) -> bool:
        """Testa conexão com o simulador"""
        try:
            status = self.get_status()
            return 'error' not in status
        except:
            return False

def run_test_scenarios():
    """Executa cenários de teste"""
    client = SMSCTestClient()
    
    print("=== SMSC Simulator Test Client ===")
    print(f"Testing connection to: {client.base_url}")
    
    # Teste de conexão
    print("\n1. Testing connection...")
    if client.test_connection():
        print("✓ Connection successful")
    else:
        print("✗ Connection failed - Make sure SMSC simulator is running")
        return
    
    # Teste de status
    print("\n2. Getting status...")
    status = client.get_status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # Teste com o comando do exemplo fornecido
    print("\n3. Testing with example SMS command...")
    example_hex = "D0 71 81 03 01 13 00 82 02 81 83 05 00 8B 64 11 FF 04 91 81 69 00 F6 8F 5A 0A 01 10 10 53 09 03 50 30 98 55 71 20 02 00 90 29 20 F9 31 79 42 71 02 00 90 29 20 39 09 FF FF FF FF FF FF FF FF FF 33 27 F4 01 FF FF FF FF 38 27 FF FF FF FF FF FF 1F FF FF 03 FE FF 23 05 14 86 FF FF 00 00 00 E2 7F 00 FF 03 00 00 00 FE EF 3E 97 FF 3F 3F 00 20 01 01 01"
    
    result = client.send_sms_command(example_hex, "")
    print(f"SMS Result: {json.dumps(result, indent=2)}")
    
    # Teste com diferentes cenários
    test_cases = [
        {
            'name': 'Simple SMS',
            'hex': 'D0 71 81 03 01 13 00',
            'msisdn': '+5511999999999'
        },
        {
            'name': 'International SMS',
            'hex': '91 81 69 00 F6 8F 5A 0A 01 10',
            'msisdn': '+1234567890'
        },
        {
            'name': 'Empty hex (error test)',
            'hex': '',
            'msisdn': ''
        }
    ]
    
    print("\n4. Running additional test cases...")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n4.{i}. {test_case['name']}")
        result = client.send_sms_command(test_case['hex'], test_case['msisdn'])
        print(f"Result: {result['status']} - {result.get('response', {}).get('message', result.get('error', 'Unknown'))}")
        time.sleep(0.5)  # Pequena pausa entre testes
    
    # Estatísticas finais
    print("\n5. Final statistics...")
    stats = client.get_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2)}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    try:
        run_test_scenarios()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")