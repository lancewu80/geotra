import type { CrossingStats, ZoneStats } from '../types'

interface Props {
  zoneStats: ZoneStats[]
  crossingStats: CrossingStats[]
}

export function LiveStatsPanel({ zoneStats, crossingStats }: Props) {
  return (
    <aside className="stats-panel">
      <section>
        <h2>進出計數</h2>
        {crossingStats.length === 0 && <p className="empty">尚未設定計數線</p>}
        <ul>
          {crossingStats.map((c) => (
            <li key={c.line_id}>
              <strong>{c.line_name}</strong>
              <span className="in">進 {c.in_count}</span>
              <span className="out">出 {c.out_count}</span>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>區域即時人數</h2>
        {zoneStats.length === 0 && <p className="empty">尚未設定區域</p>}
        <ul>
          {zoneStats.map((z) => (
            <li key={z.zone_id}>
              <strong>{z.zone_name}</strong>
              <span>{z.current_occupancy} 人</span>
              <span className="dwell">
                平均停留 {z.avg_dwell_seconds ? `${z.avg_dwell_seconds.toFixed(1)}s` : '-'}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </aside>
  )
}
