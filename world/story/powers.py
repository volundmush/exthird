from world.story.models import Stat, CharacterStat, Power, CharacterPower, Merit, CharacterMerit
from world.utils import partial_match, dramatic_capitalize
from evennia.utils.utils import lazy_property
from world.story.exceptions import StoryDBException
from world.story.stats import BaseHandler, ATTRIBUTES, ABILITIES, STYLES
from collections import defaultdict

ESSENCE_CHARMS = ["Essence"]

EXIGENT_CHARMS = ATTRIBUTES + ABILITIES + ESSENCE_CHARMS

CHARM_CATEGORIES = {
    "Solar": ABILITIES,
    "Abyssal": ABILITIES,
    "Lunar": ATTRIBUTES + ["Universal"],
    "Dragon-Blooded": ABILITIES,
    "Martial Arts": STYLES,
    "Sidereal": ABILITIES,
    "Liminal": ATTRIBUTES,
    "Getimian": ATTRIBUTES,
    "Celestial Exigent": EXIGENT_CHARMS,
    "Terrestrial Exigent": EXIGENT_CHARMS,
    "Spirit": ["Universal", "Blessings", "Divinations", "Sendings", "Divine Works", "Eidola", "Relocations",
               "Enchantments", "Inhabitings", "Tantra", "Aegis", "Curses", "Edges"],
    "Dream-Souled": ["Illusion and Transformation", "Offensive", "Defensive", "Social", "Mobility and Travel"],
    "Hearteater": ["Pawn", "Offensive", "Defensive", "Social", "Mobility and Travel", "Mysticism"],
    "Umbral": ["Penumbra", "Darkness", "Offensive", "Defensive", "Social", "Mobility and Travel"]
}

SPELL_CATEGORIES = {
    "Sorcery": ["Terrestrial", "Celestial", "Solar"],
    "Necromancy": ["Ivory", "Shadow", "Void"]
}


class PowerNameHandler(BaseHandler):
    stat_type = 'PowerName'
    custom = True
    root = dict()
    base = None

    def default_category(self):
        return ""

    def get_main_category(self, category: str = None):
        if category is None:
            category = self.default_category()
        else:
            category = partial_match(category, self.root.keys())
        if not category:
            raise StoryDBException(f"No valid Main Category of {self.stat_type} selected!")
        return category

    def get_sub_category(self, main_category: str, name: str):
        if not (categories := self.root.get(main_category, None)):
            raise StoryDBException(f"No {self.stat_type} Categories available for {main_category}.")
        if not name:
            raise StoryDBException(f"No Sub-category entered!")
        if not (sub_category := partial_match(name, categories)):
            raise StoryDBException(f"Entered Sub-Category does not match any {self.stat_type} Categories!")
        return sub_category

    def get_power(self, main_category: str, sub_category: str, name: str):
        power, created = Power.objects.get_or_create(root=self.base, category=main_category, sub_category=sub_category,
                                                     name=name)
        if created:
            power.creator = self.owner
            power.save()
        return power

    def set(self, sub_category: str, name: str, value: int = 1, main_category: str = None):
        main_category = self.get_main_category(main_category)
        sub_category = self.get_sub_category(main_category, sub_category)
        name = self.good_name(name)
        value = self.valid_value(value)
        power = self.get_power(main_category, sub_category, name)
        row, created = self.owner.db_powers.get_or_create(power=power)
        row.stat_value = value
        row.save()
        return row

    def all(self):
        return self.owner.db_powers.filter(power__root=self.base).order_by(["power__category", "power__sub_category", "power__name"])

    def all_main(self):
        out = defaultdict(lambda: defaultdict(list))
        for x in self.all():
            out[x.stat.name_2][x.stat.name_3].append(x)
        return out


class CharmHandler(PowerNameHandler):
    stat_type = "Charm"
    root = CHARM_CATEGORIES
    base = "Charms"

    def default_category(self):
        return self.owner.story_template.template.native_charm_category()


class SpellHandler(PowerNameHandler):
    stat_type = "Spell"
    root = SPELL_CATEGORIES
    base = "Spells"

    def default_category(self):
        return "Sorcery"


class EvocationHandler(PowerNameHandler):
    stat_type = "Evocation"
    base = "Evocations"

    def get_main_category(self, category: str = None):
        return "Evocations"

    def get_sub_category(self, main_category: str, name: str):
        return self.good_name(name)


class MeritHandler(BaseHandler):
    root = ["General", "Artifact", "Language", "Shaping Ritual", "Mutation", "Familiar", "Social"]
    base = 'Merits'

    def default_category(self):
        return "General"

    def get_main_category(self, category: str = None):
        if category is None:
            category = self.default_category()
        else:
            category = partial_match(category, self.root)
        if not category:
            raise StoryDBException(f"No valid Main Category of {self.stat_type} selected!")
        return category

    def get_merit(self, main_category: str, name: str):
        power, created = Merit.objects.get_or_create(root=self.base, category=main_category, name=name)
        if created:
            power.creator = self.owner
            power.save()
        return power

    def set(self, name: str, value: int = 1, main_category: str = None):
        main_category = self.get_main_category(main_category)
        name = self.good_name(name)
        value = self.valid_value(value)
        merit = self.get_merit(main_category, name)
        row, created = self.owner.db_merits.get_or_create(merit=merit)
        row.stat_value = value
        row.save()
        return row

    def all(self):
        return self.owner.db_merits.all().order_by(["merit__category", "merit__name"])

    def all_main(self):
        out = defaultdict(list)
        for x in self.all():
            out[x.stat.name_2].append(x)
        return out