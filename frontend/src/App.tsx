import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api/client'
import { LiveStatsPanel } from './components/LiveStatsPanel'
import { MapView } from './components/MapView'
import { useLiveEvents } from './hooks/useWebSocket'
import type { CrossingStats, Line, LiveEvent, LivePosition, XY, Zone, ZoneStats } from './types'

const HEAT_WINDOW = 800
const STATS_RESYNC_INTERVAL_MS = 15000
const STALE_TRACK_MS = 5000

export default function App() {
  const [zones, setZones] = useState<Zone[]>([])
  const [lines, setLines] = useState<Line[]>([])
  const [zoneStats, setZoneStats] = useState<ZoneStats[]>([])
  const [crossingStats, setCrossingStats] = useState<CrossingStats[]>([])
  const [livePositions, setLivePositions] = useState<Map<number, LivePosition>>(new Map())
  const [heatPoints, setHeatPoints] = useState<XY[]>([])
  const heatBuffer = useRef<XY[]>([])

  const refreshStats = useCallback(async () => {
    const [zs, cs] = await Promise.all([api.zoneStats(), api.crossingStats()])
    setZoneStats(zs)
    setCrossingStats(cs)
  }, [])

  useEffect(() => {
    api.zones().then(setZones)
    api.lines().then(setLines)
    refreshStats()
    // WebSocket events update counts optimistically in real time; this
    // periodic resync corrects any drift (e.g. after a dropped connection)
    const interval = setInterval(refreshStats, STATS_RESYNC_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [refreshStats])

  useEffect(() => {
    // live markers have no explicit "track lost" event, so prune anything
    // that hasn't reported a position recently
    const interval = setInterval(() => {
      setLivePositions((prev) => {
        const now = Date.now()
        const next = new Map<number, LivePosition>()
        prev.forEach((pos, id) => {
          if (now - new Date(pos.ts).getTime() < STALE_TRACK_MS) next.set(id, pos)
        })
        return next
      })
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleEvent = useCallback((event: LiveEvent) => {
    if (event.type === 'position') {
      setLivePositions((prev) => {
        const next = new Map(prev)
        next.set(event.track_id, event)
        return next
      })
      heatBuffer.current = [...heatBuffer.current, [event.x, event.y] as XY].slice(-HEAT_WINDOW)
      setHeatPoints(heatBuffer.current)
    } else if (event.type === 'crossing') {
      setCrossingStats((prev) =>
        prev.map((c) =>
          c.line_id === event.line_id
            ? {
                ...c,
                in_count: c.in_count + (event.direction === 'in' ? 1 : 0),
                out_count: c.out_count + (event.direction === 'out' ? 1 : 0),
              }
            : c,
        ),
      )
    } else if (event.type === 'zone_enter') {
      setZoneStats((prev) =>
        prev.map((z) =>
          z.zone_id === event.zone_id ? { ...z, current_occupancy: z.current_occupancy + 1 } : z,
        ),
      )
    } else if (event.type === 'zone_exit') {
      setZoneStats((prev) =>
        prev.map((z) =>
          z.zone_id === event.zone_id
            ? { ...z, current_occupancy: Math.max(0, z.current_occupancy - 1) }
            : z,
        ),
      )
    }
  }, [])

  const { connected } = useLiveEvents(handleEvent)

  return (
    <div className="app">
      <header className="app-header">
        <h1>人流分析 Dashboard</h1>
        <span className={`status ${connected ? 'online' : 'offline'}`}>
          {connected ? '即時連線中' : '連線中斷，重試中...'}
        </span>
      </header>
      <main className="app-body">
        <div className="map-panel">
          <MapView zones={zones} lines={lines} livePositions={livePositions} heatPoints={heatPoints} />
        </div>
        <LiveStatsPanel zoneStats={zoneStats} crossingStats={crossingStats} />
      </main>
    </div>
  )
}
