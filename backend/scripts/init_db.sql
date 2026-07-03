-- Local planar coordinate system (SRID 0): coordinates are camera-frame
-- pixel space (origin top-left, x right, y down), matching the source
-- video resolution. Re-project to a real CRS later if georeferencing the
-- camera view (e.g. via homography) becomes necessary.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS zones (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    geom GEOMETRY(POLYGON, 0) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lines (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    geom GEOMETRY(LINESTRING, 0) NOT NULL,
    -- which side of the line (by sign of the cross product against the
    -- line's direction vector) counts as "in"
    in_direction TEXT NOT NULL DEFAULT 'left' CHECK (in_direction IN ('left', 'right')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS track_positions (
    id BIGSERIAL PRIMARY KEY,
    track_id INTEGER NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT now(),
    geom GEOMETRY(POINT, 0) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_track_positions_geom ON track_positions USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_track_positions_ts ON track_positions (ts);

CREATE TABLE IF NOT EXISTS crossing_events (
    id BIGSERIAL PRIMARY KEY,
    line_id INTEGER NOT NULL REFERENCES lines(id) ON DELETE CASCADE,
    track_id INTEGER NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('in', 'out')),
    ts TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_crossing_events_line_ts ON crossing_events (line_id, ts);

CREATE TABLE IF NOT EXISTS zone_occupancy_events (
    id BIGSERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    track_id INTEGER NOT NULL,
    enter_ts TIMESTAMPTZ NOT NULL,
    exit_ts TIMESTAMPTZ,
    dwell_seconds DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_zone_occupancy_zone ON zone_occupancy_events (zone_id, exit_ts);
