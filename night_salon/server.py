import asyncio
import websockets
import json
from typing import Set, Optional
from night_salon.game_state import GameState
from night_salon.handlers import MessageHandler


class Server:
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.game_state = GameState()
        self.message_handler = MessageHandler(self)
        self._running = False

    def get_client_by_id(
        self, player_id: str
    ) -> Optional[websockets.WebSocketServerProtocol]:
        """Get client websocket by player ID."""
        for client in self.clients:
            if hasattr(client, "player_id") and client.player_id == player_id:
                return client
        return None

    async def register(self, websocket: websockets.WebSocketServerProtocol) -> str:
        """Register a new client connection."""
        self.clients.add(websocket)
        player_id = str(len(self.clients))
        # Attach player_id to websocket for reference
        websocket.player_id = player_id
        return player_id

    async def unregister(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Unregister a client connection."""
        if hasattr(websocket, "player_id"):
            self.game_state.remove_player(websocket.player_id)
        self.clients.remove(websocket)

    async def handler(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ) -> None:
        """Handle individual WebSocket connections."""
        player_id = await self.register(websocket)
        try:
            # Initial game state sent to new player
            await websocket.send(
                {
                    "type": "connection_established",
                    "player_id": player_id,
                    "data": self.game_state.to_dict(),
                }
            )

            async for message in websocket:
                await self.message_handler.dispatch(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def game_loop(self) -> None:
        """Main game loop running at 60 FPS."""
        while self._running:
            # Update global state
            self.game_state.global_state["game_time"] = (
                self.game_state.global_state.get("game_time", 0) + 1
            )

            # Broadcast game tick to all clients
            if self.clients:
                message = {
                    "type": "game_tick",
                    "data": {"game_time": self.game_state.global_state["game_time"]},
                }
                await self.message_handler.broadcast("game_tick", message)

            await asyncio.sleep(1 / 60)  # 60 FPS

    async def start(self, host: str, port: int) -> None:
        """Start the game server."""
        self._running = True
        self.server = await websockets.serve(self.handler, host, port)
        await asyncio.gather(self.server.serve_forever(), self.game_loop())

    async def stop(self) -> None:
        """Stop the game server."""
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # Close all client connections
        for client in self.clients:
            await client.close()
        self.clients.clear()
