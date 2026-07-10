// Side view: vertical cross-section of the airspaces above a clicked point.
// Toggled via a map control; while active, map clicks open the profile panel
// instead of the stacked airspace popup.

let sideViewMode = false;
let sideViewMarker = null;

const sideviewPanel = document.getElementById('sideview');

const ELEVATION_API = 'https://api.open-meteo.com/v1/elevation';
const UNLIMITED_DISPLAY_MARGIN = 1.15; // headroom above the highest finite bound

// --- Mode toggle control ------------------------------------------------------

const SideViewControl = L.Control.extend({
    options: { position: 'topleft' },
    onAdd: function () {
        const container = L.DomUtil.create('div', 'leaflet-bar side-view-control');
        const btn = L.DomUtil.create('a', 'side-view-toggle', container);
        btn.href = '#';
        btn.innerHTML = '⛰';
        btn.title = 'Toggle side view mode (click map to see the vertical airspace profile)';
        btn.setAttribute('role', 'button');
        btn.setAttribute('aria-pressed', 'false');

        L.DomEvent.on(btn, 'click', (e) => {
            L.DomEvent.stop(e);
            setSideViewMode(!sideViewMode, btn);
        });

        this._btn = btn;
        return container;
    }
});

function setSideViewMode(active, btn) {
    sideViewMode = active;
    const toggleBtn = btn || document.querySelector('.side-view-toggle');
    if (toggleBtn) {
        toggleBtn.classList.toggle('active', active);
        toggleBtn.setAttribute('aria-pressed', String(active));
    }
    map.getContainer().classList.toggle('side-view-cursor', active);
    if (!active) {
        closeSideView();
    }
}

function closeSideView() {
    sideviewPanel.classList.add('hidden');
    if (sideViewMarker) {
        map.removeLayer(sideViewMarker);
        sideViewMarker = null;
    }
}

// --- Ground elevation ----------------------------------------------------------

async function fetchGroundElevation(lat, lng) {
    const url = `${ELEVATION_API}?latitude=${lat.toFixed(5)}&longitude=${lng.toFixed(5)}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Elevation API returned ${response.status}`);
    const data = await response.json();
    if (!data.elevation || !data.elevation.length) throw new Error('No elevation data');
    return data.elevation[0];
}

// --- Click handling --------------------------------------------------------------

async function onSideViewClick(e) {
    if (!sideViewMode) return;

    const latlng = e.latlng;

    if (sideViewMarker) map.removeLayer(sideViewMarker);
    sideViewMarker = L.marker(latlng).addTo(map);

    const hits = findAirspacesAtPoint(latlng);

    // Show the panel immediately with a loading note, then fill in ground data
    renderSideView(latlng, null, hits, 'Loading ground elevation…');

    let ground = null;
    let note = '';
    try {
        ground = await fetchGroundElevation(latlng.lat, latlng.lng);
    } catch (err) {
        console.warn('Ground elevation lookup failed:', err);
        note = 'Ground elevation unavailable — AGL bounds shown relative to sea level.';
    }

    // Ignore stale responses if the user clicked elsewhere meanwhile
    if (!sideViewMode || !sideViewMarker || !sideViewMarker.getLatLng().equals(latlng)) return;

    renderSideView(latlng, ground, hits, note);
}

// --- Rendering --------------------------------------------------------------------

function formatMeters(m) {
    return `${Math.round(m)} m`;
}

// Human-readable resolved bounds line, e.g. "GND – 2438 m AMSL"
function describeBounds(props, ground) {
    const lower = resolveAltitudeMeters(props.lowerMeters, props.lowerRef, ground || 0);
    const upper = resolveAltitudeMeters(props.upperMeters, props.upperRef, ground || 0);
    const lowerTxt = lower === null ? escapeHtml(props.lowerBound) : `${formatMeters(lower)} AMSL`;
    const upperTxt = upper === null ? 'Unlimited' : `${formatMeters(upper)} AMSL`;
    return `${escapeHtml(props.lowerBound)} &ndash; ${escapeHtml(props.upperBound)}
        <span class="sideview-resolved">(&asymp; ${lowerTxt} &ndash; ${upperTxt})</span>`;
}

function niceTickStep(range) {
    const targets = [100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000];
    const raw = range / 6;
    for (const t of targets) {
        if (t >= raw) return t;
    }
    return targets[targets.length - 1];
}

