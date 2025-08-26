# SMSC Simulator - Instalação como Serviço

## Instalação Automática

1. **Execute como Administrador**: `instalar_servico.bat`
   - Instala o simulador como serviço do Windows
   - Inicia automaticamente o serviço
   - Configura para iniciar com o Windows

## Controle do Serviço

- **Controlar**: `controlar_servico.bat`
  - Menu interativo para gerenciar o serviço
  - Iniciar, parar, reiniciar, verificar status
  - Abrir interface web

- **Remover**: `remover_servico.bat`
  - Remove completamente o serviço

## Acesso

- **Interface Web**: http://localhost:8080/
- **SMS Handler**: http://localhost:8987/cgi-bin/smshandler.pl
- **Endpoint Port 80**: http://localhost:8080/cgi-bin/smshandler.pl

## Vantagens do Serviço

✓ **Não precisa manter PowerShell aberto**
✓ **Inicia automaticamente com o Windows**
✓ **Roda em background**
✓ **Gerenciamento via interface gráfica**
✓ **Logs automáticos**

## Logs

- Arquivo: `smsc_service.log`
- Visualizar via Visualizador de Eventos do Windows

## Requisitos

- Windows 7/10/11
- Privilégios de Administrador (apenas para instalação)
- Python 3.7+ (para desenvolvimento)

## Integração com Software

Após a instalação, seu software pode se conectar diretamente:

```
URL: http://localhost:8080/cgi-bin/smshandler.pl
Método: GET
Parâmetros: submit=$(sms_submit)&MSISDN=<numero>
```

O serviço ficará sempre disponível, sem necessidade de intervenção manual.
