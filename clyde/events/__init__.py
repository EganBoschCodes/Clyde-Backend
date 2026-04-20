from .event_directory import ColorWipe, Doorbell, MiniParty, Notify, Sunrise
from .types import Event, EventContext

EVENTS: dict[str, type[Event]] = {
    ColorWipe.NAME: ColorWipe,
    Doorbell.NAME: Doorbell,
    MiniParty.NAME: MiniParty,
    Notify.NAME: Notify,
    Sunrise.NAME: Sunrise,
}
