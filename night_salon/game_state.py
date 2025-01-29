from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import json
from datetime import datetime


@dataclass
class Vector3:
    x: float
    y: float
    z: float


@dataclass
class PlayerState:
    id: str
    name: str
    position: Vector3
    rotation: Vector3
    animation_state: str
    is_speaking: bool
    current_room: str
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["last_updated"] = self.last_updated.isoformat()
        return data


@dataclass
class RoomState:
    id: str
    name: str
    max_capacity: int
    current_players: List[str]  # List of player IDs
    ambient_sound: Optional[str]
    background_music: Optional[str]
    lighting_state: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GameState:
    def __init__(self):
        self.players: Dict[str, PlayerState] = {}
        self.rooms: Dict[str, RoomState] = {}
        self.global_state: Dict[str, Any] = {
            "time_of_day": "day",
            "weather": "clear",
            "server_time": datetime.now(),
            "active_events": [],
        }

        # Initialize default room
        self.init_default_room()

    def init_default_room(self) -> None:
        main_hall = RoomState(
            id="main_hall",
            name="Main Hall",
            max_capacity=50,
            current_players=[],
            ambient_sound="ambient_hall",
            background_music="lobby_theme",
            lighting_state={
                "intensity": 1.0,
                "color": {"r": 1.0, "g": 1.0, "b": 1.0},
                "shadows_enabled": True,
            },
        )
        self.rooms["main_hall"] = main_hall

    def add_player(self, player_id: str, name: str) -> PlayerState:
        player = PlayerState(
            id=player_id,
            name=name,
            position=Vector3(x=0.0, y=0.0, z=0.0),
            rotation=Vector3(x=0.0, y=0.0, z=0.0),
            animation_state="idle",
            is_speaking=False,
            current_room="main_hall",
            last_updated=datetime.now(),
        )
        self.players[player_id] = player
        self.rooms["main_hall"].current_players.append(player_id)
        return player

    def remove_player(self, player_id: str) -> None:
        if player_id in self.players:
            player = self.players[player_id]
            if player.current_room in self.rooms:
                self.rooms[player.current_room].current_players.remove(player_id)
            del self.players[player_id]

    def update_player_position(
        self, player_id: str, position: Vector3, rotation: Vector3
    ) -> None:
        if player_id in self.players:
            self.players[player_id].position = position
            self.players[player_id].rotation = rotation
            self.players[player_id].last_updated = datetime.now()

    def update_player_room(self, player_id: str, new_room_id: str) -> bool:
        if player_id in self.players and new_room_id in self.rooms:
            player = self.players[player_id]
            old_room = self.rooms[player.current_room]
            new_room = self.rooms[new_room_id]

            if len(new_room.current_players) < new_room.max_capacity:
                old_room.current_players.remove(player_id)
                new_room.current_players.append(player_id)
                player.current_room = new_room_id
                return True
        return False

    def set_player_speaking(self, player_id: str, is_speaking: bool) -> None:
        if player_id in self.players:
            self.players[player_id].is_speaking = is_speaking

    def add_room(self, room_id: str, name: str, max_capacity: int) -> RoomState:
        room = RoomState(
            id=room_id,
            name=name,
            max_capacity=max_capacity,
            current_players=[],
            ambient_sound=None,
            background_music=None,
            lighting_state={
                "intensity": 1.0,
                "color": {"r": 1.0, "g": 1.0, "b": 1.0},
                "shadows_enabled": True,
            },
        )
        self.rooms[room_id] = room
        return room

    def get_room_players(self, room_id: str) -> List[PlayerState]:
        if room_id in self.rooms:
            return [self.players[pid] for pid in self.rooms[room_id].current_players]
        return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "players": {pid: player.to_dict() for pid, player in self.players.items()},
            "rooms": {rid: room.to_dict() for rid, room in self.rooms.items()},
            "global_state": {
                **self.global_state,
                "server_time": self.global_state["server_time"].isoformat(),
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
