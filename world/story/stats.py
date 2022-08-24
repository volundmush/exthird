from evennia.utils.utils import lazy_property
from django.db.models import Max
from world.story.exceptions import StoryDBException
from world.utils import dramatic_capitalize, partial_match
from world.story.models import Stat, CharacterStat, CharacterSpecialty


class _Stat:
    category = None
    min_value = 0
    max_value = 50
    default_value = 0
    stat_type = "Stat"

    def __init__(self, handler):
        self.handler = handler

    def __str__(self):
        return getattr(self, "name", self.__class__.__name__)

    @lazy_property
    def stat(self):
        stat, created = Stat.objects.get_or_create(category=self.category, name=str(self))
        if created:
            if self.handler.custom:
                stat.creator = self.handler.owner
            stat.save()
        return stat

    @lazy_property
    def model(self):
        row, created = self.handler.owner.db_stats.get_or_create(stat=self.stat)
        if created:
            if self.default_value is not None:
                row.stat_value = self.default_value
            row.save()
        return row

    def can_set(self):
        return True

    def can_favor(self) -> bool:
        return True

    def can_supernal(self) -> bool:
        return True

    def can_specialize(self) -> bool:
        return False

    def is_favored(self) -> bool:
        return self.model.stat_flag_1 == 1

    def is_supernal(self) -> bool:
        return self.model.stat_flag_2 == 2

    def is_caste(self) -> bool:
        return self.model.stat_flag_2 == 1

    def calculated_value(self):
        return self.model.stat_value

    def set_value(self, value: int):
        self.model.stat_value = value
        self.model.save(update_fields=["stat_value"])

    def valid_value(self, value: int):
        try:
            value = int(value)
        except ValueError as err:
            raise StoryDBException(f"Value for {self} must be a number!")
        return value

    def should_partial_roll(self) -> bool:
        return True

    def should_display(self) -> bool:
        return True


class _Attribute(_Stat):
    category = "Attributes"
    min_value = 1
    default_value = 1


ATTRIBUTES = []

for x in ["Strength", "Dexterity", "Stamina", "Charisma", "Manipulation", "Appearance", "Perception",
          "Intelligence", "Wits"]:
    attr = type(x, (_Attribute,), dict())
    ATTRIBUTES.append(attr)


class _Ability(_Stat):
    category = "Abilities"
    stat_type = 'Ability'

    def can_specialize(self) -> bool:
        return True

    def should_display(self) -> bool:
        return self.calculated_value() or self.is_favored() or self.is_supernal()


ABILITIES = []

for x in ["Archery", "Athletics", "Awareness", "Brawl", "Bureaucracy", "Dodge", "Integrity",
          "Investigation", "Larceny", "Linguistics", "Lore", "Medicine", "Melee", "Occult",
          "Performance", "Presence", "Resistance", "Ride", "Sail", "Socialize", "Stealth", "Survival", "Thrown",
          "War"]:
    abil = type(x, (_Ability,), dict())
    ABILITIES.append(abil)


class _DerivedAbility(_Ability):
    check_path = None

    def can_set(self):
        return False

    def calculated_value(self):
        max_val = self.handler.owner.db_stats.filter(stat__category=self.check_path).aggregate(Max('value'))
        return max_val.get('value__max', 0)


class Craft(_DerivedAbility):
    check_path = 'Crafts'
    stat_type = 'Craft'


class MartialArts(_DerivedAbility):
    name = "Martial Arts"
    check_path = 'Styles'
    stat_type = 'Martial Arts Style'


ABILITIES.extend([Craft, MartialArts])


class _Style(_Stat):
    stat_type = 'Style'
    category = 'Styles'

    def should_display(self) -> bool:
        return self.calculated_value()


STYLES = []

for x in ["Snake", "Tiger", "Single Point Shining Into the Void", "White Reaper", "Ebon Shadow", "Crane",
          "Silver-Voiced Nightingale", "Righteous Devil", "Black Claw", "Steel Devil", "Dreaming Pearl Courtesan",
          "Air Dragon", "Earth Dragon", "Fire Dragon", "Water Dragon", "Wood Dragon", "Golden Janissary", "Mantis",
          "White Veil", "Centipede", "Falcon", "Laughing Monster", "Swaying Grass Dance"]:
    cname = "".join(x.split())
    sdict = dict()
    if cname != x:
        sdict["name"] = x
    style = type(cname, (_Style,), sdict)
    STYLES.append(style)


