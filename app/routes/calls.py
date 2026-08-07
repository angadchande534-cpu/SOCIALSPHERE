import asyncio
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import SessionLocal
from app.models import User
from app.security import decode_access_token

router = APIRouter(tags=["Calls"])
connections: dict[int, set[WebSocket]] = defaultdict(set)
lock = asyncio.Lock()

async def send_to(user_id: int, payload: dict):
    dead = []
    for ws in list(connections.get(user_id, set())):
        try: await ws.send_json(payload)
        except Exception: dead.append(ws)
    for ws in dead: connections[user_id].discard(ws)

@router.websocket("/ws/calls")
async def call_socket(websocket: WebSocket, token: str):
    try: user_id = decode_access_token(token)
    except ValueError:
        await websocket.close(code=4401); return
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user:
            await websocket.close(code=4401); return
        await websocket.accept()
        async with lock: connections[user_id].add(websocket)
        await websocket.send_json({"type":"ready","user_id":user_id})
        while True:
            data = await websocket.receive_json()
            target = int(data.get("target_user_id") or 0)
            if not target: continue
            payload = {**data, "from_user_id": user_id, "from_username": user.username}
            await send_to(target, payload)
    except WebSocketDisconnect:
        pass
    finally:
        async with lock: connections[user_id].discard(websocket)
        db.close()
