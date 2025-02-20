from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Basic echo implementation
            await websocket.send_text(f"Server received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected normally")
    except Exception as e:
        print(f"WebSocket error: {e}")
        # Attempt to close only if connection is still active
        try:
            await websocket.close(code=1001)  # 1001 = Going Away
        except Exception as close_error:
            print(f"Error closing connection: {close_error}")