function renderSideView(latlng, ground, features, note) {
    const groundM = ground === null || ground === undefined ? null : ground;
    const g = groundM || 0;

    // Sort ground-up so bar order matches the physical stack
    const sorted = [...features].sort((a, b) => sortKeyLower(a.properties) - sortKeyLower(b.properties));

    // Vertical extent of the plot
    let maxFinite = 0;
    let hasUnlimited = false;
    sorted.forEach((f) => {
        const p = f.properties;
        const lower = resolveAltitudeMeters(p.lowerMeters, p.lowerRef, g);
        const upper = resolveAltitudeMeters(p.upperMeters, p.upperRef, g);
        if (upper === null) hasUnlimited = true;
        maxFinite = Math.max(maxFinite, lower || 0, upper || 0);
    });
    maxFinite = Math.max(maxFinite, g + 1000);
    const maxAlt = Math.ceil((maxFinite * UNLIMITED_DISPLAY_MARGIN) / 500) * 500;

    // SVG geometry
    const W = 460, H = 320;
    const m = { top: 14, right: 12, bottom: 22, left: 58 };
    const plotW = W - m.left - m.right;
    const plotH = H - m.top - m.bottom;
    const y = (alt) => m.top + plotH - (alt / maxAlt) * plotH;

    let svg = `<svg viewBox="0 0 ${W} ${H}" class="sideview-svg" role="img" aria-label="Vertical airspace profile">`;

    // Sky background
    svg += `<rect x="${m.left}" y="${m.top}" width="${plotW}" height="${plotH}" class="sideview-sky"/>`;

    // Y axis ticks + gridlines
    const step = niceTickStep(maxAlt);
    for (let alt = 0; alt <= maxAlt; alt += step) {
        const ty = y(alt);
        svg += `<line x1="${m.left}" y1="${ty}" x2="${W - m.right}" y2="${ty}" class="sideview-grid"/>`;
        svg += `<text x="${m.left - 6}" y="${ty + 3.5}" class="sideview-tick" text-anchor="end">${alt}</text>`;
    }
    svg += `<text x="12" y="${m.top + 2}" class="sideview-axis-label">m AMSL</text>`;

    // Ground
    if (groundM !== null) {
        const gy = y(Math.min(groundM, maxAlt));
        svg += `<rect x="${m.left}" y="${gy}" width="${plotW}" height="${m.top + plotH - gy}" class="sideview-ground"/>`;
        svg += `<line x1="${m.left}" y1="${gy}" x2="${W - m.right}" y2="${gy}" class="sideview-ground-line"/>`;
        svg += `<text x="${W - m.right - 4}" y="${gy - 4}" text-anchor="end" class="sideview-ground-label">ground ${formatMeters(groundM)}</text>`;
    }

    // Airspace columns
    const n = sorted.length;
    const slot = n ? plotW / n : plotW;
    const barW = Math.min(slot * 0.72, 90);

    sorted.forEach((f, i) => {
        const p = f.properties;
        const color = p.color || getAirspaceColor(p.class);
        const lower = resolveAltitudeMeters(p.lowerMeters, p.lowerRef, g) || 0;
        const upperRaw = resolveAltitudeMeters(p.upperMeters, p.upperRef, g);
        const unlimited = upperRaw === null;
        const upper = unlimited ? maxAlt : Math.min(upperRaw, maxAlt);

        const x = m.left + slot * i + (slot - barW) / 2;
        const yTop = y(upper);
        const yBottom = y(Math.min(lower, maxAlt));
        const h = Math.max(yBottom - yTop, 2);

        svg += `<g class="sideview-bar">`;
        svg += `<rect x="${x}" y="${yTop}" width="${barW}" height="${h}" fill="${color}" fill-opacity="0.45" stroke="${color}" stroke-width="1.5"${unlimited ? ' stroke-dasharray="4 3"' : ''}/>`;
        if (unlimited) {
            svg += `<text x="${x + barW / 2}" y="${yTop + 12}" text-anchor="middle" class="sideview-unlimited">&#8734;</text>`;
        }
        // Number badge linking bar to the list below
        const badgeY = Math.max(yTop + h / 2, yTop + 10);
        svg += `<circle cx="${x + barW / 2}" cy="${badgeY}" r="9" fill="${color}"/>`;
        svg += `<text x="${x + barW / 2}" y="${badgeY + 3.5}" text-anchor="middle" class="sideview-badge">${i + 1}</text>`;
        svg += `<title>${escapeHtml(p.name)} (Class ${escapeHtml(p.class)})\n${escapeHtml(p.lowerBound)} – ${escapeHtml(p.upperBound)}</title>`;
        svg += `</g>`;
    });

    // Axis line
    svg += `<line x1="${m.left}" y1="${m.top}" x2="${m.left}" y2="${m.top + plotH}" class="sideview-axis"/>`;
    svg += `</svg>`;

    // Details list
    let list = '';
    if (n) {
        list = sorted.map((f, i) => {
            const p = f.properties;
            const color = p.color || getAirspaceColor(p.class);
            return `
                <div class="sideview-item" onclick="zoomToFeature(${f._idx})" title="Zoom to airspace">
                    <span class="sideview-item-badge" style="background:${color}">${i + 1}</span>
                    <div class="stacked-text">
                        <div class="stacked-name">${escapeHtml(p.name)} <span class="sideview-class">Class ${escapeHtml(p.class)}</span></div>
                        <div class="stacked-bounds">${describeBounds(p, groundM)}</div>
                    </div>
                </div>`;
        }).join('');
    } else {
        list = '<div class="sideview-empty">No airspaces at this point.</div>';
    }

    const groundTxt = groundM === null
        ? ''
        : `<span class="sideview-ground-info">Ground: ${formatMeters(groundM)} AMSL</span>`;

    sideviewPanel.innerHTML = `
        <div class="sideview-header">
            <div>
                <strong>Side view</strong>
                <span class="sideview-coords">${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)}</span>
                ${groundTxt}
            </div>
            <button class="sideview-close" onclick="closeSideView()" title="Close" aria-label="Close side view">&times;</button>
        </div>
        ${note ? `<div class="sideview-note">${escapeHtml(note)}</div>` : ''}
        ${svg}
        <div class="sideview-list">${list}</div>
    `;
    sideviewPanel.classList.remove('hidden');
}

// --- Init ---------------------------------------------------------------------

map.addControl(new SideViewControl());
map.on('click', onSideViewClick);
