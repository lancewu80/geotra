from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    manager = websocket.app.state.manager
    await manager.connect(websocket)
    try:
        while True:
            # clients don't send anything meaningful; just keep the socket open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
