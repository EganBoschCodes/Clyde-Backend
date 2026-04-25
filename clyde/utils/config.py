from pathlib import Path

from pydantic import BaseModel, model_validator
from home_assistant_lib import Light, MediaPlayer


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


class Room(BaseModel):
    model_config = {"frozen": True}

    name: str
    lights: tuple[str, ...]


class ClydeConfig(BaseModel):
    model_config = {"frozen": True}

    lights: dict[str, Light]
    rooms: dict[str, Room]
    media_players: dict[str, MediaPlayer] = {}

    @model_validator(mode="after")
    def validate_room_lights(self) -> "ClydeConfig":
        seen: dict[str, str] = {}
        for room_key, room in self.rooms.items():
            for light_key in room.lights:
                if light_key not in self.lights:
                    raise ValueError(f"Room '{room_key}' references unknown light '{light_key}'")
                if light_key in seen:
                    raise ValueError(f"Light '{light_key}' is assigned to both '{seen[light_key]}' and '{room_key}'")
                seen[light_key] = room_key
        return self


def load_config() -> ClydeConfig:
    return ClydeConfig.model_validate_json(CONFIG_PATH.read_text())


CONFIG = load_config()
