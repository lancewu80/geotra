import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import lines, stats, ws, zones
from .config import settings
from .db import async_session_factory
from .detection.analyzer import FlowAnalyzer
from .detection.detector import VideoDetector
from .detection.loader import reload_analyzer
from .services.aggregator import event_consumer
from .services.broadcaster import ConnectionManager

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    manager = ConnectionManager()
    analyzer = FlowAnalyzer(zones=[], lines=[])

    async with async_session_factory() as session:
        await reload_analyzer(session, analyzer)

    app.state.manager = manager
    app.state.analyzer = analyzer

    detector = VideoDetector(analyzer, loop, queue)
    detector.start()
    consumer_task = asyncio.create_task(event_consumer(queue, manager))

    try:
        yield
    finally:
        detector.stop()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="People Flow Analysis", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(zones.router)
app.include_router(lines.router)
app.include_router(stats.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
