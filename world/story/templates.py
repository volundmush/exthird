from .exceptions import StoryDBException
from world.utils import partial_match


class Template:
    sub_types = []
    sub_name = "Caste"
    sheet_colors = {}
    start_advantages = {
        "Willpower": 5,
        "Essence": 1
    }

    def set_sub(self, entry: str):
        if not entry:
            raise StoryDBException(f"Must enter a Template name!")
        if not (found := partial_match(entry, self.sub_types)):
            raise StoryDBException(f"No {self.sub_name} matches {entry}.")
        self.handler.owner.db.template_subtype = found

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


class Solar(_Solaroid):
    sub_types = ["Dawn", "Zenith", "Twilight", "Night", "Eclipse"]
    sheet_colors = {"border": "bold yellow",
                    "stat_value": "bold green",
                    "stat_name": "yellow",
                    "stat_header": "bold red"}

class Abyssal(_Solaroid):
    sub_types = ["Dusk", "Midnight", "Daybreak", "Day", "Moonshadow"]


class Infernal(_Solaroid):
    sub_types = ["Azimuth", "Ascendant", "Horizon", "Nadir", "Penumbra"]


class Lunar(Template):
    sub_types = ["Full Moon", "Changing Moon", "No Moon", "Casteless"]

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 1) + 15

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 34


class Sidereal(Template):
    sub_types = ["Journeys", "Serenity", "Battles", "Secrets", "Endings"]

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 2) + 9

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 6) + 25


class DragonBlooded(Template):
    name = "Dragon-Blooded"
    sub_name = 'Aspect'
    sub_types = ["Air", "Earth", "Fire", "Water", "Wood"]

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 1) + 11

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 23


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


TEMPLATES = [Mortal, Solar, Abyssal, Infernal, Lunar, Sidereal, DragonBlooded, Alchemical, Getimian, Liminal,
             CelestialExigent, TerrestrialExigent, DreamSouled, Hearteater, Umbral]

TEMPLATES_DICT = {x.get_name(): x for x in TEMPLATES}


class TemplateHandler:

    def __init__(self, owner):
        self.owner = owner
        self.template = self.get_templates().get(self.owner.attributes.get(key="template", default="Mortal"), None)(self)

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
        self.owner.attributes.add(key="template", value=found)
