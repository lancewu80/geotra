"""Seeds one demo zone and one demo counting line via the REST API so the
dashboard has something to render. Safe to run multiple times -- skips if
zones/lines already exist, so a one-click start script can call this on
every launch. Run after the backend is up:

    python scripts/seed_demo.py
"""

import json
import urllib.request

API_BASE = "http://localhost:8000"


def get(path: str) -> list:
    with urllib.request.urlopen(f"{API_BASE}{path}") as resp:
        return json.loads(resp.read().decode())


def post(path: str, payload: dict) -> None:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(path, resp.status, resp.read().decode())


if __name__ == "__main__":
    if get("/zones") or get("/lines"):
        print("zones/lines already exist, skipping demo seed")
    else:
        # matches FRAME_WIDTH=1280 / FRAME_HEIGHT=720 from .env.example
        post(
            "/zones",
            {"name": "入口區", "polygon": [[100, 100], [400, 100], [400, 400], [100, 400]]},
        )
        post(
            "/lines",
            {"name": "大門計數線", "coords": [[640, 0], [640, 720]], "in_direction": "left"},
        )
