export type XY = [number, number]

export interface Zone {
  id: number
  name: string
  polygon: XY[]
}

export interface Line {
  id: number
  name: string
  coords: [XY, XY]
  in_direction: 'left' | 'right'
}

export interface ZoneStats {
  zone_id: number
  zone_name: string
  current_occupancy: number
  avg_dwell_seconds: number | null
}

export interface CrossingStats {
  line_id: number
  line_name: string
  in_count: number
  out_count: number
}

export interface LivePosition {
  track_id: number
  x: number
  y: number
  ts: string
}

export type LiveEvent =
  | ({ type: 'position' } & LivePosition)
  | { type: 'crossing'; line_id: number; track_id: number; direction: 'in' | 'out'; ts: string }
  | { type: 'zone_enter'; zone_id: number; track_id: number; ts: string }
  | { type: 'zone_exit'; zone_id: number; track_id: number; dwell_seconds: number; ts: string }
