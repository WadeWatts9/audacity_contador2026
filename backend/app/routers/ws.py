import json
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

router = APIRouter()

class ConnectionManager:
    """
    Administrador de conexiones WebSocket aisladas por código de partida (sala).
    """
    def __init__(self):
        # game_code -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_code: str):
        await websocket.accept()
        if game_code not in self.active_connections:
            self.active_connections[game_code] = []
        self.active_connections[game_code].append(websocket)

    def disconnect(self, websocket: WebSocket, game_code: str):
        if game_code in self.active_connections:
            if websocket in self.active_connections[game_code]:
                self.active_connections[game_code].remove(websocket)
            if not self.active_connections[game_code]:
                del self.active_connections[game_code]

    async def broadcast(self, game_code: str, event_type: str, data: Any):
        if game_code in self.active_connections:
            payload = json.dumps({
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
            dead_sockets = []
            for connection in self.active_connections[game_code]:
                try:
                    await connection.send_text(payload)
                except Exception:
                    dead_sockets.append(connection)
            for dead in dead_sockets:
                self.disconnect(dead, game_code)

manager = ConnectionManager()

@router.websocket("/ws/{game_code}")
async def websocket_endpoint(websocket: WebSocket, game_code: str):
    await manager.connect(websocket, game_code)
    try:
        while True:
            # Mantener conexión viva y responder a pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_code)
    except Exception:
        manager.disconnect(websocket, game_code)
