import L from 'leaflet'
import { useMemo } from 'react'
import { CircleMarker, MapContainer, Polygon, Polyline, Tooltip } from 'react-leaflet'
import type { Line, LivePosition, XY, Zone } from '../types'
import { HeatLayer } from './HeatLayer'

// Must match FRAME_WIDTH / FRAME_HEIGHT in backend/.env — both sides treat
// the camera frame's pixel space as the map's planar coordinate system.
const FRAME_WIDTH = 1280
const FRAME_HEIGHT = 720

function toLatLng([x, y]: XY): [number, number] {
  // backend coords are pixel space (y grows downward); Leaflet's CRS.Simple
  // has y growing upward, so flip it
  return [FRAME_HEIGHT - y, x]
}

interface Props {
  zones: Zone[]
  lines: Line[]
  livePositions: Map<number, LivePosition>
  heatPoints: XY[]
}

export function MapView({ zones, lines, livePositions, heatPoints }: Props) {
  const bounds: L.LatLngBoundsExpression = [
    [0, 0],
    [FRAME_HEIGHT, FRAME_WIDTH],
  ]

  const heat = useMemo<[number, number, number][]>(
    () => heatPoints.map((p) => [...toLatLng(p), 0.5] as [number, number, number]),
    [heatPoints],
  )

  return (
    <MapContainer
      crs={L.CRS.Simple}
      bounds={bounds}
      style={{ height: '100%', width: '100%', background: '#111' }}
      maxZoom={4}
      minZoom={-2}
    >
      <HeatLayer points={heat} />
      {zones.map((zone) => (
        <Polygon
          key={zone.id}
          positions={zone.polygon.map(toLatLng)}
          pathOptions={{ color: '#3b82f6' }}
        >
          <Tooltip>{zone.name}</Tooltip>
        </Polygon>
      ))}
      {lines.map((line) => (
        <Polyline
          key={line.id}
          positions={line.coords.map(toLatLng)}
          pathOptions={{ color: '#f97316', weight: 3 }}
        >
          <Tooltip>{line.name}</Tooltip>
        </Polyline>
      ))}
      {Array.from(livePositions.values()).map((pos) => (
        <CircleMarker
          key={pos.track_id}
          center={toLatLng([pos.x, pos.y])}
          radius={6}
          pathOptions={{ color: '#22c55e', fillOpacity: 0.9 }}
        >
          <Tooltip permanent direction="top" offset={[0, -6]}>
            #{pos.track_id}
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
