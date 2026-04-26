import asyncio
from datetime import date, datetime

import clyde.utils as utils

from clyde.events import EVENTS
from clyde.managers import ENGINE
from clyde.state import STATE

from .types import ScheduledEvent


TICK_INTERVAL = 30.0


class Scheduler:
    def __init__(self) -> None:
        self.schedules: list[ScheduledEvent] = []
        self.last_fired: dict[tuple[str, str, str], date] = {}
        self.task: asyncio.Task[None] | None = None
        self.lock = asyncio.Lock()

    def is_running(self) -> bool:
        return self.task is not None and not self.task.done()

    async def start(self) -> utils.Result[None]:
        if self.is_running():
            return utils.ok(None)
        self.schedules = STATE.schedules()
        now = datetime.now()
        for sched in self.schedules:
            if not sched.runs_on(now.weekday()):
                continue
            if now.time() >= sched.time_of_day():
                self.last_fired[sched.key()] = now.date()
        self.task = asyncio.create_task(self.run_loop())
        return utils.ok(None)

    async def stop(self) -> None:
        if self.task is None:
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        self.task = None

    def list(self) -> list[ScheduledEvent]:
        return list(self.schedules)

    async def add(self, sched: ScheduledEvent) -> utils.Result[ScheduledEvent]:
        if sched.event not in EVENTS:
            return utils.err(KeyError(f"Unknown event '{sched.event}'"))
        if sched.room not in utils.CONFIG.rooms:
            return utils.err(KeyError(f"Unknown room '{sched.room}'"))
        async with self.lock:
            if any(s.key() == sched.key() for s in self.schedules):
                return utils.err(ValueError(f"Schedule already exists for {sched.key()}"))
            next_schedules = [*self.schedules, sched]
            _, error = STATE.set_schedules(next_schedules)
            if error:
                return utils.err(error, "persist schedules")
            self.schedules = next_schedules
            now = datetime.now()
            if sched.runs_on(now.weekday()) and now.time() >= sched.time_of_day():
                self.last_fired[sched.key()] = now.date()
        return utils.ok(sched)

    async def remove(self, sched_key: tuple[str, str, str]) -> utils.Result[ScheduledEvent]:
        async with self.lock:
            match = next((s for s in self.schedules if s.key() == sched_key), None)
            if match is None:
                return utils.err(KeyError(f"No schedule for {sched_key}"))
            next_schedules = [s for s in self.schedules if s.key() != sched_key]
            _, error = STATE.set_schedules(next_schedules)
            if error:
                return utils.err(error, "persist schedules")
            self.schedules = next_schedules
            self.last_fired.pop(sched_key, None)
        return utils.ok(match)

    async def run_loop(self) -> None:
        while True:
            now = datetime.now()
            for sched in list(self.schedules):
                if self.last_fired.get(sched.key()) == now.date():
                    continue
                if not sched.runs_on(now.weekday()):
                    continue
                if now.time() < sched.time_of_day():
                    continue
                await self.fire(sched)
                self.last_fired[sched.key()] = now.date()
            await asyncio.sleep(TICK_INTERVAL)

    async def fire(self, sched: ScheduledEvent) -> None:
        event_cls = EVENTS.get(sched.event)
        if event_cls is None:
            print(f"[scheduler] unknown event '{sched.event}' in schedule for room '{sched.room}'")
            return
        _, error = await ENGINE.fire_event(sched.room, event_cls())
        if error:
            print(f"[scheduler] fire '{sched.event}' in '{sched.room}' failed: {error}")


SCHEDULER = Scheduler()
