from pydantic import BaseModel, model_validator
from home_assistant_lib import Light, MediaPlayer


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


CONFIG = ClydeConfig(
    lights={
        "desk_lamp": Light(entity_id="light.desk_lamp"),
        "kitchen_island_1": Light(entity_id="light.kitchen_island_1"),
        "kitchen_island_2": Light(entity_id="light.kitchen_island_2"),
        "living_room_lamp_1": Light(entity_id="light.living_room_lamp_1"),
        "living_room_lamp_2": Light(entity_id="light.living_room_lamp_2"),
        "mackenzie_bedside_lamp": Light(entity_id="light.mackenzie_bedside_lamp"),
        "egan_bedside_lamp": Light(entity_id="light.egan_bedside_lamp"),
    },
    rooms={
        "office": Room(name="Office", lights=("desk_lamp",)),
        "kitchen_and_living_room": Room(
            name="Kitchen/Living Room",
            lights=(
                "kitchen_island_2",
                "kitchen_island_1",
                "living_room_lamp_1",
                "living_room_lamp_2",
            ),
        ),
        "bedroom": Room(
            name="Master Bedroom",
            lights=("mackenzie_bedside_lamp", "egan_bedside_lamp"),
        ),
    },
    media_players={
        "fire_tv": MediaPlayer(entity_id="media_player.fire_tv", adb_address="192.168.1.211:5555"),
    },
)
