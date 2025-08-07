// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    addAirspaces();
    initDragAndDrop();
    console.log(`Loaded ${geojsonData.features ? geojsonData.features.length : 0} airspace features`);
});

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

function toggleExampleMenu() {
    const menu = document.getElementById('example-menu');
    const content = document.getElementById('exampleContent');
    const btn = document.getElementById('exampleToggleBtn');
    if (menu.classList.contains('minimized')) {
        menu.classList.remove('minimized');
        btn.textContent = '▼';
        content.style.display = '';
    } else {
        menu.classList.add('minimized');
        btn.textContent = '▲';
        content.style.display = 'none';
    }
}
// Minimize on load
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('example-menu').classList.add('minimized');
    document.getElementById('exampleContent').style.display = 'none';
    document.getElementById('exampleToggleBtn').textContent = '▲';
});