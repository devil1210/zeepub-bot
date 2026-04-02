/* src/static/js/dashboard.js */

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error('Error fetching status:', error);
        document.getElementById('connection-status').innerHTML = '<span class="pulse" style="background:#ef4444"></span> OFFLINE';
    }
}

function updateUI(data) {
    // 1. Conexión
    document.getElementById('connection-status').innerHTML = '<span class="pulse"></span> ONLINE';
    
    // 2. Sistema
    const cpu = data.system.cpu_usage_percent;
    document.getElementById('cpu-value').innerText = `${cpu}%`;
    document.getElementById('cpu-progress').style.width = `${cpu}%`;
    
    document.getElementById('ram-value').innerText = `${data.system.ram_usage_mb} MB`;
    
    // 3. Librería
    document.getElementById('total-books').innerText = data.library.total_books;
    document.getElementById('pending-ia').innerText = data.library.pending_ai_corrections;
    
    // 4. Logs
    document.getElementById('uptime').innerText = data.uptime;
    document.getElementById('version').innerText = data.library.engine_version;
    document.getElementById('last-sync').innerText = new Date().toLocaleTimeString();
}

// Iniciar ciclo de actualización
fetchStatus();
setInterval(fetchStatus, 3000); // Cada 3 segundos
