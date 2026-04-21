from .event_directory import Alarm, ColorWipe, Doorbell, MiniParty, Notify
from .types import Event, EventContext

EVENTS: dict[str, type[Event]] = {
    Alarm.NAME: Alarm,
    ColorWipe.NAME: ColorWipe,
    Doorbell.NAME: Doorbell,
    MiniParty.NAME: MiniParty,
    Notify.NAME: Notify,
}
