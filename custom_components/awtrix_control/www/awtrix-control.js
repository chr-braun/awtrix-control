class AwtrixControlCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({mode: 'open'});
    }

    setConfig(config) {
        this.config = config;
        this.render();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                .awtrix-card {
                    padding: 20px;
                    background: linear-gradient(135deg, var(--ha-card-background) 0%, var(--secondary-background-color) 100%);
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                    font-family: var(--mdc-typography-font-family);
                    border: 1px solid var(--divider-color);
                    position: relative;
                    overflow: hidden;
                }
                
                .awtrix-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #00ff00, #00aaff, #ff6b35);
                    animation: rainbow 3s ease-in-out infinite;
                }
                
                @keyframes rainbow {
                    0%, 100% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                }
                
                .awtrix-header {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 24px;
                    color: var(--primary-text-color);
                    text-align: center;
                    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    position: relative;
                }
                
                .awtrix-header::after {
                    content: '🎯';
                    font-size: 32px;
                    position: absolute;
                    top: -8px;
                    right: 20px;
                    animation: bounce 2s ease-in-out infinite;
                }
                
                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                    40% { transform: translateY(-10px); }
                    60% { transform: translateY(-5px); }
                }
                
                .awtrix-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                }
                
                .awtrix-section {
                    background: linear-gradient(145deg, var(--secondary-background-color), var(--primary-background-color));
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid var(--divider-color);
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }
                
                .awtrix-section:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                }
                
                .awtrix-section::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
                    transition: left 0.5s ease;
                }
                
                .awtrix-section:hover::before {
                    left: 100%;
                }
                
                .awtrix-section h3 {
                    margin: 0 0 16px 0;
                    font-size: 16px;
                    color: var(--primary-text-color);
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .awtrix-input {
                    width: 100%;
                    padding: 12px;
                    margin-bottom: 12px;
                    border: 2px solid var(--divider-color);
                    border-radius: 8px;
                    background: var(--primary-background-color);
                    color: var(--primary-text-color);
                    font-size: 14px;
                    box-sizing: border-box;
                    transition: all 0.3s ease;
                    outline: none;
                }
                
                .awtrix-input:focus {
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
                }
                
                .awtrix-button {
                    width: 100%;
                    padding: 12px;
                    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .awtrix-button:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 15px rgba(0, 122, 255, 0.3);
                }
                
                .awtrix-button:active {
                    transform: translateY(0);
                }
                
                .awtrix-button.secondary {
                    background: linear-gradient(135deg, var(--accent-color), #ff6b35);
                }
                
                .awtrix-button.info {
                    background: linear-gradient(135deg, var(--info-color), #00aaff);
                }
                
                .awtrix-button::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                    transition: left 0.5s ease;
                }
                
                .awtrix-button:hover::before {
                    left: 100%;
                }
                
                .awtrix-status {
                    margin-top: 16px;
                    padding: 12px;
                    background: var(--primary-background-color);
                    border-radius: 8px;
                    font-size: 13px;
                    color: var(--secondary-text-color);
                    text-align: center;
                    border: 1px solid var(--divider-color);
                    transition: all 0.3s ease;
                    position: relative;
                }
                
                .awtrix-status.success {
                    background: rgba(76, 175, 80, 0.1);
                    border-color: #4caf50;
                    color: #4caf50;
                }
                
                .awtrix-status.error {
                    background: rgba(244, 67, 54, 0.1);
                    border-color: #f44336;
                    color: #f44336;
                }
                
                .awtrix-status.loading {
                    background: rgba(33, 150, 243, 0.1);
                    border-color: #2196f3;
                    color: #2196f3;
                }
                
                .awtrix-status::before {
                    content: '📊';
                    margin-right: 8px;
                }
                
                .awtrix-status.success::before {
                    content: '✅';
                }
                
                .awtrix-status.error::before {
                    content: '❌';
                }
                
                .awtrix-status.loading::before {
                    content: '🔄';
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                
                .awtrix-section-icon {
                    font-size: 20px;
                    margin-right: 8px;
                }
                
                .button-group {
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 8px;
                }
                
                .button-group .awtrix-button {
                    margin-bottom: 0;
                }
                
                .entity-selector {
                    margin-bottom: 12px;
                }
                
                .entity-selector select {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid var(--divider-color);
                    border-radius: 8px;
                    background: var(--primary-background-color);
                    color: var(--primary-text-color);
                    font-size: 14px;
                    box-sizing: border-box;
                }
                
                @media (max-width: 768px) {
                    .awtrix-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .awtrix-card {
                        padding: 16px;
                    }
                    
                    .awtrix-header {
                        font-size: 20px;
                    }
                }
            </style>
            
            <div class="awtrix-card">
                <div class="awtrix-header">AWTRIX Control</div>
                
                <div class="awtrix-grid">
                    <div class="awtrix-section">
                        <h3><span class="awtrix-section-icon">📝</span>Text senden</h3>
                        <input type="text" class="awtrix-input" id="text-input" placeholder="Text eingeben...">
                        <button class="awtrix-button" id="send-text-btn">Senden</button>
                        <div class="awtrix-status" id="text-status">Bereit</div>
                    </div>
                    
                    <div class="awtrix-section">
                        <h3><span class="awtrix-section-icon">⚡</span>Schnell-Aktionen</h3>
                        <div class="button-group">
                            <button class="awtrix-button secondary" id="send-time-btn">⏰ Zeit</button>
                            <button class="awtrix-button secondary" id="send-test-btn">🧪 Test</button>
                            <button class="awtrix-button secondary" id="send-date-btn">📅 Datum</button>
                        </div>
                        <div class="awtrix-status" id="action-status">Bereit</div>
                    </div>
                    
                    <div class="awtrix-section">
                        <h3><span class="awtrix-section-icon">🌡️</span>Sensor senden</h3>
                        <div class="entity-selector">
                            <select id="sensor-selector">
                                <option value="">Sensor auswählen...</option>
                            </select>
                        </div>
                        <button class="awtrix-button info" id="send-sensor-btn">Senden</button>
                        <div class="awtrix-status" id="sensor-status">Bereit</div>
                    </div>
                </div>
            </div>
        `;
        
        this.setupEventListeners();
        this.loadSensorEntities();
    }

    async loadSensorEntities() {
        try {
            // Lade alle verfügbaren Sensor-Entities
            const entities = Object.values(this.hass.states || {})
                .filter(state => state.entity_id.startsWith('sensor.'))
                .map(state => ({
                    id: state.entity_id,
                    name: state.attributes.friendly_name || state.entity_id
                }))
                .sort((a, b) => a.name.localeCompare(b.name));

            const selector = this.shadowRoot.getElementById('sensor-selector');
            selector.innerHTML = '<option value="">Sensor auswählen...</option>';
            
            entities.forEach(entity => {
                const option = document.createElement('option');
                option.value = entity.id;
                option.textContent = entity.name;
                selector.appendChild(option);
            });
        } catch (error) {
            console.error('Fehler beim Laden der Sensor-Entities:', error);
        }
    }

    setupEventListeners() {
        // Text senden
        this.shadowRoot.getElementById('send-text-btn').addEventListener('click', () => {
            this.sendText();
        });

        // Zeit senden
        this.shadowRoot.getElementById('send-time-btn').addEventListener('click', () => {
            this.sendTime();
        });

        // Test senden
        this.shadowRoot.getElementById('send-test-btn').addEventListener('click', () => {
            this.sendTest();
        });

        // Datum senden
        this.shadowRoot.getElementById('send-date-btn').addEventListener('click', () => {
            this.sendDate();
        });

        // Sensor senden
        this.shadowRoot.getElementById('send-sensor-btn').addEventListener('click', () => {
            this.sendSensor();
        });

        // Enter-Taste für Text-Input
        this.shadowRoot.getElementById('text-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendText();
            }
        });
    }

    async sendText() {
        const text = this.shadowRoot.getElementById('text-input').value;
        const status = this.shadowRoot.getElementById('text-status');
        
        if (text.trim()) {
            this.setStatus(status, 'loading', 'Sende...');
            try {
                await this.hass.callService('awtrix_control', 'send_text', {
                    text: text,
                    slot: 0
                });
                this.setStatus(status, 'success', 'Gesendet: ' + text);
                this.shadowRoot.getElementById('text-input').value = '';
            } catch (error) {
                this.setStatus(status, 'error', 'Fehler: ' + error.message);
            }
        } else {
            this.setStatus(status, 'error', 'Kein Text eingegeben');
        }
    }

    async sendTime() {
        const status = this.shadowRoot.getElementById('action-status');
        this.setStatus(status, 'loading', 'Sende Zeit...');
        
        try {
            await this.hass.callService('awtrix_control', 'send_time', {
                slot: 0
            });
            this.setStatus(status, 'success', 'Zeit gesendet');
        } catch (error) {
            this.setStatus(status, 'error', 'Fehler: ' + error.message);
        }
    }

    async sendTest() {
        const status = this.shadowRoot.getElementById('action-status');
        this.setStatus(status, 'loading', 'Sende Test...');
        
        try {
            await this.hass.callService('awtrix_control', 'send_text', {
                text: 'AWTRIX Test',
                slot: 0
            });
            this.setStatus(status, 'success', 'Test gesendet');
        } catch (error) {
            this.setStatus(status, 'error', 'Fehler: ' + error.message);
        }
    }

    async sendDate() {
        const status = this.shadowRoot.getElementById('action-status');
        this.setStatus(status, 'loading', 'Sende Datum...');
        
        try {
            const now = new Date();
            const dateStr = now.toLocaleDateString('de-DE');
            await this.hass.callService('awtrix_control', 'send_text', {
                text: dateStr,
                slot: 1
            });
            this.setStatus(status, 'success', 'Datum gesendet');
        } catch (error) {
            this.setStatus(status, 'error', 'Fehler: ' + error.message);
        }
    }

    async sendSensor() {
        const sensor = this.shadowRoot.getElementById('sensor-selector').value;
        const status = this.shadowRoot.getElementById('sensor-status');
        
        if (sensor.trim()) {
            this.setStatus(status, 'loading', 'Sende Sensor...');
            try {
                await this.hass.callService('awtrix_control', 'send_sensor', {
                    sensor_name: 'Sensor',
                    sensor_entity: sensor,
                    slot: 2
                });
                this.setStatus(status, 'success', 'Sensor gesendet');
            } catch (error) {
                this.setStatus(status, 'error', 'Fehler: ' + error.message);
            }
        } else {
            this.setStatus(status, 'error', 'Kein Sensor ausgewählt');
        }
    }

    setStatus(element, type, message) {
        element.className = `awtrix-status ${type}`;
        element.textContent = message;
    }

    setHass(hass) {
        this.hass = hass;
        // Lade Sensor-Entities neu, wenn hass verfügbar ist
        if (this.shadowRoot) {
            this.loadSensorEntities();
        }
    }
}

// Registriere das Custom Element
customElements.define('awtrix-control-card', AwtrixControlCard);

// Debug-Ausgabe
console.log('AWTRIX Control Card geladen');