class _Advantage(_Stat):
    stat_type = 'Advantage'
    category = 'Advantages'


class Essence(_Advantage):
    min_value = 1
    default_value = 1


class Willpower(_Advantage):
    default_value = 5


ADVANTAGES = [Essence, Willpower]


class BaseHandler:
    stat_type = 'Stat'
    custom = False

    def __init__(self, owner):
        self.owner = owner
        self.data = dict()
        self.load()

    def load(self):
        pass

    def good_name(self, in_name, max_length: int = 80) -> str:
        dc = dramatic_capitalize(in_name)
        if not dc:
            raise StoryDBException(f"Must enter a name for the {self.stat_type}.")
        if len(dc) > max_length:
            raise StoryDBException(f"'{dc} is too long a name for a {self.stat_type}.")
        if dc in EXISTS:
            raise StoryDBException(f"'{dc} conflicts with a basic Stat name!")
        return dc

    def options(self):
        return self.data.values()

    def find_stat(self, name: str) -> str:
        if not name:
            raise StoryDBException(f"Must enter a {self.stat_type} name!")
        ops = self.options()
        if (found := partial_match(name, ops)):
            return found
        raise StoryDBException(f"{self.stat_type} not found! Choices are: {ops}")

    def valid_value(self, value: int):
        try:
            value = int(value)
        except ValueError as err:
            raise StoryDBException(f"Value for {self.stat_type} must be a number!")
        return value

    def all(self):
        return sorted(list(self.data.values()), key=lambda x: str(x))


class StatHandler(BaseHandler):
    stat_classes = []
    category = None
    base = None

    def load(self):
        for x in self.stat_classes:
            stat = x(self)
            self.data[str(stat)] = stat

    def set(self, name: str, value: int):
        stat = self.find_stat(name)
        value = stat.valid_value(value)
        if not stat.can_set():
            raise StoryDBException(f"{stat} cannot be set directly.")
        stat.set_value(value)
        return stat

    def get_value(self, name: str) -> int:
        stat = self.find_stat(name)
        return stat.calculated_value()

    def set_special(self, name: str, specialty: str, value: int = 1):
        stat = self.find_stat(name)
        if not stat.can_specialize():
            raise StoryDBException(f"Cannot purchase specialties in {stat}!")
        value = self.valid_value(value)
        specialty = self.good_name(specialty)
        return stat.specialize(specialty, value=value)

    def all_specialties(self):
        return CharacterSpecialty.objects.filter(stat__owner=self.owner, stat__stat__category=self.category).order_by(
            ['stat__stat__category', 'stat__stat__name'])


class CustomHandler(BaseHandler):
    base_class = None
    class_storage = dict()
    custom = True

    def query(self):
        return []

    def load(self):
        for x in self.query():
            stat_class = self.get_or_create_stat_class(str(x))
            stat = stat_class(self)
            self.data[str(stat)] = stat

    def get_or_create_stat_class(self, name: str):
        if not (stat_class := self.class_storage.get(name, None)):
            cname = "".join(name.split())
            sdict = dict()
            if cname != name:
                sdict["name"] = name
            stat_class = type(cname, (self.base_class,), sdict)
            self.class_storage[name] = stat_class
        return stat_class

    def find_stat(self, name: str):
        name = self.good_name(name)
        if not (found := self.data.get(name, None)):
            stat_class = self.get_or_create_stat_class(name)
            found = stat_class(self)
            self.data[str(found)] = found
        return found

    def set(self, name: str, value: int):
        value = self.valid_value(value)
        stat = self.find_stat(name)
        stat.set_value(value)
        return stat


class AttributeHandler(StatHandler):
    stat_classes = ATTRIBUTES
    category = "Attributes"


EXISTS = {str(x) for x in [ATTRIBUTES + ABILITIES + ADVANTAGES + STYLES]}


class AbilityHandler(StatHandler):
    category = "Abilities"
    stat_classes = ABILITIES


class AdvantageHandler(StatHandler):
    category = 'Advantages'
    stat_classes = ADVANTAGES


class StyleHandler(StatHandler):
    category = "Styles"
    stat_classes = STYLES


class _Craft(_Stat):
    base_path = ["Crafts"]
    stat_type = 'Craft'

    def should_display(self) -> bool:
        return self.calculated_value()


class CraftHandler(CustomHandler):
    category = "Crafts"
    class_storage = dict()
    base_class = _Craft

