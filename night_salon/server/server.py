from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from night_salon.controllers.environment import EnvironmentController
from night_salon.server.event_handler import EventHandler
from night_salon.utils.logger import logger
import json

app = FastAPI()
env_controller = EnvironmentController()  # Shared environment instance

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
    print("New client connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                event_type = event.get("type")
                event_data = event.get("data", {})
                
                logger.debug(f"Received event: {event_type}")
                await EventHandler.handle_event(event_type, event_data, env_controller)
                await websocket.send_json({"status": "success"})
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
                await websocket.send_json({"status": "error", "message": "Invalid JSON format"})
                
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}", exc_info=True)
                await websocket.send_json({"status": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Connection error: {str(e)}", exc_info=True)
        await websocket.close(code=1011)




