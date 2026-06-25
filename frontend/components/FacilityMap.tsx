'use client';
import { useEffect, useRef } from 'react';
import type { Facility } from '@/lib/types';

interface Props {
  facilities: Facility[];
  height?: number;
}

function markerColor(xch4Trend: number | null): string {
  if (xch4Trend == null) return '#6B6560';
  if (xch4Trend < -1)  return '#386641';  // decreasing — good
  if (xch4Trend > 1)   return '#C1121F';  // increasing — bad
  return '#E76F00';                        // stable — amber
}

export default function FacilityMap({ facilities, height = 360 }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<unknown>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !mapRef.current || mapInstance.current) return;
    if (facilities.length === 0) return;

    // Dynamically import Leaflet (avoids SSR issues)
    async function initMap() {
      const L = (await import('leaflet')).default;

      const center = facilities.reduce(
        (acc, f) => [acc[0] + f.latitude / facilities.length, acc[1] + f.longitude / facilities.length],
        [0, 0]
      ) as [number, number];

      const map = L.map(mapRef.current!, {
        center,
        zoom: 4,
        zoomControl: true,
        attributionControl: true,
      });

      mapInstance.current = map;

      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors © CARTO',
        subdomains: 'abcd',
        maxZoom: 14,
      }).addTo(map);

      facilities.forEach(f => {
        const color = markerColor(f.xch4_trend);

        const icon = L.divIcon({
          className: '',
          html: `<div style="width:10px;height:10px;background:${color};border:2px solid white;
                 border-radius:50%;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>`,
          iconSize: [10, 10],
          iconAnchor: [5, 5],
        });

        const lines = [
          `<strong style="font-family:IBM Plex Sans,sans-serif">${f.facility_name}</strong>`,
          `<span style="font-family:IBM Plex Mono,monospace;font-size:11px">${f.latitude.toFixed(4)}°N, ${f.longitude.toFixed(4)}°E</span>`,
          f.operation_type ? `<em>${f.operation_type}</em>` : '',
          f.xch4_value != null ? `XCH4: ${f.xch4_value.toFixed(1)} ppb` : '',
          f.xch4_trend != null ? `Trend: ${f.xch4_trend > 0 ? '+' : ''}${f.xch4_trend.toFixed(2)}%` : '',
        ].filter(Boolean).join('<br/>');

        L.marker([f.latitude, f.longitude], { icon })
          .addTo(map)
          .bindPopup(`<div style="font-size:12px;line-height:1.6">${lines}</div>`);
      });

      if (facilities.length > 1) {
        const bounds = L.latLngBounds(facilities.map(f => [f.latitude, f.longitude]));
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    }

    initMap().catch(console.error);

    return () => {
      if (mapInstance.current) {
        (mapInstance.current as { remove: () => void }).remove();
        mapInstance.current = null;
      }
    };
  }, [facilities]);

  if (facilities.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-surface)', border: 'var(--beige-warm)', borderRadius: 'var(--radius)',
        color: 'var(--text-muted-light)', fontSize: '0.875rem' }}>
        No facility locations available
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <div ref={mapRef} style={{ height, borderRadius: 'var(--radius)', overflow: 'hidden',
        border: '1px solid var(--beige-warm)' }} />
      <div style={{ position: 'absolute', bottom: '8px', left: '8px', background: 'rgba(245,242,235,0.95)',
        border: '1px solid var(--beige-warm)', borderRadius: '2px', padding: '4px 8px',
        fontSize: '0.625rem', color: 'var(--text-muted-light)', fontFamily: 'var(--font-mono)', zIndex: 400 }}>
        <span style={{ color: 'var(--green-deep)' }}>● </span>XCH4 decreasing &nbsp;
        <span style={{ color: 'var(--classification-warrants)' }}>● </span>stable &nbsp;
        <span style={{ color: 'var(--classification-divergence)' }}>● </span>increasing
      </div>
    </div>
  );
}
