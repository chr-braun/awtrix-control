class AwtrixSensorSelectorCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({mode: 'open'});
        this.selectedSensors = [];
        this.automationTemplate = '';
    }

    setConfig(config) {
        this.config = config;
        this.render();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                .sensor-selector-card {
                    padding: 20px;
                    background: var(--ha-card-background);
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    font-family: var(--mdc-typography-font-family);
                    border: 1px solid var(--divider-color);
                }
                
                .card-header {
                    font-size: 20px;
                    font-weight: 600;
                    margin-bottom: 20px;
                    color: var(--primary-text-color);
                    text-align: center;
                    border-bottom: 2px solid var(--primary-color);
                    padding-bottom: 10px;
                }
                
                .sensor-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 16px;
                    margin-bottom: 20px;
                }
                
                .sensor-item {
                    background: var(--secondary-background-color);
                    padding: 16px;
                    border-radius: 8px;
                    border: 2px solid var(--divider-color);
                    transition: all 0.3s ease;
                    cursor: pointer;
                    position: relative;
                }
                
                .sensor-item:hover {
                    border-color: var(--primary-color);
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
                
                .sensor-item.selected {
                    border-color: var(--primary-color);
                    background: rgba(0, 122, 255, 0.1);
                }
                
                .sensor-item.selected::before {
                    content: '✓';
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: var(--primary-color);
                    color: white;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: bold;
                }
                
                .sensor-name {
                    font-weight: 600;
                    color: var(--primary-text-color);
                    margin-bottom: 8px;
                    font-size: 14px;
                }
                
                .sensor-entity {
                    font-family: monospace;
                    color: var(--secondary-text-color);
                    font-size: 12px;
                    margin-bottom: 8px;
                }
                
                .sensor-value {
                    font-size: 18px;
                    font-weight: bold;
                    color: var(--primary-color);
                    margin-bottom: 8px;
                }
                
                .sensor-unit {
                    font-size: 12px;
                    color: var(--secondary-text-color);
                }
                
                .controls {
                    display: flex;
                    gap: 12px;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }
                
                .control-button {
                    padding: 10px 16px;
                    background: var(--primary-color);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    flex: 1;
                    min-width: 120px;
                }
                
                .control-button:hover {
                    background: var(--accent-color);
                    transform: translateY(-1px);
                }
                
                .control-button.secondary {
                    background: var(--accent-color);
                }
                
                .control-button.danger {
                    background: #f44336;
                }
                
                .automation-section {
                    background: var(--secondary-background-color);
                    padding: 16px;
                    border-radius: 8px;
                    border: 1px solid var(--divider-color);
                    margin-top: 20px;
                }
                
                .automation-header {
                    font-size: 16px;
                    font-weight: 600;
                    margin-bottom: 12px;
                    color: var(--primary-text-color);
                }
                
                .automation-code {
                    background: var(--primary-background-color);
                    padding: 12px;
                    border-radius: 6px;
                    font-family: monospace;
                    font-size: 12px;
                    color: var(--primary-text-color);
                    border: 1px solid var(--divider-color);
                    white-space: pre-wrap;
                    max-height: 300px;
                    overflow-y: auto;
                    margin-bottom: 12px;
                }
                
                .copy-button {
                    padding: 8px 16px;
                    background: var(--accent-color);
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.3s ease;
                }
                
                .copy-button:hover {
                    background: var(--primary-color);
                }
                
                .status-message {
                    padding: 12px;
                    border-radius: 6px;
                    margin-top: 12px;
                    font-size: 14px;
                    text-align: center;
                }
                
                .status-message.success {
                    background: rgba(76, 175, 80, 0.1);
                    border: 1px solid #4caf50;
                    color: #4caf50;
                }
                
                .status-message.error {
                    background: rgba(244, 67, 54, 0.1);
                    border: 1px solid #f44336;
                    color: #f44336;
                }
                
                .filter-section {
                    margin-bottom: 20px;
                    padding: 16px;
                    background: var(--secondary-background-color);
                    border-radius: 8px;
                    border: 1px solid var(--divider-color);
                }
                
                .filter-input {
                    width: 100%;
                    padding: 10px;
                    border: 2px solid var(--divider-color);
                    border-radius: 6px;
                    background: var(--primary-background-color);
                    color: var(--primary-text-color);
                    font-size: 14px;
                    margin-bottom: 12px;
                }
                
                .filter-input:focus {
                    border-color: var(--primary-color);
                    outline: none;
                }
                
                .filter-options {
                    display: flex;
                    gap: 12px;
                    flex-wrap: wrap;
                }
                
                .filter-option {
                    padding: 6px 12px;
                    background: var(--primary-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.3s ease;
                }
                
                .filter-option:hover {
                    background: var(--primary-color);
                    color: white;
                }
                
                .filter-option.active {
                    background: var(--primary-color);
                    color: white;
                    border-color: var(--primary-color);
                }
                
                @media (max-width: 768px) {
                    .sensor-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .controls {
                        flex-direction: column;
                    }
                    
                    .control-button {
                        min-width: auto;
                    }
                }
            </style>
            
            <div class="sensor-selector-card">
                <div class="card-header">🎯 AWTRIX Sensor-Auswahl</div>
                
                <div class="filter-section">
                    <input type="text" class="filter-input" id="search-input" placeholder="Sensoren durchsuchen...">
                    <div class="filter-options">
                        <div class="filter-option active" data-type="all">Alle</div>
                        <div class="filter-option" data-type="temperature">Temperatur</div>
                        <div class="filter-option" data-type="humidity">Luftfeuchtigkeit</div>
                        <div class="filter-option" data-type="pressure">Druck</div>
                        <div class="filter-option" data-type="power">Strom/Leistung</div>
                        <div class="filter-option" data-type="other">Sonstige</div>
                    </div>
                </div>
                
                <div class="controls">
                    <button class="control-button" id="select-all-btn">Alle auswählen</button>
                    <button class="control-button secondary" id="deselect-all-btn">Alle abwählen</button>
                    <button class="control-button" id="test-selected-btn">Ausgewählte testen</button>
                    <button class="control-button danger" id="clear-selected-btn">Auswahl löschen</button>
                </div>
                
                <div class="sensor-grid" id="sensor-grid">
                    <!-- Sensoren werden hier dynamisch geladen -->
                </div>
                
                <div class="automation-section" id="automation-section" style="display: none;">
                    <div class="automation-header">🤖 Automatisierung generieren</div>
                    <div class="automation-code" id="automation-code"></div>
                    <button class="copy-button" id="copy-automation-btn">Code kopieren</button>
                </div>
                
                <div id="status-message"></div>
            </div>
        `;
        
        this.setupEventListeners();
        this.loadSensors();
    }

    setupEventListeners() {
        // Suchfunktion
        this.shadowRoot.getElementById('search-input').addEventListener('input', (e) => {
            this.filterSensors(e.target.value);
        });

        // Filter-Optionen
        this.shadowRoot.querySelectorAll('.filter-option').forEach(option => {
            option.addEventListener('click', (e) => {
                this.shadowRoot.querySelectorAll('.filter-option').forEach(opt => opt.classList.remove('active'));
                e.target.classList.add('active');
                this.filterSensors(this.shadowRoot.getElementById('search-input').value, e.target.dataset.type);
            });
        });

        // Kontroll-Buttons
        this.shadowRoot.getElementById('select-all-btn').addEventListener('click', () => this.selectAllSensors());
        this.shadowRoot.getElementById('deselect-all-btn').addEventListener('click', () => this.deselectAllSensors());
        this.shadowRoot.getElementById('test-selected-btn').addEventListener('click', () => this.testSelectedSensors());
        this.shadowRoot.getElementById('clear-selected-btn').addEventListener('click', () => this.clearSelectedSensors());
        this.shadowRoot.getElementById('copy-automation-btn').addEventListener('click', () => this.copyAutomationCode());
    }

    async loadSensors() {
        try {
            const entities = Object.values(this.hass.states || {})
                .filter(state => state.entity_id.startsWith('sensor.'))
                .map(state => ({
                    id: state.entity_id,
                    name: state.attributes.friendly_name || state.entity_id,
                    state: state.state,
                    unit: state.attributes.unit_of_measurement || '',
                    type: this.getSensorType(state)
                }))
                .sort((a, b) => a.name.localeCompare(b.name));

            this.renderSensors(entities);
        } catch (error) {
            console.error('Fehler beim Laden der Sensoren:', error);
            this.showStatus('Fehler beim Laden der Sensoren', 'error');
        }
    }

    getSensorType(state) {
        const entityId = state.entity_id.toLowerCase();
        const friendlyName = (state.attributes.friendly_name || '').toLowerCase();
        
        if (entityId.includes('temp') || entityId.includes('temperature') || friendlyName.includes('temp') || friendlyName.includes('temperatur')) {
            return 'temperature';
        } else if (entityId.includes('humidity') || entityId.includes('hum') || friendlyName.includes('luftfeuchtigkeit') || friendlyName.includes('feuchtigkeit')) {
            return 'humidity';
        } else if (entityId.includes('pressure') || entityId.includes('baro') || friendlyName.includes('druck') || friendlyName.includes('barometer')) {
            return 'pressure';
        } else if (entityId.includes('power') || entityId.includes('watt') || entityId.includes('ampere') || entityId.includes('volt') || 
                   friendlyName.includes('leistung') || friendlyName.includes('strom') || friendlyName.includes('spannung')) {
            return 'power';
        } else {
            return 'other';
        }
    }

    renderSensors(sensors) {
        const grid = this.shadowRoot.getElementById('sensor-grid');
        grid.innerHTML = '';

        sensors.forEach(sensor => {
            const sensorElement = document.createElement('div');
            sensorElement.className = 'sensor-item';
            sensorElement.dataset.entityId = sensor.id;
            sensorElement.dataset.type = sensor.type;
            
            sensorElement.innerHTML = `
                <div class="sensor-name">${sensor.name}</div>
                <div class="sensor-entity">${sensor.id}</div>
                <div class="sensor-value">${sensor.state}</div>
                <div class="sensor-unit">${sensor.unit}</div>
            `;
            
            sensorElement.addEventListener('click', () => this.toggleSensorSelection(sensor, sensorElement));
            grid.appendChild(sensorElement);
        });
    }

    toggleSensorSelection(sensor, element) {
        const isSelected = element.classList.contains('selected');
        
        if (isSelected) {
            element.classList.remove('selected');
            this.selectedSensors = this.selectedSensors.filter(s => s.id !== sensor.id);
        } else {
            element.classList.add('selected');
            this.selectedSensors.push(sensor);
        }
        
        this.updateAutomationSection();
    }

    selectAllSensors() {
        this.shadowRoot.querySelectorAll('.sensor-item').forEach(item => {
            if (!item.classList.contains('selected')) {
                item.classList.add('selected');
                const sensor = {
                    id: item.dataset.entityId,
                    name: item.querySelector('.sensor-name').textContent,
                    type: item.dataset.type
                };
                this.selectedSensors.push(sensor);
            }
        });
        this.updateAutomationSection();
    }

    deselectAllSensors() {
        this.shadowRoot.querySelectorAll('.sensor-item').forEach(item => {
            item.classList.remove('selected');
        });
        this.selectedSensors = [];
        this.updateAutomationSection();
    }

    clearSelectedSensors() {
        this.selectedSensors = [];
        this.shadowRoot.querySelectorAll('.sensor-item').forEach(item => {
            item.classList.remove('selected');
        });
        this.updateAutomationSection();
    }

    async testSelectedSensors() {
        if (this.selectedSensors.length === 0) {
            this.showStatus('Keine Sensoren ausgewählt', 'error');
            return;
        }

        this.showStatus('Teste ausgewählte Sensoren...', 'success');
        
        for (const sensor of this.selectedSensors) {
            try {
                await this.hass.callService('awtrix_control', 'send_sensor', {
                    sensor_name: sensor.name,
                    sensor_entity: sensor.id,
                    slot: Math.min(this.selectedSensors.indexOf(sensor), 7),
                    color: this.getColorForType(sensor.type)
                });
                await new Promise(resolve => setTimeout(resolve, 1000)); // 1 Sekunde Pause
            } catch (error) {
                console.error(`Fehler beim Testen von ${sensor.name}:`, error);
            }
        }
        
        this.showStatus(`${this.selectedSensors.length} Sensoren getestet`, 'success');
    }

    getColorForType(type) {
        const colors = {
            'temperature': '#FF6B35',
            'humidity': '#00A3FF',
            'pressure': '#9C27B0',
            'power': '#FFD700',
            'other': '#4CAF50'
        };
        return colors[type] || '#666666';
    }

    updateAutomationSection() {
        const section = this.shadowRoot.getElementById('automation-section');
        const codeElement = this.shadowRoot.getElementById('automation-code');
        
        if (this.selectedSensors.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        this.automationTemplate = this.generateAutomationCode();
        codeElement.textContent = this.automationTemplate;
    }

    generateAutomationCode() {
        let code = `# AWTRIX Sensor-Automatisierung
# Generiert von AWTRIX Control Sensor-Selector

automation:
  # Automatische Sensor-Updates alle 5 Minuten
  - alias: "AWTRIX Sensor Updates"
    description: "Sendet ausgewählte Sensor-Werte an AWTRIX"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    action:
`;

        // Ersetze Platzhalter mit echten Sensor-Daten
        this.selectedSensors.forEach((sensor, index) => {
            const slot = Math.min(index, 7);
            const color = this.getColorForType(sensor.type);
            code += `      - service: awtrix_control.send_sensor
        data:
          sensor_name: "${sensor.name}"
          sensor_entity: ${sensor.id}
          slot: ${slot}
          color: "${color}"
`;
            if (index < this.selectedSensors.length - 1) {
                code += `      - delay: "00:00:02"
`;
            }
        });

        code += `
# Script für manuelle Updates
script:
  awtrix_sensor_update:
    alias: "AWTRIX Sensor Update"
    description: "Sendet alle ausgewählten Sensoren an AWTRIX"
    sequence:
`;

        // Füge Script-Sequenz hinzu
        this.selectedSensors.forEach((sensor, index) => {
            const slot = Math.min(index, 7);
            const color = this.getColorForType(sensor.type);
            code += `      - service: awtrix_control.send_sensor
        data:
          sensor_name: "${sensor.name}"
          sensor_entity: ${sensor.id}
          slot: ${slot}
          color: "${color}"
`;
            if (index < this.selectedSensors.length - 1) {
                code += `      - delay: "00:00:02"
`;
            }
        });

        code += `
# Lovelace Button für manuelle Updates
# Füge dies zu deinem Dashboard hinzu:
type: button
name: "AWTRIX Sensor Update"
tap_action:
  action: call-service
  service: script.awtrix_sensor_update
icon: mdi:refresh
`;

        return code;
    }

    filterSensors(searchTerm, filterType = 'all') {
        const items = this.shadowRoot.querySelectorAll('.sensor-item');
        
        items.forEach(item => {
            const name = item.querySelector('.sensor-name').textContent.toLowerCase();
            const entityId = item.querySelector('.sensor-entity').textContent.toLowerCase();
            const type = item.dataset.type;
            
            const matchesSearch = !searchTerm || name.includes(searchTerm.toLowerCase()) || entityId.includes(searchTerm.toLowerCase());
            const matchesType = filterType === 'all' || type === filterType;
            
            item.style.display = matchesSearch && matchesType ? 'block' : 'none';
        });
    }

    async copyAutomationCode() {
        try {
            await navigator.clipboard.writeText(this.automationTemplate);
            this.showStatus('Code in Zwischenablage kopiert!', 'success');
        } catch (error) {
            console.error('Fehler beim Kopieren:', error);
            this.showStatus('Fehler beim Kopieren des Codes', 'error');
        }
    }

    showStatus(message, type) {
        const statusElement = this.shadowRoot.getElementById('status-message');
        statusElement.className = `status-message ${type}`;
        statusElement.textContent = message;
        
        setTimeout(() => {
            statusElement.textContent = '';
            statusElement.className = 'status-message';
        }, 5000);
    }

    setHass(hass) {
        this.hass = hass;
        if (this.shadowRoot) {
            this.loadSensors();
        }
    }
}

// Registriere das Custom Element
customElements.define('awtrix-sensor-selector-card', AwtrixSensorSelectorCard);

// Debug-Ausgabe
console.log('AWTRIX Sensor Selector Card geladen und registriert');




