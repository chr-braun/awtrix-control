// AWTRIX Control Cards Loader
// Diese Datei lädt alle Custom Cards für AWTRIX Control

console.log('AWTRIX Control Cards werden geladen...');

// Funktion zum Laden der Cards
function loadAwtrixCards() {
    // Lade die Haupt-Control Card
    const controlScript = document.createElement('script');
    controlScript.src = '/awtrix_control/awtrix-control.js';
    controlScript.onload = () => {
        console.log('✅ AWTRIX Control Card geladen');
        
        // Lade die Sensor-Selector Card nach der Control Card
        const sensorScript = document.createElement('script');
        sensorScript.src = '/awtrix_control/sensor-selector-card.js';
        sensorScript.onload = () => {
            console.log('✅ AWTRIX Sensor Selector Card geladen');
            console.log('🎯 Alle AWTRIX Control Cards sind bereit!');
            
            // Registriere die Cards global
            window.AWTRIX_CARDS_LOADED = true;
            
            // Dispatch Event für andere Komponenten
            window.dispatchEvent(new CustomEvent('awtrix-cards-loaded'));
        };
        sensorScript.onerror = (error) => {
            console.error('❌ Fehler beim Laden der Sensor Selector Card:', error);
        };
        document.head.appendChild(sensorScript);
    };
    controlScript.onerror = (error) => {
        console.error('❌ Fehler beim Laden der Control Card:', error);
    };
    document.head.appendChild(controlScript);
}

// Warte bis das DOM geladen ist
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAwtrixCards);
} else {
    // DOM ist bereits geladen
    loadAwtrixCards();
}

// Alternative: Falls DOM bereits geladen ist
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM geladen, lade AWTRIX Cards...');
    if (!window.AWTRIX_CARDS_LOADED) {
        loadAwtrixCards();
    }
});

// Registriere die Cards global
window.AWTRIX_CARDS_LOADED = false;
console.log('🎯 AWTRIX Control Cards Loader ist bereit!');
