import colorsys

from home_assistant_lib import RGB


def hex_to_rgb(hex_color: str) -> RGB:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hue_to_rgb(hue: float, saturation: float = 1.0, value: float = 1.0) -> RGB:
    r, g, b = colorsys.hsv_to_rgb(hue % 1.0, saturation, value)
    return int(r * 255), int(g * 255), int(b * 255)
