// SMSC Simulator Dashboard JavaScript
class SMSCDashboard {
    constructor() {
        this.baseUrl = window.location.origin;
        this.updateInterval = 10000; // 10 seconds
        this.updateTimer = null;
        this.isOnline = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.checkServerStatus();
        this.startAutoUpdate();
        this.loadRecentMessages();
        this.loadConfiguration();
    }
    
    bindEvents() {
        // SMS Test Form
        const smsForm = document.getElementById('smsTestForm');
        if (smsForm) {
            smsForm.addEventListener('submit', (e) => this.handleSMSTest(e));
        }
        
        // Refresh buttons
        const refreshBtn = document.getElementById('refreshStats');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.updateStatistics());
        }
        
        const refreshMsgBtn = document.getElementById('refreshMessages');
        if (refreshMsgBtn) {
            refreshMsgBtn.addEventListener('click', () => this.loadRecentMessages());
        }
        
        // Send message button
        const sendMessageBtn = document.getElementById('sendMessage');
        if (sendMessageBtn) {
            sendMessageBtn.addEventListener('click', () => this.sendMessage());
        }
        
        // Clear messages button
        const clearMsgBtn = document.getElementById('clearMessages');
        if (clearMsgBtn) {
            clearMsgBtn.addEventListener('click', () => this.clearMessages());
        }
        
        // Example buttons
        const exampleBtns = document.querySelectorAll('.example-btn');
        exampleBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.loadExample(e));
        });
        
        // Bind reset statistics button
        const resetStatsBtn = document.getElementById('resetStatsBtn');
        if (resetStatsBtn) {
            resetStatsBtn.addEventListener('click', () => this.resetStatistics());
        }

        // Bind update SMS port button
        const updateSmsPortBtn = document.getElementById('updateSmsPortBtn');
        const updateWebPortBtn = document.getElementById('updateWebPortBtn');
        
        if (updateSmsPortBtn) {
            updateSmsPortBtn.addEventListener('click', () => this.updateSmsPort());
        }
        
        if (updateWebPortBtn) {
            updateWebPortBtn.addEventListener('click', () => this.updateWebPort());
        }
        
        // Bind update host button
        const updateHostBtn = document.getElementById('updateHostBtn');
        if (updateHostBtn) {
            updateHostBtn.addEventListener('click', () => this.updateHost());
        }
        
        // Bind update timeout button
        const updateTimeoutBtn = document.getElementById('updateTimeoutBtn');
        if (updateTimeoutBtn) {
            updateTimeoutBtn.addEventListener('click', () => this.updateTimeout());
        }
        
        // Bind update max connections button
        const updateMaxConnectionsBtn = document.getElementById('updateMaxConnectionsBtn');
        if (updateMaxConnectionsBtn) {
            updateMaxConnectionsBtn.addEventListener('click', () => this.updateMaxConnections());
        }
        
        // Bind restart server button
        const restartServerBtn = document.getElementById('restartServerBtn');
        if (restartServerBtn) {
            restartServerBtn.addEventListener('click', () => this.restartServer());
        }
        
        // Bind update log level button
        const updateLogLevelBtn = document.getElementById('updateLogLevelBtn');
        if (updateLogLevelBtn) {
            updateLogLevelBtn.addEventListener('click', () => this.updateLogLevel());
        }
        
        // Auto-update toggle
        const autoUpdateToggle = document.getElementById('autoUpdate');
        if (autoUpdateToggle) {
            autoUpdateToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoUpdate();
                } else {
                    this.stopAutoUpdate();
                }
            });
        }
    }
    
    async checkServerStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch(`${this.baseUrl}/status`, {
                method: 'GET',
                signal: controller.signal,
                cache: 'no-cache',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            clearTimeout(timeoutId);
            
            const data = await response.json();
            
            this.isOnline = response.ok && data.status === 'running';
            this.updateStatusIndicator();
            
            if (this.isOnline) {
                this.updateStatistics();
            }
        } catch (error) {
            console.error('Error checking server status:', error);
            this.isOnline = false;
            this.updateStatusIndicator();
            
            // Retry after 3 seconds if offline
            setTimeout(() => {
                this.checkServerStatus();
            }, 3000);
        }
    }
    
    updateStatusIndicator() {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (statusDot && statusText) {
            if (this.isOnline) {
                statusDot.classList.remove('offline');
                statusText.textContent = 'Online';
            } else {
                statusDot.classList.add('offline');
                statusText.textContent = 'Offline';
            }
        }
    }
    
    async updateStatistics() {
        if (!this.isOnline) return;
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout
            
            const [statsResponse, configResponse] = await Promise.all([
                fetch(`${this.baseUrl}/stats`, {
                    signal: controller.signal,
                    cache: 'no-cache'
                }),
                fetch(`${this.baseUrl}/config`, {
                    signal: controller.signal,
                    cache: 'no-cache'
                })
            ]);
            
            clearTimeout(timeoutId);
            
            const stats = await statsResponse.json();
            const config = await configResponse.json();
            
            // Update statistics display
            this.updateStatElement('totalMessages', stats.total_messages || 0);
            this.updateStatElement('successfulMessages', stats.successful_messages || 0);
            this.updateStatElement('failedMessages', stats.failed_messages || 0);
            this.updateStatElement('uptime', this.formatUptime(stats.uptime_seconds || 0));
            this.updateStatElement('lastMessage', stats.last_message_time ? this.formatDateTime(stats.last_message_time) : 'Nunca');
            
            // Update ports display
            this.updateStatElement('webPort', config.web_port || 8080);
            this.updateStatElement('smsPort', config.sms_port || 8081);
            
            // Update success rate
            const total = stats.total_messages || 0;
            const successful = stats.successful_messages || 0;
            const successRate = total > 0 ? ((successful / total) * 100).toFixed(1) : '0.0';
            this.updateStatElement('successRate', `${successRate}%`);
            
        } catch (error) {
            console.error('Error updating statistics:', error);
            this.showToast('Erro ao atualizar estatísticas', 'error');
        }
    }
    
    updateStatElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    formatDateTime(isoString) {
        const date = new Date(isoString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
    }
    
    async handleSMSTest(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const apduHex = formData.get('apdu_hex').trim();
        const msisdn = formData.get('msisdn').trim();
        
        if (!apduHex) {
            this.showToast('Por favor, insira os dados APDU hexadecimais', 'error');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const response = await fetch(`${this.baseUrl}/cgi-bin/smshandler.pl`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `apdu_hex=${encodeURIComponent(apduHex)}&msisdn=${encodeURIComponent(msisdn)}`
            });
            
            const responseText = await response.text();
            let responseData;
            
            try {
                responseData = JSON.parse(responseText);
            } catch {
                responseData = { raw_response: responseText };
            }
            
            this.displayResponse(responseData, response.ok);
            
            if (response.ok) {
                this.showToast('Mensagem SMS enviada com sucesso!', 'success');
                form.reset();
                // Update statistics after successful send
                setTimeout(() => {
                    this.updateStatistics();
                    this.loadRecentMessages();
                }, 1000);
            } else {
                this.showToast('Erro ao enviar mensagem SMS', 'error');
            }
            
        } catch (error) {
            console.error('Error sending SMS:', error);
            this.displayResponse({ error: error.message }, false);
            this.showToast('Erro de conexão com o servidor', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayResponse(data, isSuccess) {
        const responseSection = document.getElementById('responseSection');
        const responseContent = document.getElementById('responseContent');
        
        if (responseSection && responseContent) {
            responseSection.style.display = 'block';
            responseContent.className = `response-content ${isSuccess ? 'response-success' : 'response-error'}`;
            responseContent.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            
            // Scroll to response
            responseSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    async loadRecentMessages() {
        if (!this.isOnline) return;
        
        try {
            const response = await fetch(`${this.baseUrl}/messages`);
            const data = await response.json();
            
            this.displayMessages(data.messages || []);
            
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showToast('Erro ao carregar mensagens recentes', 'error');
        }
    }
    
    displayMessages(messages) {
        const messagesList = document.getElementById('messagesList');
        if (!messagesList) return;
        
        if (messages.length === 0) {
            messagesList.innerHTML = '<div class="no-messages">Nenhuma mensagem encontrada</div>';
            return;
        }
        
        const messagesHtml = messages.map(msg => {
            const direction = msg.direction || 'unknown';
            const directionIcon = direction === 'received' ? '📥' : direction === 'sent' ? '📤' : '❓';
            const directionText = direction === 'received' ? 'Recebida' : direction === 'sent' ? 'Enviada' : 'Desconhecida';
            const directionClass = direction === 'received' ? 'received' : direction === 'sent' ? 'sent' : 'unknown';
            
            const replyButton = direction === 'received' ? 
                `<button class="btn btn-small btn-reply" onclick="replyToMessage('${msg.msisdn || msg.destination_address}', '${msg.id}')">
                    ↩️ Responder
                </button>` : '';
            
            return `
                <div class="message-item ${directionClass}">
                    <div class="message-header">
                        <span class="message-direction">${directionIcon} ${directionText}</span>
                        <span class="message-id">ID: ${msg.id || 'N/A'}</span>
                        <span class="message-time">${this.formatTimestamp(msg.timestamp)}</span>
                        ${replyButton}
                    </div>
                    <div class="message-details">
                        <strong>MSISDN:</strong> ${msg.msisdn || msg.destination_address || 'N/A'}<br>
                        <strong>Status:</strong> ${msg.status || 'N/A'}<br>
                        <strong>APDU:</strong> <code>${(msg.apdu_hex || msg.raw_data || '').substring(0, 50)}${(msg.apdu_hex || msg.raw_data || '').length > 50 ? '...' : ''}</code>
                    </div>
                </div>
            `;
        }).join('');
        
        messagesList.innerHTML = messagesHtml;
    }
    
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('pt-BR');
        } catch {
            return timestamp;
        }
    }
    
    async sendMessage() {
        const destination = prompt('Digite o número de destino (ex: +5511999999999):');
        if (!destination) return;
        
        const message = prompt('Digite a mensagem a ser enviada:', '');
        if (!message) return;
        
        try {
            const params = new URLSearchParams({
                destination: destination,
                message: message
            });
            
            const response = await fetch(`${this.baseUrl}/simulate-outgoing?${params}`);
            const data = await response.json();
            
            if (response.ok && data.status === 'OK') {
                this.loadRecentMessages();
                this.updateStatistics();
                this.showToast(`Mensagem enviada com sucesso! ID: ${data.message_id}`, 'success');
            } else {
                this.showToast('Erro ao enviar mensagem: ' + (data.message || 'Erro desconhecido'), 'error');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showToast('Erro ao enviar mensagem', 'error');
        }
    }
    
    async clearMessages() {
        if (!confirm('Tem certeza que deseja limpar todas as mensagens?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/messages`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showToast('Mensagens limpas com sucesso', 'success');
                this.loadRecentMessages();
                this.updateStatistics();
            } else {
                this.showToast('Erro ao limpar mensagens', 'error');
            }
        } catch (error) {
            console.error('Error clearing messages:', error);
            this.showToast('Erro de conexão ao limpar mensagens', 'error');
        }
    }
    
    loadExample(event) {
        const exampleType = event.target.dataset.example;
        const apduInput = document.getElementById('apdu_hex');
        const msisdnInput = document.getElementById('msisdn');
        
        if (!apduInput || !msisdnInput) return;
        
        const examples = {
            simple: {
                apdu: '0001000C91559876543210000004C8F71D14',
                msisdn: '+5511999887766'
            },
            international: {
                apdu: '0001000C91559876543210000008C8F71D1406C8F71D14',
                msisdn: '+1234567890'
            },
            long: {
                apdu: '0001000C91559876543210000020C8F71D14C8F71D14C8F71D14C8F71D14C8F71D14C8F71D14C8F71D14C8F71D14',
                msisdn: '+5511888777666'
            }
        };
        
        const example = examples[exampleType];
        if (example) {
            apduInput.value = example.apdu;
            msisdnInput.value = example.msisdn;
            this.showToast(`Exemplo ${exampleType} carregado`, 'success');
        }
    }
    
    startAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        this.updateTimer = setInterval(() => {
            this.checkServerStatus();
        }, this.updateInterval);
    }
    
    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }
    
    async resetStatistics() {
        try {
            const response = await fetch(`${this.baseUrl}/config/reset-stats`, {
                method: 'GET',
                cache: 'no-cache',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showToast('Estatísticas resetadas com sucesso!', 'success');
                
                // Update statistics and configuration immediately
                this.updateStatistics();
                this.loadConfiguration();
                this.loadRecentMessages();
            } else {
                throw new Error('Falha ao resetar estatísticas');
            }
        } catch (error) {
            console.error('Error resetting statistics:', error);
            this.showToast('Erro ao resetar estatísticas: ' + error.message, 'error');
        }
    }
    
    async loadConfiguration() {
        try {
            const response = await fetch(`${this.baseUrl}/config`, {
                method: 'GET',
                cache: 'no-cache',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const config = await response.json();
                
                // Update all input fields
                const webPortInput = document.getElementById('webPortInput');
                const smsPortInput = document.getElementById('smsPortInput');
                const hostInput = document.getElementById('hostInput');
                const timeoutInput = document.getElementById('timeoutInput');
                const maxConnectionsInput = document.getElementById('maxConnectionsInput');
                const versionInput = document.getElementById('versionInput');
                const logLevelInput = document.getElementById('logLevelInput');
                
                if (webPortInput) webPortInput.value = config.web_port || '8080';
                if (smsPortInput) smsPortInput.value = config.sms_port || '8081';
                if (hostInput) hostInput.value = config.host || 'localhost';
                if (timeoutInput) timeoutInput.value = config.timeout || '30';
                if (maxConnectionsInput) maxConnectionsInput.value = config.max_connections || '100';
                const versionDisplay = document.getElementById('versionDisplay');
                if (versionDisplay) versionDisplay.textContent = config.version || '1.0.0';
                if (logLevelInput) logLevelInput.value = config.log_level || 'INFO';
                
                const serverUptime = document.getElementById('serverUptime');
                if (serverUptime) serverUptime.textContent = config.uptime || '--';
                
                const systemVersion = document.getElementById('systemVersion');
                if (systemVersion) systemVersion.textContent = config.version || '1.0.0';
                
                const totalMessagesConfig = document.getElementById('totalMessagesConfig');
                if (totalMessagesConfig) totalMessagesConfig.textContent = config.total_messages || '0';
                
                this.showToast('Configurações carregadas com sucesso', 'success');
            } else {
                throw new Error('Falha ao carregar configurações');
            }
        } catch (error) {
            console.error('Erro ao carregar configurações:', error);
            this.showToast('Erro ao carregar configurações', 'error');
        }
    }
    
    async updateSmsPort() {
        const smsPortInput = document.getElementById('smsPortInput');
        const newPort = parseInt(smsPortInput.value);
        
        if (!newPort || newPort < 1024 || newPort > 65535) {
            this.showToast('Porta SMS deve estar entre 1024 e 65535', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/config/update-sms-port`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sms_port: newPort })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(`Porta SMS atualizada para ${newPort}. Reinicie o servidor para aplicar.`, 'success');
            } else {
                throw new Error('Falha ao atualizar porta SMS');
            }
        } catch (error) {
            console.error('Erro ao atualizar porta SMS:', error);
            this.showToast('Erro ao atualizar porta SMS', 'error');
        }
    }
    
    async updateWebPort() {
        const webPortInput = document.getElementById('webPortInput');
        const newPort = parseInt(webPortInput.value);
        
        if (!newPort || newPort < 1024 || newPort > 65535) {
            this.showToast('Porta Web deve estar entre 1024 e 65535', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/config/update-web-port`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ web_port: newPort })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(`Porta Web atualizada para ${newPort}. Reinicie o servidor para aplicar.`, 'success');
            } else {
                throw new Error('Falha ao atualizar porta web');
            }
        } catch (error) {
            console.error('Erro ao atualizar porta web:', error);
            this.showToast('Erro ao atualizar porta web', 'error');
        }
    }
    
    async updateHost() {
        const hostInput = document.getElementById('hostInput');
        const newHost = hostInput.value.trim();
        
        if (!newHost) {
            this.showToast('Host não pode estar vazio', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/config/update-host`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ host: newHost })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(`Host atualizado para ${newHost}. Reinicie o servidor para aplicar.`, 'success');
            } else {
                throw new Error('Falha ao atualizar host');
            }
        } catch (error) {
            console.error('Erro ao atualizar host:', error);
            this.showToast('Erro ao atualizar host', 'error');
        }
    }
    
    async updateTimeout() {
        const timeoutInput = document.getElementById('timeoutInput');
        const newTimeout = parseInt(timeoutInput.value);
        
        if (!newTimeout || newTimeout < 1 || newTimeout > 300) {
            this.showToast('Timeout deve estar entre 1 e 300 segundos', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/config/update-timeout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ timeout: newTimeout })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(`Timeout atualizado para ${newTimeout} segundos.`, 'success');
            } else {
                throw new Error('Falha ao atualizar timeout');
            }
        } catch (error) {
            console.error('Erro ao atualizar timeout:', error);
            this.showToast('Erro ao atualizar timeout', 'error');
        }
    }
    
    async updateMaxConnections() {
        const maxConnectionsInput = document.getElementById('maxConnectionsInput');
        const newMaxConnections = parseInt(maxConnectionsInput.value);
        
        if (!newMaxConnections || newMaxConnections < 1 || newMaxConnections > 1000) {
            this.showToast('Máximo de conexões deve estar entre 1 e 1000', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/config/update-max-connections`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ max_connections: newMaxConnections })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(`Máximo de conexões atualizado para ${newMaxConnections}.`, 'success');
            } else {
                throw new Error('Falha ao atualizar máximo de conexões');
            }
        } catch (error) {
            console.error('Erro ao atualizar máximo de conexões:', error);
            this.showToast('Erro ao atualizar máximo de conexões', 'error');
        }
    }
    
    async restartServer() {
        // Confirmação mais detalhada
        const confirmMessage = `🔄 REINICIAR SERVIDOR\n\n` +
            `Esta ação irá:\n` +
            `• Parar o servidor atual\n` +
            `• Iniciar uma nova instância\n` +
            `• Interromper temporariamente o serviço (2-5 segundos)\n\n` +
            `Deseja continuar?`;
            
        if (!confirm(confirmMessage)) {
            return;
        }
        
        // Desabilitar o botão durante o processo
        const restartBtn = document.getElementById('restartServerBtn');
        const originalText = restartBtn.innerHTML;
        restartBtn.disabled = true;
        restartBtn.innerHTML = '<span class="icon">⏳</span> Reiniciando...';
        
        try {
            this.showToast('🔄 Iniciando reinicialização do servidor...', 'info');
            
            const response = await fetch(`${this.baseUrl}/config/restart-server`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast('✅ Servidor reiniciado com sucesso! Recarregando página...', 'success');
                
                // Aguarda um pouco mais para garantir que o servidor reiniciou
                setTimeout(() => {
                    window.location.reload();
                }, 4000);
            } else {
                throw new Error(`Falha na requisição: ${response.status}`);
            }
        } catch (error) {
            console.error('Erro ao reiniciar servidor:', error);
            this.showToast('❌ Erro ao reiniciar servidor: ' + error.message, 'error');
            
            // Reabilitar o botão em caso de erro
            restartBtn.disabled = false;
            restartBtn.innerHTML = originalText;
        }
    }
    
    async updateLogLevel() {
        const logLevelSelect = document.getElementById('logLevelInput');
        const newLogLevel = logLevelSelect.value;
        
        if (!newLogLevel) {
            this.showToast('Selecione um nível de log', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/config/update-log-level`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ log_level: newLogLevel })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(`Nível de log atualizado para ${newLogLevel}.`, 'success');
            } else {
                throw new Error('Falha ao atualizar nível de log');
            }
        } catch (error) {
            console.error('Erro ao atualizar nível de log:', error);
            this.showToast('Erro ao atualizar nível de log', 'error');
        }
    }
    
    showLoading(show) {
        let overlay = document.getElementById('loadingOverlay');
        
        if (show) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'loadingOverlay';
                overlay.className = 'loading-overlay';
                overlay.innerHTML = `
                    <div class="loading-spinner">
                        <span class="icon">⏳</span>
                        <div>Enviando mensagem...</div>
                    </div>
                `;
                document.body.appendChild(overlay);
            }
            overlay.style.display = 'flex';
        } else {
            if (overlay) {
                overlay.style.display = 'none';
            }
        }
    }
    
    showToast(message, type = 'info') {
        let container = document.getElementById('toastContainer');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-header">
                <span class="toast-title">${type === 'success' ? 'Sucesso' : type === 'error' ? 'Erro' : 'Informação'}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
            <div class="toast-message">${message}</div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SMSCDashboard();
});

// Add some utility functions for enhanced UX
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show success feedback
        const toast = new SMSCDashboard();
        toast.showToast('Copiado para a área de transferência', 'success');
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// Function to reply to a message
function replyToMessage(msisdn, messageId) {
    const msisdnInput = document.getElementById('msisdn');
    const apduInput = document.getElementById('apdu_hex');
    
    if (msisdnInput) {
        msisdnInput.value = msisdn;
    }
    
    if (apduInput) {
        apduInput.focus();
    }
    
    // Scroll to the SMS form
    const smsForm = document.getElementById('smsTestForm');
    if (smsForm) {
        smsForm.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Show toast notification
    const dashboard = new SMSCDashboard();
    dashboard.showToast(`Respondendo à mensagem #${messageId} para ${msisdn}`, 'info');
}

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+Enter to submit SMS form
    if (e.ctrlKey && e.key === 'Enter') {
        const smsForm = document.getElementById('smsTestForm');
        if (smsForm) {
            smsForm.dispatchEvent(new Event('submit'));
        }
    }
    
    // F5 to refresh statistics
    if (e.key === 'F5' && !e.ctrlKey) {
        e.preventDefault();
        const dashboard = new SMSCDashboard();
        dashboard.updateStatistics();
        dashboard.loadRecentMessages();
    }
});

// Add service worker for offline support (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Service worker registration would go here
        // navigator.serviceWorker.register('/sw.js');
    });
}