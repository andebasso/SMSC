# 🚀 SMSC Simulator - Solução Completa sem PowerShell

## ✅ Problema Resolvido!

**Antes:** Precisava manter o PowerShell aberto o tempo todo  
**Agora:** Roda como serviço do Windows em background

---

## 📦 Instalação Rápida (Recomendada)

### 1️⃣ Instalar como Serviço do Windows

```bash
# Execute como Administrador:
instalar_servico.bat
```

**O que acontece:**
- ✅ Instala automaticamente como serviço do Windows
- ✅ Configura para iniciar com o sistema
- ✅ Inicia imediatamente o serviço
- ✅ Não precisa mais do PowerShell aberto!

### 2️⃣ Gerenciar o Serviço

```bash
# Menu interativo de controle:
controlar_servico.bat
```

**Opções disponíveis:**
- 🟢 Iniciar serviço
- 🔴 Parar serviço  
- 🔄 Reiniciar serviço
- 📊 Ver status
- 🌐 Abrir interface web

---

## 🎯 Integração com Seu Software

### Endpoint Principal
```
URL: http://localhost:8080/cgi-bin/smshandler.pl
Método: GET
Parâmetros: submit=$(sms_submit)&MSISDN=<numero>
```

### Exemplo de Uso
```bash
curl "http://localhost:8080/cgi-bin/smshandler.pl?submit=D07181030113008202818305008B6411FF&MSISDN=5511999999999"
```

### Resposta
```json
{
  "status": "OK",
  "message": "SMS received and processed",
  "message_id": 123,
  "response_code": "00"
}
```

---

## 🌐 Interfaces Disponíveis

| Interface | URL | Descrição |
|-----------|-----|-----------|
| **Web Interface** | http://localhost:8080/ | Interface completa de gerenciamento |
| **SMS Handler** | http://localhost:8987/cgi-bin/smshandler.pl | Endpoint alternativo |
| **Port 80 Simulation** | http://localhost:8080/cgi-bin/smshandler.pl | Compatibilidade com porta 80 |
| **API Status** | http://localhost:8080/status | Status do sistema |
| **API Stats** | http://localhost:8080/stats | Estatísticas em tempo real |
| **API Messages** | http://localhost:8080/messages | Lista de mensagens |

---

## 🔧 Vantagens da Solução

### ✅ Sem PowerShell
- Não precisa manter terminal aberto
- Roda completamente em background
- Inicia automaticamente com o Windows

### ✅ Gerenciamento Fácil
- Scripts batch para controle
- Interface web intuitiva
- Logs automáticos

### ✅ Integração Perfeita
- Compatível com formato $(sms_submit)
- Suporte a todos os parâmetros SMS
- Resposta em JSON padronizada

### ✅ Confiabilidade
- Serviço do Windows nativo
- Reinicialização automática em caso de erro
- Monitoramento via Event Viewer

---

## 📋 Comandos Úteis

### Controle Manual do Serviço
```bash
# Iniciar
sc start "SMSCSimulator"

# Parar
sc stop "SMSCSimulator"

# Status
sc query "SMSCSimulator"

# Remover
sc delete "SMSCSimulator"
```

### Verificar se está Funcionando
```bash
# Teste rápido
curl http://localhost:8080/status

# Enviar SMS de teste
curl "http://localhost:8080/cgi-bin/smshandler.pl?submit=teste"
```

---

## 🗂️ Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `smsc_service.exe` | Executável standalone (6.7MB) |
| `smsc_service.py` | Script do serviço |
| `instalar_servico.bat` | Instalador automático |
| `controlar_servico.bat` | Menu de controle |
| `remover_servico.bat` | Desinstalador |
| `smsc_service.log` | Logs do serviço |

---

## 🚨 Solução de Problemas

### Erro de Permissão
```bash
# Execute como Administrador
Powershell -Command "Start-Process cmd -Verb RunAs"
```

### Porta em Uso
```bash
# Verificar o que está usando a porta
netstat -ano | findstr :8080
```

### Serviço não Inicia
```bash
# Ver logs detalhados
type smsc_service.log
```

---

## 🎉 Resultado Final

**Seu software agora pode:**
- ✅ Conectar diretamente no simulador
- ✅ Funcionar sem intervenção manual
- ✅ Rodar 24/7 sem problemas
- ✅ Reiniciar automaticamente após reboot

**Você não precisa mais:**
- ❌ Manter PowerShell aberto
- ❌ Iniciar manualmente o simulador
- ❌ Se preocupar com travamentos
- ❌ Configurar nada após reinicialização

---

## 📞 Suporte

Se tiver problemas:
1. Verifique os logs: `smsc_service.log`
2. Teste a conectividade: `curl http://localhost:8080/status`
3. Use o menu de controle: `controlar_servico.bat`

**Agora seu simulador SMSC é uma solução profissional completa! 🚀**