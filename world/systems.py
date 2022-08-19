from django.conf import settings
from world.utils import utcnow
from twisted.internet import reactor, task
import time


def sleep_for(delay):
    return task.deferLater(reactor, delay, lambda: None)


class System:
    name = "system"
    interval = 0.0

    def __init__(self):
        self.looper = None
        self.task = None

    def at_init(self):
        pass

    def at_start(self):
        pass

    async def update(self):
        pass

    async def run(self):
        if not self.interval > 0:
            return
        while True:
            start = time.monotonic()
            await self.update()
            after = time.monotonic()
            diff = after - start
            remaining = self.interval - diff
            if remaining > 0:
                await sleep_for(remaining)

    def at_stop(self):
        if self.task:
            self.task.cancel()

    def at_reload_start(self):
        pass

    def at_reload_stop(self):
        pass

    def at_cold_start(self):
        pass

    def at_cold_stop(self):
        pass


class PlaySystem(System):
    name = "play"
    interval = 1.0

    def __init__(self):
        super().__init__()
        from world.plays.plays import DefaultPlay
        self.play = DefaultPlay

    async def update(self):
        for play in self.play.objects.all():
            play.last_good = utcnow()
            if not play.sessions.count():
                play.timeout_seconds = play.timeout_seconds + self.interval
                if play.timeout_seconds >= settings.PLAY_TIMEOUT_SECONDS:
                    play.at_timeout()

    def at_cold_start(self):
        for play in self.play.objects.all():
            play.at_server_cold_start()

    def at_cold_stop(self):
        for play in self.play.objects.all():
            play.at_server_cold_stop()
