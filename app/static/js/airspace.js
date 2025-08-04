
// Styling constants
const defaultWeight = 2;
const highlightedWeight = 5;
const defaultStyle = {
    weight: defaultWeight,
    opacity: 0.6,
    interactive: true,
};

let airspaceLayer = null;

// Color mapping for airspace classes - now uses centralized config
function getAirspaceColor(airspaceClass) {
    return AIRSPACE_COLORS[airspaceClass] || DEFAULT_AIRSPACE_COLOR;
}

// Highlight airspace function
function highlightAirspace(airspace) {
    return function (e) {
        const polygon = e.target;
        polygon.setStyle({
            weight: highlightedWeight,
        });

        const nameEl = airspaceinfo.querySelector('.name');
        const classEl = airspaceinfo.querySelector('.class');
        const boundsEl = airspaceinfo.querySelector('.bounds');

        nameEl.innerText = airspace.name;
        classEl.innerHTML = `<span class="airspace-class class-${airspace.class}">Class ${airspace.class}</span>`;
        boundsEl.innerText = `From ${airspace.lowerBound} to ${airspace.upperBound}`;
        airspaceinfo.classList.remove('hidden');
    };
}

// Reset highlight function
function resetHighlight(e) {
    const polygon = e.target;
    polygon.setStyle({
        weight: defaultWeight,
    });
    airspaceinfo.classList.add('hidden');
}

// Zoom to airspace function
function zoomToAirspace(e) {
    const polygon = e.target;
    map.fitBounds(polygon.getBounds());
}

// Style function for airspaces
function airspaceStyle(feature) {
    const airspaceClass = feature.properties.class;
    const color = feature.properties.color || getAirspaceColor(airspaceClass);

    return Object.assign({}, defaultStyle, {
        fillColor: color,
        color: color,
        fillOpacity: 0.4
    });
}

// Feature interaction
function onEachFeature(feature, layer) {
    const props = feature.properties;

    // Event listeners
    layer.addEventListener('mouseover', highlightAirspace(props));
    layer.addEventListener('mouseout', resetHighlight);
    layer.addEventListener('click', zoomToAirspace);

    // Popup content
    const popupContent = `
        <div>
            <h6>${props.name}</h6>
            <p><span class="airspace-class class-${props.class}">${props.class}</span></p>
            <p><strong>Lower:</strong> ${props.lowerBound}<br>
            <strong>Upper:</strong> ${props.upperBound}</p>
        </div>
    `;

    layer.bindPopup(popupContent);
}

// Add airspaces to map
function addAirspaces() {
    if (geojsonData && geojsonData.features) {
        // Sort airspaces
        const sortedFeatures = [...geojsonData.features].sort((a, b) => {
            // Circles (smaller features) should be on top
            const aIsCircle = a.geometry.type === 'Polygon' && isCircleFeature(a);
            const bIsCircle = b.geometry.type === 'Polygon' && isCircleFeature(b);

            if (aIsCircle && !bIsCircle) return 1;
            if (!aIsCircle && bIsCircle) return -1;

            return 0;
        });

        const sortedGeoJSON = {
            ...geojsonData,
            features: sortedFeatures
        };

        airspaceLayer = L.geoJSON(sortedGeoJSON, {
            style: airspaceStyle,
            onEachFeature: onEachFeature
        }).addTo(map);

        // Fit map to bounds
        if (airspaceLayer.getBounds().isValid()) {
            map.fitBounds(airspaceLayer.getBounds());
        }
    }
}

// Helper function to detect if a polygon feature represents a circle
function isCircleFeature(feature) {
    if (feature.geometry.type !== 'Polygon') return false;
    const coords = feature.geometry.coordinates[0];
    return coords.length > 30; // Circles are approximated with many points
}
