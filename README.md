# Simulador SMSC (Short Message Service Center)

Este é um simulador de SMSC desenvolvido em Python para testes locais com simuladores de telefone. O simulador pode processar comandos APDU hexadecimais e responder via HTTP/HTTPS.

## Características

- ✅ Processamento de comandos APDU hexadecimais
- ✅ Servidor HTTP/HTTPS
- ✅ Parser de dados SMS
- ✅ Interface web moderna e responsiva
- ✅ Sistema de resposta a mensagens SMS
- ✅ Modal interativo para resposta rápida
- ✅ Logging detalhado
- ✅ API REST para status e estatísticas
- ✅ Configuração flexível
- ✅ Cliente de teste incluído
- ✅ Histórico completo de mensagens
- ✅ Estatísticas em tempo real

## Instalação

1. **Clone ou baixe os arquivos do projeto**
2. **Instale Python 3.7+** (se não estiver instalado)
3. **Execute o simulador:**

```bash
python smsc_simulator.py
```

## Uso Básico

### Iniciando o Simulador

```bash
# Modo padrão com interface web (porta 8080)
python smsc_simulator.py

# Com configuração personalizada
python run_simulator.py --port 8080 --host localhost

# Servidor HTTP na porta 80 (requer privilégios de administrador)
python http_server_80.py

# Usando o script de inicialização
python start_http_server.py
```

**Após iniciar, acesse:**
- Interface Web: `http://localhost:8080/`
- API Endpoints: `http://localhost:8080/status`, `/stats`, etc.

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Interface web principal |
| `/cgi-bin/smshandler.pl` | GET/POST | Processa comandos SMS (compatível com seu simulador) |
| `/sms-reply` | POST | Endpoint para resposta a mensagens SMS |
| `/status` | GET | Status do simulador |
| `/stats` | GET | Estatísticas de mensagens processadas |
| `/messages` | GET | Lista todas as mensagens processadas |
| `/simulate-outgoing` | POST | Simula mensagem de saída |
| `/config` | GET/POST | Configurações do simulador |
| `/config/reset-stats` | POST | Reset das estatísticas |
| `/health` | GET | Health check |

### Exemplo de Requisição SMS

O simulador aceita requisições no formato :

```
http://localhost:8080/cgi-bin/smshandler.pl?submit=D07181030113008202818305008B6411FF0491816900F68F5A0A0110105309035030985571200200902920F93179427102009029203909FFFFFFFFFFFFFFFFFF3327F401FFFFFFFF3827FFFFFFFFFFFF1FFFFF03FEFF23051486FFFF000000E27F00FF03000000FEEF3E97FF3F3F0020010101&MSISDN=
```

### Resposta do Simulador

```json
{
  "status": "OK",
  "message": "SMS received and processed",
  "message_id": 1,
  "response_code": "00"
}
```

## Interface Web

O simulador inclui uma interface web moderna e responsiva acessível em `http://localhost:8080/`

### Funcionalidades da Interface Web

- 📱 **Visualização de Mensagens**: Lista todas as mensagens SMS recebidas e enviadas
- 💬 **Sistema de Resposta**: Responda mensagens diretamente pela interface
- 📊 **Estatísticas em Tempo Real**: Acompanhe métricas do simulador
- ⚙️ **Configurações**: Ajuste parâmetros do simulador
- 🔄 **Atualização Automática**: Interface se atualiza automaticamente

### Respondendo Mensagens SMS

1. **Via Interface Web**:
   - Acesse `http://localhost:8080/`
   - Clique no botão "Responder" ao lado da mensagem
   - Digite sua resposta no modal que aparece
   - Clique em "Enviar Resposta"

2. **Via API REST**:
   ```bash
   curl -X POST http://localhost:8080/sms-reply \
     -H "Content-Type: application/json" \
     -d '{
       "msisdn": "5511999999999",
       "message": "Sua resposta aqui",
       "original_message_id": "1"
     }'
   ```

### Resposta da API de Reply

```json
{
  "status": "success",
  "message": "Reply sent successfully",
  "reply_id": 2
}
```

## Testando o Simulador

### Usando a Interface Web (Recomendado)

1. **Inicie o simulador**:
   ```bash
   python smsc_simulator.py
   ```

2. **Acesse a interface web**:
   - Abra seu navegador em `http://localhost:8080/`
   - Visualize mensagens em tempo real
   - Teste o sistema de resposta
   - Monitore estatísticas

### Usando o Cliente de Teste

```bash
python test_client.py
```

Este script irá:
1. Testar a conexão
2. Verificar o status
3. Enviar o comando de exemplo
4. Executar cenários de teste adicionais
5. Mostrar estatísticas finais

### Teste Manual

Você pode testar manualmente usando curl ou seu navegador:

