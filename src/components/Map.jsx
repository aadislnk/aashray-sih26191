import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const OSM_RASTER_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: [
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
      ],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors'
    }
  },
  layers: [
    {
      id: 'osm',
      type: 'raster',
      source: 'osm'
    }
  ]
};

const PRIORITY_CONFIG = {
  P1: {
    color: '#dc2626',
    size: 30,
    label: 'P1'
  },
  P2: {
    color: '#f97316',
    size: 26,
    label: 'P2'
  },
  P3: {
    color: '#eab308',
    size: 22,
    label: 'P3'
  },
  P4: {
    color: '#22c55e',
    size: 18,
    label: 'P4'
  }
};

const RISK_CONFIG = {
  very_high: {
    color: '#dc2626',
    size: 28,
    label: 'VH'
  },
  high: {
    color: '#f97316',
    size: 25,
    label: 'H'
  },
  moderate: {
    color: '#eab308',
    size: 22,
    label: 'M'
  },
  low: {
    color: '#22c55e',
    size: 19,
    label: 'L'
  }
};

function getRiskConfig(value) {
  if (value == null) {
    return RISK_CONFIG.low;
  }

  const score = Number(value);

  if (score >= 0.75) {
    return RISK_CONFIG.very_high;
  }

  if (score >= 0.50) {
    return RISK_CONFIG.high;
  }

  if (score >= 0.25) {
    return RISK_CONFIG.moderate;
  }

  return RISK_CONFIG.low;
}

function getActiveLayer({
  showFlood,
  showCyclone,
  showRainfall,
  showRisk
}) {
  if (showRisk) return 'risk';
  if (showFlood) return 'flood';
  if (showCyclone) return 'cyclone';
  if (showRainfall) return 'rainfall';

  return 'habitations';
}

