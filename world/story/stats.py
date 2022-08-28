from evennia.utils.utils import lazy_property
from django.db.models import Max
from world.story.exceptions import StoryDBException
from world.utils import dramatic_capitalize, partial_match
from world.story.models import Stat, CharacterStat, CharacterSpecialty


class MetaStat(type):

    def __str__(cls):
        return getattr(cls, "name", cls.__name__)


class _Stat(metaclass=MetaStat):
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
                row.value = self.default_value
            row.save()
        return row

    def can_set(self):
        return True

    def can_favor(self) -> bool:
        return True

    def can_supernal(self) -> bool:
        return True

    def can_caste(self) -> bool:
        return True

    def can_specialize(self) -> bool:
        return False

    def is_favored(self, ignore_derived=False) -> bool:
        return self.model.flag_1 == 1

    def is_supernal(self, ignore_derived=False) -> bool:
        return self.model.flag_2 == 1

    def is_caste(self, ignore_derived=False) -> bool:
        return self.model.flag_1 == 2

    def true_value(self):
        return self.model.value

    def calculated_value(self):
        return self.true_value()

    def set_value(self, value: int):
        self.model.value = value
        self.model.save(update_fields=["value"])

    def valid_value(self, value: int):
        try:
            value = int(value)
        except ValueError as err:
            raise StoryDBException(f"Value for {self} must be a number!")
        except TypeError as err:
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

    def should_display(self) -> bool:
        return self.calculated_value() or self.is_caste() or self.is_favored() or self.is_supernal()


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
        return self.calculated_value() or self.is_caste() or self.is_favored() or self.is_supernal()


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
        stats = self.handler.owner.db_stats.filter(stat__category=self.check_path)
        if stats.count():
            max_val = stats.aggregate(Max('value'))
            return max_val.get('value__max', 0)
        return self.default_value


class Craft(_DerivedAbility):
    check_path = 'Crafts'
    stat_type = 'Craft'


class MartialArts(_DerivedAbility):
    name = "Martial Arts"
    check_path = 'Styles'
    stat_type = 'Martial Arts Style'

    def can_favor(self) -> bool:
        return False

    def can_caste(self) -> bool:
        return False

    def is_favored(self, ignore_derived=False) -> bool:
        if ignore_derived:
            return super().is_favored(ignore_derived=ignore_derived)
        return self.handler.data["Brawl"].is_favored(ignore_derived=ignore_derived)

    def is_caste(self, ignore_derived=False) -> bool:
        if ignore_derived:
            return super().is_favored(ignore_derived=ignore_derived)
        return self.handler.data["Brawl"].is_caste(ignore_derived=ignore_derived)


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

    def find_stat(self, name: str) -> _Stat:
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
        except TypeError as err:
            raise StoryDBException(f"Value for {self.stat_type} must be a number!")
        return value

    def all(self):
        return sorted(list(self.data.values()), key=lambda x: str(x))


