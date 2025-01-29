from typing import Dict, Any, Callable, Awaitable, TYPE_CHECKING
import json
import logging
from dataclasses import dataclass
import websockets
from night_salon.game_state import GameState, Vector3

if TYPE_CHECKING:
    from .server import GameServer

logger = logging.getLogger(__name__)


@dataclass
class ClientMessage:
    type: str
    data: Dict[str, Any]
    player_id: str


class MessageHandler:
    def __init__(self, game_server: "GameServer"):
        self.server = game_server
        self.handlers: Dict[str, Callable[[ClientMessage], Awaitable[None]]] = {
            "join": self.handle_join,
            "leave": self.handle_leave,
            "move": self.handle_move,
            "chat": self.handle_chat,
            "room_change": self.handle_room_change,
            "voice_state": self.handle_voice_state,
            "interaction": self.handle_interaction,
            "animation": self.handle_animation,
        }

    async def dispatch(
        self, websocket: websockets.WebSocketServerProtocol, message: str
    ) -> None:
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            player_id = data.get("player_id")

            if not msg_type or not player_id:
                await self.send_error(websocket, "Invalid message format")
                return

            client_message = ClientMessage(
                type=msg_type, data=data.get("data", {}), player_id=player_id
            )

            handler = self.handlers.get(msg_type)
            if handler:
                await handler(client_message)
            else:
                await self.send_error(websocket, f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(websocket, "Internal server error")

    async def broadcast(
        self, event_type: str, data: Dict[str, Any], exclude_player: str = None
    ) -> None:
        """Broadcast message to all connected clients, optionally excluding one player."""
        message = json.dumps({"type": event_type, "data": data})

        for client in self.server.clients:
            if exclude_player and client.player_id == exclude_player:
                continue
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                continue

    async def send_error(
        self, websocket: websockets.WebSocketServerProtocol, message: str
    ) -> None:
        """Send error message to a specific client."""
        await websocket.send(
            json.dumps({"type": "error", "data": {"message": message}})
        )

    # Handler Methods
    async def handle_join(self, message: ClientMessage) -> None:
        """Handle new player joining the game."""
        player_name = message.data.get("name", f"Player_{message.player_id}")
        self.server.game_state.add_player(message.player_id, player_name)

        await self.broadcast(
            "player_joined",
            {"player_id": message.player_id, "name": player_name},
            exclude_player=message.player_id,
        )

        # Send current game state to new player
        client = self.server.get_client_by_id(message.player_id)
        if client:
            await client.send(
                json.dumps(
                    {"type": "game_state", "data": self.server.game_state.to_dict()}
                )
            )

    async def handle_leave(self, message: ClientMessage) -> None:
        """Handle player leaving the game."""
        self.server.game_state.remove_player(message.player_id)
        await self.broadcast("player_left", {"player_id": message.player_id})

    async def handle_move(self, message: ClientMessage) -> None:
        """Handle player movement updates."""
        pos = message.data.get("position", {})
        rot = message.data.get("rotation", {})

        position = Vector3(
            x=float(pos.get("x", 0)), y=float(pos.get("y", 0)), z=float(pos.get("z", 0))
        )
        rotation = Vector3(
            x=float(rot.get("x", 0)), y=float(rot.get("y", 0)), z=float(rot.get("z", 0))
        )

        self.server.game_state.update_player_position(
            message.player_id, position, rotation
        )

        await self.broadcast(
            "player_moved",
            {"player_id": message.player_id, "position": pos, "rotation": rot},
            exclude_player=message.player_id,
        )

    async def handle_chat(self, message: ClientMessage) -> None:
        """Handle chat messages."""
        chat_message = message.data.get("message", "")
        room_id = self.server.game_state.players[message.player_id].current_room

        await self.broadcast(
            "chat",
            {"player_id": message.player_id, "message": chat_message, "room": room_id},
        )

    async def handle_room_change(self, message: ClientMessage) -> None:
        """Handle player changing rooms."""
        new_room = message.data.get("room_id")
        if new_room:
            success = self.server.game_state.update_player_room(
                message.player_id, new_room
            )
            if success:
                await self.broadcast(
                    "room_changed",
                    {"player_id": message.player_id, "room_id": new_room},
                )

    async def handle_voice_state(self, message: ClientMessage) -> None:
        """Handle voice chat state changes."""
        is_speaking = message.data.get("is_speaking", False)
        self.server.game_state.set_player_speaking(message.player_id, is_speaking)

        await self.broadcast(
            "voice_state_changed",
            {"player_id": message.player_id, "is_speaking": is_speaking},
            exclude_player=message.player_id,
        )

    async def handle_interaction(self, message: ClientMessage) -> None:
        """Handle player interactions with objects or other players."""
        interaction_type = message.data.get("interaction_type")
        target_id = message.data.get("target_id")

        await self.broadcast(
            "interaction",
            {
                "player_id": message.player_id,
                "interaction_type": interaction_type,
                "target_id": target_id,
            },
        )

    async def handle_animation(self, message: ClientMessage) -> None:
        """Handle animation state changes."""
        animation_state = message.data.get("state")
        if animation_state:
            if message.player_id in self.server.game_state.players:
                self.server.game_state.players[message.player_id].animation_state = (
                    animation_state
                )

                await self.broadcast(
                    "animation_changed",
                    {"player_id": message.player_id, "state": animation_state},
                    exclude_player=message.player_id,
                )
