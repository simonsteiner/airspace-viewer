// DOM elements
const airspaceinfo = document.getElementById("airspaceinfo");

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

// Escape user-provided strings (airspace names come from uploaded files)
function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

// Generate airspace info HTML (used for both popup and info panel)
function generateAirspaceInfoHTML(props) {
    return `
        <div>
            <h6 class="airspace-class class-${escapeHtml(props.class)}">${escapeHtml(props.name)}<br>Class ${escapeHtml(props.class)}</h6>
            <p>
                <strong>Lower:</strong> ${escapeHtml(props.lowerBound)}<br>
                <strong>Upper:</strong> ${escapeHtml(props.upperBound)}
            </p>
        </div>
    `;
}

// Highlight airspace function
function highlightAirspace(airspace) {
    return function (e) {
        const polygon = e.target;
        polygon.setStyle({
            weight: highlightedWeight,
        });

        // Suppress the hover info panel while side view mode is active
        if (typeof sideViewMode !== 'undefined' && sideViewMode) return;

        // Use the same HTML as popup for the info panel
        airspaceinfo.innerHTML = generateAirspaceInfoHTML(airspace);
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

// --- Point-in-polygon lookup -------------------------------------------------

// Ray casting on a GeoJSON ring ([lng, lat] pairs)
function pointInRing(lng, lat, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const xi = ring[i][0], yi = ring[i][1];
        const xj = ring[j][0], yj = ring[j][1];
        if (((yi > lat) !== (yj > lat)) &&
            (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
            inside = !inside;
        }
    }
    return inside;
}

function featureContainsPoint(feature, latlng) {
    if (!feature.geometry || feature.geometry.type !== 'Polygon') return false;
    const rings = feature.geometry.coordinates;
    if (!rings.length || !pointInRing(latlng.lng, latlng.lat, rings[0])) return false;
    // Point must not fall into a hole
    for (let i = 1; i < rings.length; i++) {
        if (pointInRing(latlng.lng, latlng.lat, rings[i])) return false;
    }
    return true;
}

// All airspaces whose polygon contains the given point
function findAirspacesAtPoint(latlng) {
    if (!geojsonData || !geojsonData.features) return [];
    return geojsonData.features.filter((f) => featureContainsPoint(f, latlng));
}

// --- Altitude helpers (shared with side view) --------------------------------

// Resolve a bound to meters AMSL for sorting/plotting.
// AGL bounds are offset by the ground elevation when known.
function resolveAltitudeMeters(meters, ref, groundElevation) {
    if (meters === null || meters === undefined) return null; // unlimited/unknown
    if (ref === 'AGL') return (groundElevation || 0) + meters;
    return meters; // AMSL or FL (standard atmosphere approximation)
}

function sortKeyLower(props) {
    const v = resolveAltitudeMeters(props.lowerMeters, props.lowerRef, 0);
    return v === null ? 0 : v;
}

// --- Stacked airspace popup ---------------------------------------------------

function generateStackedListHTML(features) {
    // Highest floor first, so the list reads like the vertical stack
    const sorted = [...features].sort((a, b) => sortKeyLower(b.properties) - sortKeyLower(a.properties));

    const items = sorted.map((feature) => {
        const props = feature.properties;
        const color = props.color || getAirspaceColor(props.class);
        return `
            <div class="stacked-item" onclick="zoomToFeature(${feature._idx})" title="Zoom to airspace">
                <span class="stacked-color" style="background:${color}"></span>
                <div class="stacked-text">
                    <div class="stacked-name">${escapeHtml(props.name)}</div>
                    <div class="stacked-bounds">Class ${escapeHtml(props.class)} &middot; ${escapeHtml(props.lowerBound)} &ndash; ${escapeHtml(props.upperBound)}</div>
                </div>
            </div>`;
    }).join('');

    return `
        <div class="stacked-popup">
            <div class="stacked-title">${sorted.length} airspace${sorted.length !== 1 ? 's' : ''} at this point</div>
            ${items}
        </div>`;
}

// Zoom to a feature by its index in geojsonData.features (used from popup HTML)
function zoomToFeature(idx) {
    const feature = geojsonData.features[idx];
    if (feature && feature._layer) {
        map.closePopup();
        map.fitBounds(feature._layer.getBounds());
    }
}

function onMapClick(e) {
    // Side view mode has its own click handling (side_view.js)
    if (typeof sideViewMode !== 'undefined' && sideViewMode) return;

    const hits = findAirspacesAtPoint(e.latlng);
    if (!hits.length) return;

    L.popup({ maxWidth: 320, maxHeight: 340 })
        .setLatLng(e.latlng)
        .setContent(generateStackedListHTML(hits))
        .openOn(map);
}

// Feature interaction
function onEachFeature(feature, layer) {
    const props = feature.properties;

    // Keep a feature -> layer link for zooming from the stacked popup
    feature._layer = layer;

    // Event listeners
    layer.addEventListener('mouseover', highlightAirspace(props));
    layer.addEventListener('mouseout', resetHighlight);
    // Clicks bubble to the map, which shows the stacked airspace popup
}

// Add airspaces to map
function addAirspaces() {
    if (geojsonData && geojsonData.features) {
        // Remember original index for popup -> feature lookup
        geojsonData.features.forEach((f, i) => { f._idx = i; });

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

    map.on('click', onMapClick);
}

// Helper function to detect if a polygon feature represents a circle
function isCircleFeature(feature) {
    if (feature.geometry.type !== 'Polygon') return false;
    const coords = feature.geometry.coordinates[0];
    return coords.length > 30; // Circles are approximated with many points
}
