
// Airspace color configuration - injected from Python
{{ airspace_colors_js | safe }}

// Airspace data from server
const geojsonData = {{ geojson | safe }};