```bash
# Status do simulador
curl http://localhost:8080/status

# Enviar SMS de teste
curl "http://localhost:8080/cgi-bin/smshandler.pl?submit=D071810301130082028183&MSISDN=5511999999999"

# Ver estatísticas
curl http://localhost:8080/stats
```

## Configuração

### Variáveis de Ambiente

```bash
# Configurações do servidor
SMSC_HOST=localhost
SMSC_HTTP_PORT=8080
SMSC_HTTPS_PORT=8443

# Logging
SMSC_LOG_LEVEL=INFO
SMSC_LOG_FILE=smsc_simulator.log

# SSL/HTTPS
SMSC_ENABLE_HTTPS=false
SMSC_SSL_CERT=server.crt
SMSC_SSL_KEY=server.key
```

### Arquivo de Configuração

Edite `config.py` para personalizar:
- Portas do servidor
- Configurações de logging
- Códigos de resposta APDU
- Simulação de delays
- Armazenamento de mensagens

## Estrutura do Projeto

```
SMSC/
├── smsc_simulator.py       # Simulador principal
├── config.py              # Configurações
├── test_client.py         # Cliente de teste
├── run_simulator.py       # Script de inicialização
├── http_server_80.py      # Servidor HTTP na porta 80
├── start_http_server.py   # Script para iniciar servidor HTTP
├── requirements.txt       # Dependências
├── README.md             # Este arquivo
├── COMO_USAR_SERVICO.md  # Guia de uso do serviço
├── INSTALACAO_SERVICO.md # Guia de instalação como serviço
├── static/               # Arquivos da interface web
│   ├── index.html        # Página principal
│   ├── script.js         # JavaScript da interface
│   └── style.css         # Estilos CSS
└── logs/                 # Logs (criado automaticamente)
```

## Funcionalidades Avançadas

### Parser APDU

O simulador inclui um parser básico para comandos APDU que extrai:
- Tipo de mensagem
- Referência da mensagem
- Informações do número de telefone
- Dados hexadecimais completos

### Logging

Todos os eventos são registrados em:
- Console (tempo real)
- Arquivo de log (`smsc_simulator.log`)

### Estatísticas

O simulador mantém estatísticas de:
- Total de mensagens processadas (recebidas e enviadas)
- Última mensagem processada
- Tempo de atividade
- Histórico completo de mensagens
- Contadores separados para mensagens de entrada e saída
- Estatísticas de respostas enviadas

## Integração com Seu Simulador de Telefone

1. **Configure seu simulador de telefone** para enviar requisições para:
   - `http://localhost:8080/cgi-bin/smshandler.pl`

2. **Formato da requisição** deve ser:
   ```
   GET /cgi-bin/smshandler.pl?submit=<HEX_DATA>&MSISDN=<PHONE_NUMBER>
   ```

3. **O simulador responderá** com JSON contendo:
   - Status da operação
   - ID da mensagem
   - Código de resposta

## Solução de Problemas

### Erro "Connection could not be established"

1. Verifique se o simulador está rodando:
   ```bash
   python smsc_simulator.py
   ```

2. Teste a conexão:
   ```bash
   curl http://localhost:8080/status
   ```

3. Verifique se a porta não está em uso:
   ```bash
   netstat -an | findstr :8080
   ```

### Mudando a Porta

Se a porta 8080 estiver em uso:

```python
# Em smsc_simulator.py, linha final:
simulator = SMSCSimulator(host='localhost', http_port=9080)
```

Ou use variável de ambiente:
```bash
set SMSC_HTTP_PORT=9080
python smsc_simulator.py
```

### Logs Detalhados

Para debug, altere o nível de log em `config.py`:
```python
LOG_LEVEL = 'DEBUG'
```

## HTTPS (SSL/TLS)

Para habilitar HTTPS:

1. **Gere certificados SSL** (auto-assinados para teste):
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
   ```

2. **Configure no código**:
   ```python
   simulator = SMSCSimulator(host='localhost', http_port=8080, https_port=8443)
   simulator.start_https_server()  # Em vez de start_http_server()
   ```

3. **Acesse via HTTPS**:
   ```
   https://localhost:8443/cgi-bin/smshandler.pl
   ```

## Desenvolvimento

### Adicionando Novos Endpoints

1. Edite `SMSCRequestHandler` em `smsc_simulator.py`
2. Adicione novo método `_handle_<endpoint>_request`
3. Registre no método `do_GET`

### Melhorando o Parser APDU

1. Edite a classe `APDUParser`
2. Implemente parsing específico para diferentes tipos de APDU
3. Adicione validações adicionais

### Testes Automatizados

```bash
# Instale pytest (opcional)
pip install pytest

# Execute testes
pytest test_client.py -v
```

## Licença

Este projeto é fornecido como está, para fins de teste e desenvolvimento.

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs em `smsc_simulator.log`
2. Execute o cliente de teste para diagnóstico
3. Consulte a seção de solução de problemas acima