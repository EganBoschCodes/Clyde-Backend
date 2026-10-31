from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator


KEY_PREFIX = "studio_"
PREVIEW_KEY = "studio_preview"
MAX_COLORS = 8

type HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]
type RoutineStyle = Literal["drift", "flicker", "pulse", "chase", "static"]


class CustomRoutineSpec(BaseModel):
    model_config = {"frozen": True}

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    colors: Annotated[list[HexColor], Field(min_length=1, max_length=MAX_COLORS)]
    style: RoutineStyle
    speed: Annotated[float, Field(ge=0.0, le=1.0)]
    brightness: Annotated[int, Field(ge=1, le=255)]

    @field_validator("colors")
    @classmethod
    def normalize_colors(cls, colors: list[str]) -> list[str]:
        return [c.upper() for c in colors]
