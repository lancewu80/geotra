from fastapi import Request

from .detection.analyzer import FlowAnalyzer
from .services.broadcaster import ConnectionManager


def get_manager(request: Request) -> ConnectionManager:
    return request.app.state.manager


def get_analyzer(request: Request) -> FlowAnalyzer:
    return request.app.state.analyzer