class StatHandler(BaseHandler):
    stat_classes = []
    stat_type = None
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
        return stat, value

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

    def get_caste_count(self):
        return 0

    def get_favor_count(self):
        return 0

    def get_supernal_count(self):
        return 0

    def get_caste(self):
        return []

    def set_favored(self, stat: str, value: bool = True, toggle: bool = False):
        if not isinstance(stat, _Stat):
            stat = self.find_stat(stat)
        if not stat.can_favor():
            raise StoryDBException(f"{stat} cannot be a Favored {self.stat_type}!")
        if toggle:
            value = not stat.is_favored(ignore_derived=True)
        if value:
            count = len([x for x in self.data.values() if x.is_favored(ignore_derived=True)])
            if count >= self.get_favor_count():
                raise StoryDBException(f"Cannot set another Favored {self.stat_type}!")
            if stat.is_favored(ignore_derived=True):
                raise StoryDBException(f"{stat} is already a Favored {self.stat_type}!")
            if stat.is_caste(ignore_derived=True):
                raise StoryDBException(f"{stat} has been picked as a {self.sub_name} {self.stat_type}!")
        else:
            if not stat.is_favored(ignore_derived=True):
                raise StoryDBException(f"{stat} is not a Favored {self.stat_type}!")
        stat.model.flag_1 = 1 if value else 0
        stat.model.save(update_fields=["flag_1"])
        return stat, value

    def set_caste(self, stat: str, value: bool = True, toggle: bool = False):
        if not isinstance(stat, _Stat):
            stat = self.find_stat(stat)
        if not stat.can_caste():
            raise StoryDBException(f"{stat} cannot be a {self.owner.sub_name} {self.stat_type}!")
        if str(stat) not in self.get_caste():
            raise StoryDBException(
                f"{stat} cannot be a {self.owner.sub_name} {self.stat_type}!")
        if toggle:
            value = not stat.is_caste(ignore_derived=True)
        if value:
            count = len([x for x in self.data.values() if x.is_caste(ignore_derived=True)])
            if count >= self.get_caste_count():
                raise StoryDBException(
                    f"Cannot set another {self.owner.sub_name} {self.stat_type}!")
            if stat.is_caste(ignore_derived=True):
                raise StoryDBException(f"{stat} is already a {self.owner.sub_name} {self.stat_type}!")
            if stat.is_favored(ignore_derived=True):
                raise StoryDBException(f"{stat} has been picked as a Favored {self.stat_type}!")
        else:
            if not stat.is_caste(ignore_derived=True):
                raise StoryDBException(f"{stat} is not a {self.owner.sub_name} {self.stat_type}!")
        stat.model.flag_1 = 2 if value else 0
        stat.model.save(update_fields=["flag_1"])
        return stat, value

    def set_supernal(self, stat: str, value: bool = True, toggle: bool = False):
        if not isinstance(stat, _Stat):
            stat = self.find_stat(stat)
        if not stat.can_supernal():
            raise StoryDBException(f"{stat} cannot be a {self.owner.supernal_name} {self.stat_type}!")
        if toggle:
            value = not stat.is_supernal(ignore_derived=True)
        if value:
            count = len([x for x in self.data.values() if x.is_supernal(ignore_derived=True)])
            if count >= self.get_supernal_count() and value:
                raise StoryDBException(
                    f"Cannot set another {self.owner.supernal_name} {self.stat_type}!")
            if not stat.is_caste():
                raise StoryDBException(
                    f"{stat} must first become a {self.owner.sub_name} {self.stat_type}!")
        else:
            if not stat.is_supernal(ignore_derived=True):
                raise StoryDBException(
                    f"{stat} is already a {self.owner.supernal_name} {self.stat_type}!")
        stat.model.flag_2 = 1 if value else 0
        stat.model.save(update_fields=["flag_2"])
        return stat, value

    def all_specialties(self):
        return CharacterSpecialty.objects.filter(stat__owner=self.owner, stat__stat__category=self.category).order_by(
            'stat__stat__category', 'stat__stat__name')

    def reset_sub(self):
        for stat in self.data.values():
            stat.model.flag_1 = 0
            stat.model.flag_2 = 0
            stat.model.save(update_fields=["flag_1", "flag_2"])


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
        return stat, stat.calculated_value()


class AttributeHandler(StatHandler):
    stat_classes = ATTRIBUTES
    category = "Attributes"
    stat_type = 'Attribute'

    def get_caste_count(self):
        return self.owner.caste_attributes

    def get_favor_count(self):
        return self.owner.favored_attributes

    def get_supernal_count(self):
        return self.owner.supernal_attributes

    def get_caste(self):
        return self.owner.sub_attributes


EXISTS = {str(x) for x in [ATTRIBUTES + ABILITIES + ADVANTAGES + STYLES]}


class AbilityHandler(StatHandler):
    category = "Abilities"
    stat_classes = ABILITIES
    stat_type = 'Ability'

    def get_caste_count(self):
        return self.owner.caste_abilities

    def get_favor_count(self):
        return self.owner.favored_abilities

    def get_supernal_count(self):
        return self.owner.supernal_abilities

    def get_caste(self):
        return self.owner.sub_abilities


class AdvantageHandler(StatHandler):
    category = 'Advantages'
    stat_classes = ADVANTAGES


class StyleHandler(StatHandler):
    category = "Styles"
    stat_classes = STYLES


class _Craft(_Stat):
    category = "Crafts"
    stat_type = 'Craft'

    def should_display(self) -> bool:
        return self.calculated_value()


class CraftHandler(CustomHandler):
    category = "Crafts"
    class_storage = dict()
    base_class = _Craft

