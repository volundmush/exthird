from .exceptions import StoryDBException
from world.utils import partial_match
from world.story.models import CharacterTemplate


class Template:
    sub_types = []
    sub_name = "Caste"
    sheet_colors = {}
    start_advantages = {
        "Willpower": 5,
        "Essence": 1
    }
    sub_abilities = {}
    sub_attributes = {}
    extra_fields = {}
    default_sub = None
    supernal_name = None

    def caste_attributes_available(self) -> int:
        return 0

    def caste_abilities_available(self) -> int:
        return 0

    def favored_attributes_available(self) -> int:
        return 0

    def favored_abilities_available(self) -> int:
        return 0

    def supernal_attributes_available(self) -> int:
        return 0

    def supernal_abilities_available(self) -> int:
        return 0

    def set_sub(self, entry: str):
        if not entry:
            raise StoryDBException(f"Must enter a Template name!")
        if not (found := partial_match(entry, self.sub_types)):
            raise StoryDBException(f"No {self.sub_name} matches {entry}.")
        current_sub = self.handler.owner.story.sub_name
        self.handler.owner.story.sub_name = found
        self.handler.owner.story.save(update_fields=["sub_name"])

        if current_sub != found:
            self.reset_sub()

    def reset_sub(self):
        self.owner.story_attributes.reset_sub()
        self.owner.story_abilities.reset_sub()

    def pool_personal_max(self):
        pass

    def pool_peripheral_max(self):
        pass

    @classmethod
    def get_name(cls):
        return getattr(cls, "name", cls.__name__)

    def __str__(self):
        return getattr(self, "name", self.__class__.__name__)

    def __repr__(self):
        return '<Template: %s>' % str(self)

    def __init__(self, handler):
        self.handler = handler

    def initialize(self):
        pass

    def native_charm_category(self):
        return str(self)

    def get_advantage_value(self, name: str):
        return self.handler.owner.story_advantages.get_value(name)


class Mortal(Template):
    pass


class _Solaroid(Template):

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 3) + 10

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 7) + 26

    def favored_abilities_available(self) -> int:
        return 5

    def caste_abilities_available(self) -> int:
        return 5

    def supernal_abilities_available(self) -> int:
        return 1


_DAWN = ["Archery", "Awareness", "Brawl", "Dodge", "Melee", "Resistance", "Thrown", "War"]
_ZENITH = ["Athletics", "Integrity", "Performance", "Lore", "Presence", "Resistance", "Survival", "War"]
_TWILIGHT = ["Bureaucracy", "Craft", "Integrity", "Investigation", "Linguistics", "Lore", "Medicine", "Occult"]
_NIGHT = ["Athletics", "Awareness", "Dodge", "Investigation", "Larceny", "Ride", "Stealth", "Socialize"]
_ECLIPSE = ["Bureaucracy", "Larceny", "Linguistics", "Occult", "Presence", "Ride", "Sail", "Socialize"]


class Solar(_Solaroid):
    sub_types = ["Dawn", "Zenith", "Twilight", "Night", "Eclipse"]
    default_sub = "Dawn"
    sheet_colors = {"border": "bold yellow",
                    "stat_value": "bold green",
                    "stat_supernal": "bold yellow underline",
                    "stat_favored": "yellow",
                    "stat_caste": "bold yellow",
                    "stat_header": "bold red",
                    "power_subcategory": "bold yellow"
                    }
    sub_abilities = {
        "Dawn": _DAWN,
        "Zenith": _ZENITH,
        "Twilight": _TWILIGHT,
        "Night": _NIGHT,
        "Eclipse": _ECLIPSE
    }
    supernal_name = "Supernal"


class Abyssal(_Solaroid):
    sub_types = ["Dusk", "Midnight", "Daybreak", "Day", "Moonshadow"]
    default_sub = "Dusk"
    sheet_colors = {"border": "bold black",
                    "stat_value": "red",
                    "stat_supernal": "bold red underline",
                    "stat_favored": "red",
                    "stat_caste": "bold red",
                    "stat_header": "not bold magenta",
                    "power_subcategory": "bold black"
                    }
    sub_abilities = {
        "Dusk": _DAWN,
        "Midnight": _ZENITH,
        "Daybreak": _TWILIGHT,
        "Day": _NIGHT,
        "Moonshadow": _ECLIPSE
    }
    supernal_name = "Chthonic"


class Infernal(_Solaroid):
    sub_types = ["Azimuth", "Ascendant", "Horizon", "Nadir", "Penumbra"]
    default_sub = "Azimuth"
    sheet_colors = {"border": "bold green",
                    "stat_value": "not bold cyan",
                    "stat_supernal": "bold green underline",
                    "stat_favored": "green",
                    "stat_caste": "bold green",
                    "stat_header": "bold cyan",
                    "power_subcategory": "bold green"
                    }


