import type { CrossingStats, Line, Zone, ZoneStats } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_BASE ?? 'ws://localhost:8000'

async function request<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const api = {
  zones: () => request<Zone[]>('/zones'),
  lines: () => request<Line[]>('/lines'),
  zoneStats: () => request<ZoneStats[]>('/stats/zones'),
  crossingStats: () => request<CrossingStats[]>('/stats/crossings'),
}

export const WS_URL = `${WS_BASE}/ws/live`
