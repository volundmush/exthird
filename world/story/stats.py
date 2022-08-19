from .base import BaseHandler, StatHandler
from world.story import ATTRIBUTES, ABILITIES, MA_STYLES
from world.story.exceptions import StoryDBException
from world.utils import dramatic_capitalize, partial_match


class AttributeHandler(StatHandler):
    base_path = ["Attributes"]

    def options(self) -> list[str]:
        return ATTRIBUTES

    def valid_value(self, name: str, value: int):
        value = super().valid_value(name, value)
        if value < 1:
            raise StoryDBException("Attributes cannot be below 1!")
        return value


class AbilityHandler(StatHandler):
    base_path = ["Abilities"]
    link_abil = {"Brawl": "Martial Arts",
                 "Martial Arts": "Brawl"}
    no_set = ("Craft", "Martial Arts")

    def options(self) -> list[str]:
        return ABILITIES

    def can_set(self, name: str, value: int):
        if name in self.no_set:
            raise StoryDBException(f"{name} cannot be set directly.")

    def favor(self, name: str, value: int):
        stat = self.find_stat(name)
        value = self.valid_value(stat, value)
        linked = self.link_abil.get(stat, None)
        if linked and value > 0:
            lnk_row = self.stat_row(self.base_path + [linked])
            if found := self.owner.story_stats.filter(stat=lnk_row).first():
                if found.stat_flag_1 > 0:
                    raise StoryDBException(f"{linked} is already picked!")
        row = self.stat_row(self.base_path + [stat])
        return self.set_flag_1(row, value=value)


class StyleHandler(StatHandler):
    base_path = ["Styles"]

    def options(self) -> list[str]:
        return MA_STYLES


class CraftHandler(BaseHandler):
    base_path = ["Crafts"]

    def set(self, name: str, value: int, creator):
        stat = self.good_name(name, name_for="Craft")
        value = self.valid_value(stat, value)
        row = self.stat_row(self.base_path + [stat], creator=creator)
        if value:
            return self.set_int(row, value)
        else:
            found = self.owner.story_stats.filter(stat=row).first()
            if found:
                found.delete()
            if not row.users.count():
                row.delete()
            return found
