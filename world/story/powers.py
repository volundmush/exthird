from world.story.models import StorytellerStat, CharacterStat
from world.utils import partial_match, dramatic_capitalize
from evennia.utils.utils import lazy_property
from world.story.exceptions import StoryDBException
from world.story.stats import BaseHandler
from collections import defaultdict


ATTRIBUTES = ["Strength", "Dexterity", "Stamina", "Charisma", "Manipulation", "Appearance", "Perception",
              "Intelligence", "Wits"]

ATTRIBUTES_PSM = {
    "physical": ["Strength", "Dexterity", "Stamina"],
    "social": ["Charisma", "Manipulation", "Appearance"],
    "mental": ["Perception", "Intelligence", "Wits"]
}

ABILITIES = ["Archery", "Athletics", "Awareness", "Brawl", "Bureaucracy", "Craft", "Dodge", "Integrity",
             "Investigation", "Larceny", "Linguistics", "Lore", "Martial Arts", "Medicine", "Melee", "Occult",
             "Performance", "Presence", "Resistance", "Ride", "Sail", "Socialize", "Stealth", "Survival", "Thrown",
             "War"]

MA_STYLES = ["Snake", "Tiger", "Single Point Shining Into the Void", "White Reaper", "Ebon Shadow", "Crane",
             "Silver-Voiced Nightingale", "Righteous Devil", "Black Claw", "Steel Devil", "Dreaming Pearl Courtesan",
             "Air Dragon", "Earth Dragon", "Fire Dragon", "Water Dragon", "Wood Dragon", "Golden Janissary", "Mantis",
             "White Veil", "Centipede", "Falcon", "Laughing Monster", "Swaying Grass Dance"]

ESSENCE_CHARMS = ["Essence"]

EXIGENT_CHARMS = ATTRIBUTES + ABILITIES + ESSENCE_CHARMS

CHARM_CATEGORIES = {
    "Solar": ABILITIES,
    "Abyssal": ABILITIES,
    "Lunar": ATTRIBUTES + ["Universal"],
    "Dragon-Blooded": ABILITIES,
    "Martial Arts": MA_STYLES,
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

    def set(self, sub_category: str, name: str, value: int = 1, main_category: str = None):
        main_category = self.get_main_category(main_category)
        if not (categories := self.root.get(main_category, None)):
            raise StoryDBException(f"No {self.stat_type} Categories available for {main_category}.")
        if not sub_category:
            raise StoryDBException(f"No Sub-category entered!")
        if not (sub_category := partial_match(sub_category, categories)):
            raise StoryDBException(f"Entered Sub-Category does not match any {self.stat_type} Categories!")
        name = self.good_name(name)
        value = self.valid_value(value)
        path = self.make_path([self.base, main_category, sub_category, name])
        stat = self.get_stat(path)
        row, created = self.owner.story_stats.get_or_create(stat=stat)
        row.stat_value = value
        row.save()
        return row

    def all(self):
        return self.owner.story_stats.filter(stat__name_1=self.base).exclude(stat__name_4='').order_by("stat__name_4")

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
