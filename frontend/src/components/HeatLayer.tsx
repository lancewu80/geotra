import L from 'leaflet'
import 'leaflet.heat'
import { useEffect } from 'react'
import { useMap } from 'react-leaflet'

interface Props {
  points: [number, number, number?][]
}

export function HeatLayer({ points }: Props) {
  const map = useMap()

  useEffect(() => {
    // @ts-expect-error leaflet.heat augments the L namespace at runtime; no bundled types
    const layer = L.heatLayer(points, { radius: 20, blur: 15, maxZoom: 1 })
    layer.addTo(map)
    return () => {
      map.removeLayer(layer)
    }
  }, [map, points])

  return null
}
