import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// OpenStreetMap Free Raster Style
const OSM_RASTER_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
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

// Priority Color & Size Configurations
const PRIORITY_CONFIG = {
  P1: { color: '#dc2626', size: 30, label: 'P1' },
  P2: { color: '#f97316', size: 26, label: 'P2' },
  P3: { color: '#eab308', size: 22, label: 'P3' },
  P4: { color: '#22c55e', size: 18, label: 'P4' }
};

export default function Map({ habitations = [], onMarkerClick, showHabitations = true }) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);

  // Use refs to prevent stale closure issues in MapLibre event handlers
  const navigate = useNavigate();
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;

  const onMarkerClickRef = useRef(onMarkerClick);
  onMarkerClickRef.current = onMarkerClick;

  // Initialize MapLibre instance once
  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: OSM_RASTER_STYLE,
      center: [76.13, 11.68], // [lon, lat]
      zoom: 11,
      attributionControl: true
    });

    // Add zoom and rotation controls to top-left
    map.addControl(new maplibregl.NavigationControl(), 'top-left');

    mapInstance.current = map;

    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  // Update Markers when habitations or showHabitations layer toggle changes
  useEffect(() => {
    if (!mapInstance.current) return;

    // Remove existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    if (!showHabitations || !habitations.length) return;

    const map = mapInstance.current;

    habitations.forEach((h) => {
      if (!h.centroid || typeof h.centroid.lat !== 'number' || typeof h.centroid.lon !== 'number') {
        return;
      }

      const config = PRIORITY_CONFIG[h.priority] || PRIORITY_CONFIG.P4;

      // 1. Outer Container (Hit Target Box)
      // Provides a generous 44x44px clickable area without interfering with MapLibre's position transforms
      const markerContainer = document.createElement('div');
      markerContainer.className = 'maplibre-marker-hitbox';
      markerContainer.style.width = '44px';
      markerContainer.style.height = '44px';
      markerContainer.style.display = 'flex';
      markerContainer.style.alignItems = 'center';
      markerContainer.style.justifyContent = 'center';
      markerContainer.style.cursor = 'pointer';
      markerContainer.style.pointerEvents = 'auto';
      markerContainer.style.background = 'transparent';
      markerContainer.style.userSelect = 'none';

      // 2. Inner Visual Circle Element (Scales smoothly on hover without shifting coordinate transforms)
      const innerCircle = document.createElement('div');
      innerCircle.className = 'maplibre-marker-circle';
      innerCircle.style.width = `${config.size}px`;
      innerCircle.style.height = `${config.size}px`;
      innerCircle.style.backgroundColor = config.color;
      innerCircle.style.border = '2.5px solid #ffffff';
      innerCircle.style.borderRadius = '50%';
      innerCircle.style.boxShadow = '0 2px 8px rgba(0,0,0,0.35)';
      innerCircle.style.display = 'flex';
      innerCircle.style.alignItems = 'center';
      innerCircle.style.justifyContent = 'center';
      innerCircle.style.color = '#ffffff';
      innerCircle.style.fontSize = config.size >= 26 ? '10px' : '9px';
      innerCircle.style.fontWeight = 'bold';
      innerCircle.style.transformOrigin = 'center center';
      innerCircle.style.transition = 'transform 0.15s ease, box-shadow 0.15s ease';
      innerCircle.style.pointerEvents = 'none'; // Click goes to markerContainer
      innerCircle.innerText = config.label;

      markerContainer.appendChild(innerCircle);

      // Safe hover animation applied strictly to the inner circle
      markerContainer.addEventListener('mouseenter', () => {
        innerCircle.style.transform = 'scale(1.22)';
        innerCircle.style.boxShadow = '0 4px 14px rgba(0,0,0,0.45)';
      });
      markerContainer.addEventListener('mouseleave', () => {
        innerCircle.style.transform = 'scale(1)';
        innerCircle.style.boxShadow = '0 2px 8px rgba(0,0,0,0.35)';
      });

      // 3. Build Popup HTML
      const popupHtml = `
        <div style="font-family: Inter, sans-serif; padding: 4px; min-width: 220px;">
          <div style="border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 8px;">
            <span style="font-size: 10px; font-weight: 700; color: #2563eb; font-family: monospace;">${h.id}</span>
            <h4 style="margin: 2px 0 0 0; font-size: 14px; font-weight: 700; color: #0f172a;">${h.name}</h4>
          </div>
          <div style="font-size: 12px; line-height: 1.6; color: #475569; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
              <span>Priority:</span>
              <strong style="color: ${config.color};">${h.priority}</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span>Risk Score:</span>
              <strong style="color: #dc2626;">${h.risk_score} / 100</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span>Population:</span>
              <strong>${h.population?.toLocaleString() || 'N/A'}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; margin-top: 2px;">
              <span>Centroid:</span>
              <span style="font-family: monospace;">${h.centroid.lat.toFixed(3)}, ${h.centroid.lon.toFixed(3)}</span>
            </div>
          </div>
          <button 
            type="button"
            class="maplibre-view-details-btn"
            style="
              width: 100%;
              display: block; 
              text-align: center; 
              background-color: #2563eb; 
              color: #ffffff; 
              border: none;
              font-size: 12px; 
              font-weight: 600; 
              padding: 7px 12px; 
              border-radius: 6px; 
              cursor: pointer;
              transition: background-color 0.15s ease;
            "
          >
            View Details →
          </button>
        </div>
      `;

      const popup = new maplibregl.Popup({
        offset: 14,
        closeButton: true,
        closeOnClick: false,
        maxWidth: '300px'
      }).setHTML(popupHtml);

      // Attach button click handler upon popup DOM render
      popup.on('open', () => {
        const popupEl = popup.getElement();
        if (!popupEl) return;

        const detailsBtn = popupEl.querySelector('.maplibre-view-details-btn');
        if (detailsBtn) {
          detailsBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (navigateRef.current) {
              navigateRef.current(`/habitation/${h.id}`);
            }
          };

          detailsBtn.onmouseenter = () => {
            detailsBtn.style.backgroundColor = '#1d4ed8';
          };
          detailsBtn.onmouseleave = () => {
            detailsBtn.style.backgroundColor = '#2563eb';
          };
        }
      });

      // 4. Create and add Marker with center anchor
      const marker = new maplibregl.Marker({ 
        element: markerContainer,
        anchor: 'center'
      })
        .setLngLat([h.centroid.lon, h.centroid.lat])
        .setPopup(popup)
        .addTo(map);

      // 5. Handle Click on Marker
      markerContainer.addEventListener('click', (e) => {
        e.stopPropagation();
        marker.togglePopup();
        if (onMarkerClickRef.current) {
          onMarkerClickRef.current(h);
        }
      });

      markersRef.current.push(marker);
    });
  }, [habitations, showHabitations]);

  return (
    <div className="relative w-full h-full min-h-[500px] rounded-xl overflow-hidden shadow-inner border border-slate-300">
      <div ref={mapContainer} className="w-full h-full min-h-[500px]" />
    </div>
  );
}