class Lunar(Template):
    sub_types = ["Full Moon", "Changing Moon", "No Moon", "Casteless"]
    default_sub = "Casteless"
    sheet_colors = {"border": "bold cyan",
                    "stat_value": "bold green",
                    "stat_supernal": "bold cyan underline",
                    "stat_favored": "cyan",
                    "stat_caste": "bold cyan",
                    "stat_header": "bold blue",
                    "power_subcategory": "bold cyan"
                    }
    sub_attributes = {
        "Full Moon": ["Dexterity", "Stamina", "Strength"],
        "Changing Moon": ["Appearance", "Charisma", "Manipulation"],
        "No Moon": ["Intelligence", "Perception", "Wits"]
    }

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 1) + 15

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 34

    def favored_attributes_available(self) -> int:
        return 2

    def caste_attributes_available(self) -> int:
        if self.handler.owner.story.sub_name != "Casteless":
            return 2
        return 0


class Sidereal(Template):
    sub_types = ["Journeys", "Serenity", "Battles", "Secrets", "Endings"]
    sheet_colors = {"border": "bold magenta",
                    "stat_value": "bold green",
                    "stat_supernal": "bold magenta underline",
                    "stat_favored": "not bold magenta",
                    "stat_caste": "bold magenta",
                    "stat_header": "bold blue",
                    "power_subcategory": "bold magenta"
                    }

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 2) + 9

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 6) + 25


class DragonBlooded(Template):
    name = "Dragon-Blooded"
    sub_name = 'Aspect'
    sub_types = ["Air", "Earth", "Fire", "Water", "Wood"]
    default_sub = "Air"
    sheet_colors = {"border": "bold red",
                    "stat_value": "bold green",
                    "stat_supernal": "bold red underline",
                    "stat_favored": "not bold red",
                    "stat_caste": "bold red",
                    "stat_header": "bold cyan",
                    "power_subcategory": "not bold cyan"
                    }
    sub_abilities = {
        "Air": ["Linguistics", "Lore", "Occult", "Stealth", "Thrown"],
        "Earth": ["Awareness", "Craft", "Integrity", "Resistance", "War"],
        "Fire": ["Athletics", "Dodge", "Melee", "Presence", "Socialize"],
        "Water": ["Brawl", "Bureaucracy", "Investigation", "Larceny", "Sail"],
        "Wood": ["Archery", "Medicine", "Performance", "Ride", "Survival"]
    }

    def favored_abilities_available(self) -> int:
        return 5

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 1) + 11

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 23

    def reset_sub(self):
        super().reset_sub()
        for abil in self.sub_abilities.get(self.handler.owner.story.sub_name, list()):
            if (ab := self.handler.owner.story_abilities.data.get(abil, None)):
                ab.flag_1 = 2
                ab.save(update_fields=["flag_1"])


class Alchemical(Template):
    sub_types = ['Adamant', 'Jade', 'Moonsilver', 'Orichalcum', 'Starmetal', 'Soulsteel']


class Getimian(Template):
    sub_types = ["Spring", "Summer", "Autumn", "Winter"]


class Liminal(Template):
    sub_types = ["Blood", "Breath", "Flesh", "Marrow", "Soil"]

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 3) + 10

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 23


class _Celestial(Template):

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 2) + 11

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 6) + 27


class CelestialExigent(_Celestial):
    name = "Celestial Exigent"


class _Terrestrial(Template):

    def pool_personal_max(self):
        return self.get_advantage_value("Essence") + 11

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 23


class TerrestrialExigent(_Terrestrial):
    name = "Terrestrial Exigent"


class DreamSouled(_Terrestrial):
    name = "Dream-Souled"


class Hearteater(_Celestial):
    pass


class Umbral(_Celestial):
    pass


#TEMPLATES = [Mortal, Solar, Abyssal, Infernal, Lunar, Sidereal, DragonBlooded, Alchemical, Getimian, Liminal,
#             CelestialExigent, TerrestrialExigent, DreamSouled, Hearteater, Umbral]

TEMPLATES = [Mortal, Solar, Lunar, DragonBlooded, CelestialExigent, TerrestrialExigent, DreamSouled, Hearteater, Umbral]

TEMPLATES_DICT = {x.get_name(): x for x in TEMPLATES}


class TemplateHandler:

    def __init__(self, owner):
        self.owner = owner
        self.template = self.get_templates().get(self.owner.story.name)(self)

    def __str__(self):
        return f"<{self.__class__.__name__}: {str(self.template)}>"

    def get_templates(self):
        return TEMPLATES_DICT

    def set(self, template_name: str):
        templates = self.get_templates()
        if not template_name:
            raise StoryDBException(f"Must enter a Template name!")
        if not (found := partial_match(template_name, templates.keys())):
            raise StoryDBException(f"No Template matches {template_name}.")
        self.template = templates[found](self)
        self.owner.story.name = found
        self.owner.story.sub_name = self.template.default_sub
        self.owner.story.extra = None
        self.owner.story.save()
        self.template.reset_sub()
