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

// ============================================================
// REAL WAYANAD LANDSLIDE INVENTORY
// ============================================================
// 65 inventory records spatially matched to these 3 pilot
// villages from the processed Wayanad landslide inventory.
// ============================================================

const WAYANAD_LANDSLIDE_EVENTS = {
  'Thrikkaipatta Part': 3,
  'Vellarimala': 32,
  'Kottappadi Part': 30
};

function getRiskConfig(value) {
  if (value === null || value === undefined) {
    return RISK_CONFIG.low;
  }

  const score = Number(value);

  if (!Number.isFinite(score)) {
    return RISK_CONFIG.low;
  }

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
  showRisk,
  showLandslide
}) {
  if (showLandslide) return 'landslide';
  if (showRisk) return 'risk';
  if (showFlood) return 'flood';
  if (showCyclone) return 'cyclone';
  if (showRainfall) return 'rainfall';

  return 'habitations';
}

function getLatitude(habitation) {
  const value = Number(
    habitation?.centroid?.lat ??
    habitation?.latitude
  );

  return Number.isFinite(value)
    ? value
    : null;
}

function getLongitude(habitation) {
  const value = Number(
    habitation?.centroid?.lng ??
    habitation?.centroid?.lon ??
    habitation?.longitude
  );

  return Number.isFinite(value)
    ? value
    : null;
}

function hasValidCoordinates(habitation) {
  const lat = getLatitude(habitation);
  const lon = getLongitude(habitation);

  return (
    lat !== null &&
    lon !== null &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180
  );
}

