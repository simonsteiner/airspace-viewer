// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    addAirspaces();
    initDragAndDrop();
    console.log(`Loaded ${geojsonData.features ? geojsonData.features.length : 0} airspace features`);
});