export default function Map({
  habitations = [],
  onMarkerClick,
  showHabitations = true,
  showFlood = false,
  showCyclone = false,
  showRainfall = false,
  showRisk = false,
  showLandslide = false
}) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);

  // ============================================================
  // ACTIVE POPUP
  // ============================================================

  // Keeps track of the one village popup currently open.
  const activePopupRef = useRef(null);

  const navigate = useNavigate();

  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;

  const onMarkerClickRef = useRef(onMarkerClick);
  onMarkerClickRef.current = onMarkerClick;

  // ============================================================
  // CREATE MAP
  // ============================================================

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: OSM_RASTER_STYLE,

      center: [76.5, 10.5],

      zoom: 7,

      attributionControl: true
    });

    map.addControl(
      new maplibregl.NavigationControl(),
      'top-left'
    );

    mapInstance.current = map;

    map.on('load', () => {
      if (habitations.length === 0) return;

      const bounds = new maplibregl.LngLatBounds();

      habitations.forEach((h) => {
        if (
          h.centroid &&
          typeof h.centroid.lat === 'number' &&
          typeof h.centroid.lon === 'number'
        ) {
          bounds.extend([
            h.centroid.lon,
            h.centroid.lat
          ]);
        }
      });

      if (!bounds.isEmpty()) {
        map.fitBounds(
          bounds,
          {
            padding: 60,
            maxZoom: 11,
            duration: 800
          }
        );
      }
    });

    return () => {
      if (activePopupRef.current) {
        activePopupRef.current.remove();
        activePopupRef.current = null;
      }

      map.remove();

      mapInstance.current = null;
    };
  }, []);

  // ============================================================
  // CREATE / REFRESH MARKERS
  // ============================================================

  useEffect(() => {
    if (!mapInstance.current) return;

    const map = mapInstance.current;

    // ----------------------------------------------------------
    // CLOSE CURRENT POPUP BEFORE REBUILDING MARKERS
    // ----------------------------------------------------------

    if (activePopupRef.current) {
      activePopupRef.current.remove();
      activePopupRef.current = null;
    }

    // ----------------------------------------------------------
    // REMOVE OLD MARKERS
    // ----------------------------------------------------------

    markersRef.current.forEach(
      (marker) => marker.remove()
    );

    markersRef.current = [];

    if (!habititionsValid(habitations)) {
      return;
    }

    const activeLayer = getActiveLayer({
      showFlood,
      showCyclone,
      showRainfall,
      showRisk
    });

    if (
      activeLayer === 'habitations' &&
      !showHabitations
    ) {
      return;
    }

    if (showLandslide) {
      console.warn(
        'Landslide layer requires Wayanad/Kerala spatial data and is not drawn over the current hazard dataset.'
      );
    }

    habitations.forEach((h) => {
      if (
        !h.centroid ||
        typeof h.centroid.lat !== 'number' ||
        typeof h.centroid.lon !== 'number'
      ) {
        return;
      }

      let config;

      let layerLabel = 'Habitations';

      if (activeLayer === 'habitations') {
        config =
          PRIORITY_CONFIG[h.priority] ||
          PRIORITY_CONFIG.P4;

        layerLabel = 'Village Priority';
      } else {
        const hazardValue =
          h.hazards?.[activeLayer];

        config = getRiskConfig(hazardValue);

        if (activeLayer === 'risk') {
          layerLabel = 'Multi-Hazard Risk';
        }

        if (activeLayer === 'flood') {
          layerLabel = 'Flood Risk';
        }

        if (activeLayer === 'cyclone') {
          layerLabel = 'Cyclone Risk';
        }

        if (activeLayer === 'rainfall') {
          layerLabel = 'Rainfall Risk';
        }
      }

      // ========================================================
      // MARKER
      // ========================================================

      const markerContainer =
        document.createElement('div');

      markerContainer.className =
        'maplibre-marker-hitbox';

      markerContainer.style.width = '44px';
      markerContainer.style.height = '44px';
      markerContainer.style.display = 'flex';
      markerContainer.style.alignItems = 'center';
      markerContainer.style.justifyContent = 'center';
      markerContainer.style.cursor = 'pointer';
      markerContainer.style.pointerEvents = 'auto';
      markerContainer.style.background = 'transparent';
      markerContainer.style.userSelect = 'none';

      const innerCircle =
        document.createElement('div');

      innerCircle.className =
        'maplibre-marker-circle';

      innerCircle.style.width =
        `${config.size}px`;

      innerCircle.style.height =
        `${config.size}px`;

      innerCircle.style.backgroundColor =
        config.color;

      innerCircle.style.border =
        '2.5px solid #ffffff';

      innerCircle.style.borderRadius =
        '50%';

      innerCircle.style.boxShadow =
        '0 2px 8px rgba(0,0,0,0.35)';

      innerCircle.style.display = 'flex';
      innerCircle.style.alignItems = 'center';
      innerCircle.style.justifyContent = 'center';

      innerCircle.style.color = '#ffffff';

      innerCircle.style.fontSize =
        config.size >= 26
          ? '9px'
          : '8px';

      innerCircle.style.fontWeight = 'bold';

      innerCircle.style.transformOrigin =
        'center center';

      innerCircle.style.transition =
        'transform 0.15s ease, box-shadow 0.15s ease';

      innerCircle.style.pointerEvents = 'none';

      innerCircle.innerText = config.label;

      markerContainer.appendChild(
        innerCircle
      );

      // ========================================================
      // HOVER EFFECT
      // ========================================================

      markerContainer.addEventListener(
        'mouseenter',
        () => {
          innerCircle.style.transform =
            'scale(1.22)';

          innerCircle.style.boxShadow =
            '0 4px 14px rgba(0,0,0,0.45)';
        }
      );

      markerContainer.addEventListener(
        'mouseleave',
        () => {
          innerCircle.style.transform =
            'scale(1)';

          innerCircle.style.boxShadow =
            '0 2px 8px rgba(0,0,0,0.35)';
        }
      );

      // ========================================================
      // HAZARD DATA
      // ========================================================

      const hazards = h.hazards || {};

      const hazardRows = `
        <div style="
          margin-top:8px;
          padding-top:8px;
          border-top:1px solid #e2e8f0;
        ">

          <div style="
            font-weight:700;
            color:#0f172a;
            margin-bottom:4px;
          ">
            AI/ML Hazard Scores
          </div>

          <div style="
            display:flex;
            justify-content:space-between;
          ">
            <span>Coastal</span>
            <strong>
              ${formatHazard(hazards.coastal)}
            </strong>
          </div>

          <div style="
            display:flex;
            justify-content:space-between;
          ">
            <span>Flood</span>
            <strong>
              ${formatHazard(hazards.flood)}
            </strong>
          </div>

          <div style="
            display:flex;
            justify-content:space-between;
          ">
            <span>Cyclone</span>
            <strong>
              ${formatHazard(hazards.cyclone)}
            </strong>
          </div>

          <div style="
            display:flex;
            justify-content:space-between;
          ">
            <span>Rainfall</span>
            <strong>
              ${formatHazard(hazards.rainfall)}
            </strong>
          </div>

        </div>
      `;

      // ========================================================
      // POPUP HTML
      // ========================================================

      const popupHtml = `

        <div style="
          font-family:Inter,sans-serif;
          padding:4px;
          min-width:240px;
        ">

          <div style="
            border-bottom:1px solid #e2e8f0;
            padding-bottom:6px;
            margin-bottom:8px;
          ">

            <span style="
              font-size:10px;
              font-weight:700;
              color:#2563eb;
              font-family:monospace;
            ">
              ${h.id}
            </span>

            <h4 style="
              margin:2px 0 0 0;
              font-size:14px;
              font-weight:700;
              color:#0f172a;
            ">
              ${h.name}
            </h4>

          </div>

          <div style="
            font-size:12px;
            line-height:1.6;
            color:#475569;
            margin-bottom:10px;
          ">

            <div style="
              display:flex;
              justify-content:space-between;
            ">
              <span>Layer:</span>

              <strong style="
                color:${config.color};
              ">
                ${layerLabel}
              </strong>
            </div>

            <div style="
              display:flex;
              justify-content:space-between;
            ">
              <span>Priority:</span>

              <strong style="
                color:${config.color};
              ">
                ${h.priority}
              </strong>
            </div>

            <div style="
              display:flex;
              justify-content:space-between;
            ">
              <span>Overall Risk:</span>

              <strong style="
                color:#dc2626;
              ">
                ${h.risk_score ?? 'N/A'} / 100
              </strong>
            </div>

            <div style="
              display:flex;
              justify-content:space-between;
            ">
              <span>Population:</span>

              <strong>
                ${
                  h.population != null
                    ? Number(
                        h.population
                      ).toLocaleString()
                    : 'N/A'
                }
              </strong>
            </div>

            ${hazardRows}

            <div style="
              display:flex;
              justify-content:space-between;
              font-size:11px;
              color:#94a3b8;
              margin-top:8px;
            ">

              <span>Centroid:</span>

              <span style="
                font-family:monospace;
              ">
                ${h.centroid.lat.toFixed(3)},
                ${h.centroid.lon.toFixed(3)}
              </span>

            </div>

          </div>

          <button
            type="button"
            class="maplibre-view-details-btn"
            style="
              width:100%;
              display:block;
              text-align:center;
              background-color:#2563eb;
              color:#ffffff;
              border:none;
              font-size:12px;
              font-weight:600;
              padding:7px 12px;
              border-radius:6px;
              cursor:pointer;
            "
          >
            View Details →
          </button>

        </div>
      `;

      // ========================================================
      // POPUP
      // ========================================================

      const popup =
        new maplibregl.Popup({
          offset: 14,
          closeButton: true,

          // IMPORTANT:
          // We control popup closing ourselves.
          closeOnClick: false,

          maxWidth: '320px'
        })
        .setHTML(popupHtml);

      // ========================================================
      // POPUP OPEN
      // ========================================================

      popup.on('open', () => {
        activePopupRef.current = popup;

        const popupEl =
          popup.getElement();

        if (!popupEl) return;

        const detailsBtn =
          popupEl.querySelector(
            '.maplibre-view-details-btn'
          );

        if (detailsBtn) {
          detailsBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();

            if (navigateRef.current) {
              navigateRef.current(
                `/habitation/${h.id}`
              );
            }
          };
        }
      });

      // ========================================================
      // POPUP CLOSE
      // ========================================================

      popup.on('close', () => {
        if (
          activePopupRef.current === popup
        ) {
          activePopupRef.current = null;
        }
      });

      // ========================================================
      // MARKER
      // ========================================================

      const marker =
        new maplibregl.Marker({
          element: markerContainer,
          anchor: 'center'
        })
        .setLngLat([
          h.centroid.lon,
          h.centroid.lat
        ])
        .setPopup(popup)
        .addTo(map);

      // ========================================================
      // MARKER CLICK
      // ========================================================

      markerContainer.addEventListener(
        'click',
        (e) => {
          e.stopPropagation();

          // ----------------------------------------------------
          // CLOSE PREVIOUS VILLAGE POPUP
          // ----------------------------------------------------

          if (
            activePopupRef.current &&
            activePopupRef.current !== popup
          ) {
            activePopupRef.current.remove();

            activePopupRef.current = null;
          }

          // ----------------------------------------------------
          // TOGGLE CURRENT VILLAGE
          // ----------------------------------------------------

          marker.togglePopup();

          // ----------------------------------------------------
          // UPDATE SELECTED VILLAGE
          // ----------------------------------------------------

          if (onMarkerClickRef.current) {
            onMarkerClickRef.current(h);
          }
        }
      );

      markersRef.current.push(marker);
    });

  }, [
    habitations,
    showHabitations,
    showFlood,
    showCyclone,
    showRainfall,
    showRisk,
    showLandslide
  ]);

  // ============================================================
  // MAP CONTAINER
  // ============================================================

  return (
    <div className="
      relative
      w-full
      h-full
      min-h-[500px]
      rounded-xl
      overflow-hidden
      shadow-inner
      border
      border-slate-300
    ">
      <div
        ref={mapContainer}
        className="
          w-full
          h-full
          min-h-[500px]
        "
      />
    </div>
  );
}


// ============================================================
// VALIDATION
// ============================================================

function habititionsValid(habitations) {
  return (
    Array.isArray(habitations) &&
    habitations.length > 0
  );
}


// ============================================================
// HAZARD FORMATTER
// ============================================================

function formatHazard(value) {
  if (value == null) {
    return 'N/A';
  }

  return `${(
    Number(value) * 100
  ).toFixed(1)}`;
}