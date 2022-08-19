from world.story.exceptions import StoryDBException
from world.utils import dramatic_capitalize, partial_match
from world.story.models import StorytellerStat
import typing


class BaseHandler:

    def __init__(self, owner):
        self.owner = owner

    def process_path(self, path: list[str]) -> dict:
        names = dict()
        for i, n in enumerate(path):
            names[f"name_{i + 1}"] = dramatic_capitalize(n)
        return names

    def stat_row(self, path: list[str], creator=None):
        if len(path) > 4:
            raise StoryDBException(f"Database depth limit is 4, got {path}")
        names = self.process_path(path)
        if creator:
            names["creator"] = creator
        stat, created = StorytellerStat.objects.get_or_create(**names)
        if created:
            stat.save()
        return stat

    def good_name(self, in_name, name_for: str = "stat", max_length: int = 80) -> str:
        dc = dramatic_capitalize(in_name)
        if not dc:
            raise StoryDBException(f"Must enter a name for the {name_for}.")
        if len(dc) > max_length:
            raise StoryDBException(f"'{dc} is too long a name for a {name_for}.")
        return dc

    def set_base(self, stat_row, value: int = 1) -> ("cstat", int):
        if value < 0:
            raise StoryDBException(f"Must enter a whole number 0 or greater!")
        cstat, created = self.owner.story_stats.get_or_create(stat=stat_row)
        return cstat, value

    def set_int(self, stat_row, value: int = 1):
        cstat, value = self.set_base(stat_row, value=value)
        cstat.stat_value = value
        cstat.save()
        return cstat

    def set_flag_1(self, stat_row, value: int = 1):
        cstat, value = self.set_base(stat_row, value=value)
        cstat.stat_flag_1 = value
        cstat.save()
        return cstat

    def set_flag_2(self, stat_row, value: int = 1):
        cstat, value = self.set_base(stat_row, value=value)
        cstat.stat_flag_2 = value
        cstat.save()
        return cstat

    def valid_value(self, name: str, value: int):
        try:
            value = int(value)
        except ValueError as err:
            raise StoryDBException(f"Value for {name} must be a number!")
        return value


class StatHandler(BaseHandler):
    base_path = []

    def options(self) -> list[str]:
        return []

    def find_stat(self, name: str) -> str:
        if not name:
            raise StoryDBException("Must enter a stat name!")
        ops = self.options()
        if (found := partial_match(name, ops)):
            return found
        raise StoryDBException(f"Stat not found! Choices are: {ops}")

    def can_set(self, name: str, value: int):
        return True

    def set(self, name: str, value: int):
        stat = self.find_stat(name)
        value = self.valid_value(stat, value)
        if not self.can_set(stat, value):
            return
        row = self.stat_row(self.base_path + [stat])
        return self.set_int(row, value)

    def default_value(self, name: str):
        return 0

    def get_value(self, name: str) -> int:
        stat = self.find_stat(name)
        names = self.process_path(self.base_path + [stat])
        if not (stat_row := StorytellerStat.objects.filter(**names).first()):
            return self.default_value(stat)
        if not (found := self.owner.story_stats.filter(stat=stat_row).first()):
            return self.default_value(stat)
        return found.stat_value

