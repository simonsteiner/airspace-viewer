// DOM elements
const mapdiv = document.getElementById("map");

// Initialize the map centered on Switzerland
const map = L.map('map').setView([46.8182, 8.2275], 8);

L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
}).addTo(map);

// Control panel toggle functionality
function toggleControlPanel() {
    const panel = document.getElementById('controlPanel');
    const toggleBtn = document.getElementById('toggleBtn');
    const isMinimized = panel.classList.contains('minimized');

    if (isMinimized) {
        panel.classList.remove('minimized');
        toggleBtn.textContent = '▲';
    } else {
        panel.classList.add('minimized');
        toggleBtn.textContent = '▼';
    }
}
