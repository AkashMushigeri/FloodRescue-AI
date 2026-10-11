import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import type { Incident } from '../types';

interface MapComponentProps {
  incidents?: Incident[];
  selectedIncident?: Incident | null;
  onSelectIncident?: (incident: Incident) => void;
  pickerMode?: boolean;
  selectedCoords?: { lat: number; lng: number } | null;
  onSelectCoords?: (lat: number, lng: number) => void;
  center?: [number, number];
  zoom?: number;
}

// Custom SVG marker generator based on priority
function createCustomMarker(priority?: string, isSelected: boolean = false): L.DivIcon {
  let color = '#3B82F6'; // medium blue
  if (priority === 'critical') color = '#EF4444'; // red
  else if (priority === 'high') color = '#F59E0B'; // amber/orange
  else if (priority === 'low') color = '#6B7280'; // gray

  const stroke = isSelected ? '#FFFFFF' : '#0B132B';
  const size = isSelected ? 36 : 28;

  const svgHtml = `
    <div style="transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center;">
      <svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="${color}" stroke="${stroke}" stroke-width="2">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
        <circle cx="12" cy="9" r="2.5" fill="#FFFFFF"/>
      </svg>
      ${isSelected ? `<span style="background: ${color}; color: white; font-size: 10px; font-weight: bold; padding: 1px 4px; border-radius: 4px; margin-top: -4px;">ACTIVE</span>` : ''}
    </div>
  `;

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: svgHtml,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
  });
}

function LocationPicker({ onSelect }: { onSelect: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onSelect(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export const MapComponent: React.FC<MapComponentProps> = ({
  incidents = [],
  selectedIncident,
  onSelectIncident,
  pickerMode = false,
  selectedCoords,
  onSelectCoords,
  center = [13.0475, 80.23], // Default center around flood area (e.g. Chennai)
  zoom = 12,
}) => {
  // Filter incidents that have valid coordinates
  const validIncidents = incidents.filter(
    (i) => i.latitude !== null && i.latitude !== undefined && i.longitude !== null && i.longitude !== undefined
  );

  return (
    <div className="w-full h-full min-h-[350px] relative rounded-lg overflow-hidden border border-disaster-cardBorder shadow-md">
      <MapContainer
        center={selectedCoords ? [selectedCoords.lat, selectedCoords.lng] : center}
        zoom={zoom}
        style={{ width: '100%', height: '100%', minHeight: '350px' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {pickerMode && onSelectCoords && <LocationPicker onSelect={onSelectCoords} />}

        {/* Selected Coordinates Pin in Picker Mode */}
        {pickerMode && selectedCoords && (
          <Marker
            position={[selectedCoords.lat, selectedCoords.lng]}
            icon={createCustomMarker('critical', true)}
          >
            <Popup>
              <div className="text-gray-900 text-xs font-medium">
                <strong>Selected Location Pin</strong><br />
                Lat: {selectedCoords.lat.toFixed(4)}, Lng: {selectedCoords.lng.toFixed(4)}
              </div>
            </Popup>
          </Marker>
        )}

        {/* Incident Markers */}
        {!pickerMode &&
          validIncidents.map((incident) => {
            const isSelected = selectedIncident?.incident_id === incident.incident_id;
            return (
              <Marker
                key={incident.incident_id}
                position={[incident.latitude!, incident.longitude!]}
                icon={createCustomMarker(incident.suggested_priority, isSelected)}
                eventHandlers={{
                  click: () => onSelectIncident && onSelectIncident(incident),
                }}
              >
                <Popup>
                  <div className="text-gray-900 text-xs p-1">
                    <div className="font-bold text-sm flex items-center justify-between gap-2 border-b pb-1 mb-1">
                      <span>{incident.incident_id}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase text-white ${
                        incident.suggested_priority === 'critical' ? 'bg-red-600' :
                        incident.suggested_priority === 'high' ? 'bg-amber-600' : 'bg-blue-600'
                      }`}>
                        {incident.suggested_priority}
                      </span>
                    </div>
                    <p className="font-semibold text-gray-800">
                      People Reported: <span className="text-red-700 font-bold">{incident.people_reported}</span>
                    </p>
                    <p className="text-gray-600">Water: {incident.water_level}</p>
                    <p className="text-gray-600">Landmark: {incident.landmark_description}</p>
                    {incident.has_injuries && (
                      <p className="text-red-600 font-bold mt-1">⚠️ Medical Emergency Reported</p>
                    )}
                    {onSelectIncident && (
                      <button
                        onClick={() => onSelectIncident(incident)}
                        className="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white py-1 px-2 rounded text-xs font-semibold"
                      >
                        Inspect Incident
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>
    </div>
  );
};