function isWayanadLandslideVillage(habitation) {
  if (!habitation) {
    return false;
  }

  if (
    String(habitation.district || '')
      .toLowerCase() !== 'wayanad'
  ) {
    return false;
  }

  return (
    WAYANAD_LANDSLIDE_EVENTS[
      habitation.name
    ] !== undefined
  );
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
  const activePopupRef = useRef(null);

  const navigate = useNavigate();

  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;

  const onMarkerClickRef = useRef(onMarkerClick);
  onMarkerClickRef.current = onMarkerClick;

  // ==========================================================
  // CREATE MAP
  // ==========================================================

  useEffect(() => {
    if (!mapContainer.current) {
      return;
    }

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: OSM_RASTER_STYLE,
      center: [78.9629, 22.5937],
      zoom: 5,
      attributionControl: true
    });

    map.addControl(
      new maplibregl.NavigationControl(),
      'top-left'
    );

    mapInstance.current = map;

    map.on('load', () => {
      fitMapToHabitations(map, habitations);
    });

    return () => {
      activePopupRef.current = null;

      map.remove();

      mapInstance.current = null;
    };
  }, []);

  // ==========================================================
  // FIT MAP
  // ==========================================================

  useEffect(() => {
    if (!mapInstance.current) {
      return;
    }

    const map = mapInstance.current;

    if (!map.loaded()) {
      return;
    }

    fitMapToHabitations(
      map,
      habitations
    );
  }, [habitations]);

  // ==========================================================
  // MARKERS
  // ==========================================================

  useEffect(() => {
    if (!mapInstance.current) {
      return;
    }

    const map = mapInstance.current;

    markersRef.current.forEach(
      (marker) => marker.remove()
    );

    markersRef.current = [];

    activePopupRef.current = null;

    if (
      !Array.isArray(habitations) ||
      habitations.length === 0
    ) {
      return;
    }

    const activeLayer = getActiveLayer({
      showFlood,
      showCyclone,
      showRainfall,
      showRisk,
      showLandslide
    });

    if (
      activeLayer === 'habitations' &&
      !showHabitations
    ) {
      return;
    }

    habitations.forEach((h) => {
      if (!hasValidCoordinates(h)) {
        return;
      }

      const latitude = getLatitude(h);
      const longitude = getLongitude(h);

      const isLandslideVillage =
        isWayanadLandslideVillage(h);

      // --------------------------------------------------------
      // Hide non-landslide villages when landslide layer active
      // --------------------------------------------------------

      if (
        activeLayer === 'landslide' &&
        !isLandslideVillage
      ) {
        return;
      }

      let config;
      let layerLabel;

      // --------------------------------------------------------
      // LANDSLIDE
      // --------------------------------------------------------

      if (
        activeLayer === 'landslide'
      ) {
        config = {
          color: '#7f1d1d',
          size: 32,
          label: 'LS'
        };

        layerLabel =
          'Wayanad Landslide Inventory';
      }

      // --------------------------------------------------------
      // HABITATION PRIORITY
      // --------------------------------------------------------

      else if (
        activeLayer === 'habitations'
      ) {
        config =
          PRIORITY_CONFIG[
            h.priority
          ] ||
          PRIORITY_CONFIG.P4;

        layerLabel =
          'Village Priority';
      }

      // --------------------------------------------------------
      // OTHER HAZARDS
      // --------------------------------------------------------

      else {
        let hazardValue = null;

        if (
          activeLayer === 'risk'
        ) {
          hazardValue =
            h.risk_score != null
              ? Number(h.risk_score) / 100
              : null;
        } else {
          hazardValue =
            h.hazards?.[
              activeLayer
            ];
        }

        config =
          getRiskConfig(
            hazardValue
          );

        if (
          activeLayer === 'risk'
        ) {
          layerLabel =
            'Multi-Hazard Risk';
        }

        if (
          activeLayer === 'flood'
        ) {
          layerLabel =
            'Flood Risk';
        }

        if (
          activeLayer === 'cyclone'
        ) {
          layerLabel =
            'Cyclone Risk';
        }

        if (
          activeLayer === 'rainfall'
        ) {
          layerLabel =
            'Rainfall Risk';
        }
      }

      // ========================================================
      // MARKER
      // ========================================================

      const markerContainer =
        document.createElement('div');

      markerContainer.style.width =
        '44px';

      markerContainer.style.height =
        '44px';

      markerContainer.style.display =
        'flex';

      markerContainer.style.alignItems =
        'center';

      markerContainer.style.justifyContent =
        'center';

      markerContainer.style.cursor =
        'pointer';

      markerContainer.style.pointerEvents =
        'auto';

      markerContainer.style.background =
        'transparent';

      // --------------------------------------------------------
      // Circle
      // --------------------------------------------------------

      const innerCircle =
        document.createElement('div');

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
        '0 2px 8px rgba(0,0,0,0.4)';

      innerCircle.style.display =
        'flex';

      innerCircle.style.alignItems =
        'center';

      innerCircle.style.justifyContent =
        'center';

      innerCircle.style.color =
        '#ffffff';

      innerCircle.style.fontSize =
        '9px';

      innerCircle.style.fontWeight =
        'bold';

      innerCircle.style.pointerEvents =
        'none';

      innerCircle.innerText =
        config.label;

      markerContainer.appendChild(
        innerCircle
      );

      markerContainer.addEventListener(
        'mouseenter',
        () => {
          innerCircle.style.transform =
            'scale(1.2)';
        }
      );

      markerContainer.addEventListener(
        'mouseleave',
        () => {
          innerCircle.style.transform =
            'scale(1)';
        }
      );

      // ========================================================
      // POPUP
      // ========================================================

      const eventCount =
        WAYANAD_LANDSLIDE_EVENTS[
          h.name
        ];

      const popupHtml = `

        <div
          style="
            font-family:Inter,sans-serif;
            padding:4px;
            min-width:250px;
          "
        >

          <div
            style="
              border-bottom:1px solid #e2e8f0;
              padding-bottom:7px;
              margin-bottom:8px;
            "
          >

            <div
              style="
                font-size:10px;
                font-weight:700;
                color:#2563eb;
                font-family:monospace;
              "
            >
              ${escapeHtml(h.id)}
            </div>

            <div
              style="
                margin-top:2px;
                font-size:14px;
                font-weight:700;
                color:#0f172a;
              "
            >
              ${escapeHtml(h.name)}
            </div>

          </div>

          <div
            style="
              font-size:12px;
              line-height:1.6;
              color:#475569;
            "
          >

            <div
              style="
                display:flex;
                justify-content:space-between;
              "
            >
              <span>
                Layer:
              </span>

              <strong
                style="
                  color:${config.color};
                "
              >
                ${layerLabel}
              </strong>
            </div>

            <div
              style="
                display:flex;
                justify-content:space-between;
              "
            >
              <span>
                Priority:
              </span>

              <strong>
                ${h.priority || 'P4'}
              </strong>
            </div>

            <div
              style="
                display:flex;
                justify-content:space-between;
              "
            >
              <span>
                AASHRAY Risk:
              </span>

              <strong
                style="
                  color:#dc2626;
                "
              >
                ${
                  h.risk_score != null
                    ? `${Number(
                        h.risk_score
                      ).toFixed(1)} / 100`
                    : 'N/A'
                }
              </strong>
            </div>

            ${
              activeLayer === 'landslide'
                ? `
                  <div
                    style="
                      margin-top:8px;
                      padding-top:8px;
                      border-top:1px solid #e2e8f0;
                    "
                  >

                    <div
                      style="
                        display:flex;
                        justify-content:space-between;
                      "
                    >
                      <span>
                        Inventory Events:
                      </span>

                      <strong
                        style="
                          color:#7f1d1d;
                        "
                      >
                        ${eventCount}
                      </strong>
                    </div>

                    <div
                      style="
                        margin-top:5px;
                        font-size:10px;
                        color:#64748b;
                      "
                    >
                      Spatially matched records
                      from the Wayanad landslide
                      inventory.
                    </div>

                  </div>
                `
                : ''
            }

            <div
              style="
                display:flex;
                justify-content:space-between;
                margin-top:7px;
              "
            >

              <span>
                Population:
              </span>

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

            <div
              style="
                display:flex;
                justify-content:space-between;
                font-size:10px;
                color:#94a3b8;
                margin-top:8px;
              "
            >

              <span>
                Coordinates:
              </span>

              <span
                style="
                  font-family:monospace;
                "
              >
                ${latitude.toFixed(4)},
                ${longitude.toFixed(4)}
              </span>

            </div>

          </div>

          <button
            type="button"
            class="maplibre-view-details-btn"
            style="
              width:100%;
              margin-top:10px;
              background:#2563eb;
              color:#fff;
              border:0;
              padding:7px;
              border-radius:6px;
              font-size:12px;
              font-weight:600;
              cursor:pointer;
            "
          >
            View Village Profile →
          </button>

        </div>
      `;

      const popup =
        new maplibregl.Popup({
          offset: 14,
          closeButton: true,
          closeOnClick: false,
          maxWidth: '320px'
        }).setHTML(
          popupHtml
        );

      popup.on(
        'open',
        () => {
          activePopupRef.current =
            popup;

          const popupElement =
            popup.getElement();

          if (!popupElement) {
            return;
          }

          const detailsButton =
            popupElement.querySelector(
              '.maplibre-view-details-btn'
            );

          if (
            detailsButton
          ) {
            detailsButton.onclick =
              (event) => {
                event.preventDefault();
                event.stopPropagation();

                navigateRef.current(
                  `/habitation/${h.id}`
                );
              };
          }
        }
      );

      popup.on(
        'close',
        () => {
          if (
            activePopupRef.current ===
            popup
          ) {
            activePopupRef.current =
              null;
          }
        }
      );

      // ========================================================
      // ADD MARKER
      // ========================================================

      const marker =
        new maplibregl.Marker({
          element:
            markerContainer,
          anchor: 'center'
        })
          .setLngLat([
            longitude,
            latitude
          ])
          .setPopup(popup)
          .addTo(map);

      markerContainer.addEventListener(
        'click',
        (event) => {
          event.stopPropagation();

          if (
            activePopupRef.current &&
            activePopupRef.current !==
              popup
          ) {
            activePopupRef.current.remove();
          }

          marker.togglePopup();

          if (
            onMarkerClickRef.current
          ) {
            onMarkerClickRef.current(
              h
            );
          }
        }
      );

      markersRef.current.push(
        marker
      );
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

  return (
    <div
      className="
        relative
        w-full
        h-full
        min-h-[500px]
        rounded-xl
        overflow-hidden
        shadow-inner
        border
        border-slate-300
      "
    >

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
// FIT MAP
// ============================================================

function fitMapToHabitations(
  map,
  habitations
) {
  if (
    !Array.isArray(
      habitations
    ) ||
    habitations.length === 0
  ) {
    return;
  }

  const bounds =
    new maplibregl.LngLatBounds();

  let validCount = 0;

  habitations.forEach(
    (habitation) => {
      if (
        !hasValidCoordinates(
          habitation
        )
      ) {
        return;
      }

      const latitude =
        getLatitude(
          habitation
        );

      const longitude =
        getLongitude(
          habitation
        );

      bounds.extend([
        longitude,
        latitude
      ]);

      validCount++;
    }
  );

  if (
    validCount === 0 ||
    bounds.isEmpty()
  ) {
    return;
  }

  map.fitBounds(
    bounds,
    {
      padding: 60,
      maxZoom: 11,
      duration: 800
    }
  );
}

// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return '';
  }

  return String(value)
    .replaceAll(
      '&',
      '&amp;'
    )
    .replaceAll(
      '<',
      '&lt;'
    )
    .replaceAll(
      '>',
      '&gt;'
    )
    .replaceAll(
      '"',
      '&quot;'
    )
    .replaceAll(
      "'",
      '&#039;'
    );
}