/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect } from 'react'

// Fix para ícones do Leaflet no Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

interface Farm {
  id: string
  name: string
  crop: string
  lat: number
  lon: number
  icon: string
  color: string
}

interface MapProps {
  farms: Farm[]
  selectedFarm: Farm | null
  onSelectFarm: (farm: Farm) => void
  isLoading: boolean
}

// Componente para ajustar o centro do mapa
function MapController({ selectedFarm }: { selectedFarm: Farm | null }) {
  const map = useMap()

  useEffect(() => {
    if (selectedFarm) {
      map.flyTo([selectedFarm.lat, selectedFarm.lon], 7, {
        duration: 1.5,
      })
    }
  }, [selectedFarm, map])

  return null
}

export default function Map({
  farms,
  selectedFarm,
  onSelectFarm,
  isLoading,
}: MapProps) {
  // Criar ícones customizados para cada fazenda
  const createCustomIcon = (farm: Farm, isSelected: boolean) => {
    const size = isSelected ? 48 : 36
    return L.divIcon({
      html: `
        <div style="
          width: ${size}px;
          height: ${size}px;
          background: ${farm.color};
          border: 4px solid white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: ${size * 0.5}px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          transition: all 0.3s ease;
          cursor: pointer;
          ${isSelected ? 'transform: scale(1.2); box-shadow: 0 6px 20px rgba(0,0,0,0.4);' : ''}
        ">
          ${farm.icon}
        </div>
      `,
      className: 'custom-marker',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    })
  }

  return (
    <MapContainer
      center={[40, -100]}
      zoom={4}
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {farms.map((farm) => (
        <Marker
          key={farm.id}
          position={[farm.lat, farm.lon]}
          icon={createCustomIcon(farm, selectedFarm?.id === farm.id)}
          eventHandlers={{
            click: () => {
              onSelectFarm(farm)
            },
          }}
        >
          <Popup>
            <div className="text-center p-2">
              <div className="text-3xl mb-2">{farm.icon}</div>
              <h3 className="font-bold text-gray-900 text-lg">{farm.name}</h3>
              <p className="text-sm text-gray-600">{farm.crop}</p>
              <p className="text-xs text-gray-500 mt-1">
                {farm.lat.toFixed(4)}°, {farm.lon.toFixed(4)}°
              </p>
              <button
                onClick={() => onSelectFarm(farm)}
                disabled={isLoading}
                className={`mt-3 font-semibold py-2 px-4 rounded-lg text-sm transition-colors ${
                  isLoading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
              >
                {isLoading ? 'Aguarde...' : 'Selecionar Fazenda'}
              </button>
            </div>
          </Popup>
        </Marker>
      ))}

      <MapController selectedFarm={selectedFarm} />
    </MapContainer>
  )
}
