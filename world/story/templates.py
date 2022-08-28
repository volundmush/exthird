from .exceptions import StoryDBException
from world.utils import partial_match
from typeclasses.characters import Character


class Template(Character):
    kind = None
    sub_abilities = []
    sub_attributes = []
    caste_attributes = 0
    favored_attributes = 0
    supernal_attributes = 0
    caste_abilities = 0
    favored_abilities = 0
    supernal_abilities = 0
    dots_abilities = 28
    dots_specialties = 4
    sub_name = "Caste"
    sheet_colors = {}
    start_advantages = {
        "Willpower": 5,
        "Essence": 1
    }
    extra_fields = {}
    supernal_attribute_name = None
    supernal_ability_name = None
    chargen_template = []
    chargen_attributes = []
    chargen_abilities = []


    def at_object_creation(self):
        super().at_object_creation()
        self.story_reset()

    def story_reset(self):
        for k, v in self.start_advantages.items():
            if (stat := self.story_advantages.data[k]):
                if stat.calculated_value() < v:
                    stat.set_value(v)
        self.story_attributes.reset_sub()
        self.story_abilities.reset_sub()
        self.attributes.clear(category="extra")

    def pool_personal_max(self):
        pass

    def pool_peripheral_max(self):
        pass

    def native_charm_category(self):
        return self.kind

    def get_advantage_value(self, name: str):
        return self.story_advantages.get_value(name)

    def change_type(self, name: str):
        from world.story.templates import find_template, TEMPLATES
        found = find_template(name)
        if not isinstance(self, found):
            self.swap_typeclass(new_typeclass=found)
            return True
        return False

    @classmethod
    def get_type_name(cls):
        return getattr(cls, "type_name", cls.__name__)

    def full_kind_name(self):
        return f"{self.get_type_name()} {self.sub_name} {self.kind}"

    def get_extra_field(self, name: str):
        return self.attributes.get(name, category='extra', default='')

    def set_extra_field(self, name: str, value: str):
        if not name:
            raise StoryDBException("Must enter a field name!")
        if not (choice := partial_match(name, self.extra_fields.keys())):
            raise StoryDBException("That is not a valid field name!")
        if not value:
            raise StoryDBException("Must enter a value!")
        options = self.extra_fields[choice]
        match options:
            case True | False:
                pass
            case _:
                if isinstance(options, list):
                    if not (value := partial_match(value, options)):
                        raise StoryDBException(f"Not a valid choice for {choice}! Choices are: {', '.join(options)}")
        self.attributes.add(choice, value=value, category="extra")
        return choice, value


class Mortal(Template):
    kind = "Mortal"
    sub_name = "Archetype"
    extra_fields = {"Profession": None}
    start_advantages = {
        "Willpower": 3,
        "Essence": 1
    }


class _Solaroid(Template):
    favored_abilities = 5
    caste_abilities = 5
    chargen_abilities = ["Every Favored Ability must have at least one dot!"]

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 3) + 10

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 7) + 26


_DAWN = ["Archery", "Awareness", "Brawl", "Dodge", "Melee", "Resistance", "Thrown", "War"]
_ZENITH = ["Athletics", "Integrity", "Performance", "Lore", "Presence", "Resistance", "Survival", "War"]
_TWILIGHT = ["Bureaucracy", "Craft", "Integrity", "Investigation", "Linguistics", "Lore", "Medicine", "Occult"]
_NIGHT = ["Athletics", "Awareness", "Dodge", "Investigation", "Larceny", "Ride", "Stealth", "Socialize"]
_ECLIPSE = ["Bureaucracy", "Larceny", "Linguistics", "Occult", "Presence", "Ride", "Sail", "Socialize"]


class _Solar(_Solaroid):
    kind = "Solar"
    sheet_colors = {"border": "bold yellow",
                    "stat_value": "bold green",
                    "stat_supernal": "bold yellow underline",
                    "stat_favored": "yellow",
                    "stat_caste": "bold yellow",
                    "stat_header": "bold red",
                    "power_subcategory": "bold yellow"
                    }
    supernal_abilities = 1
    supernal_ability_name = "Supernal"
    chargen_attributes = ["Solars distribute 8/6/4 Primary/Secondary/Tertiary points amongst their Attributes. Remember, each begins 1 for free."]


class Dawn(_Solar):
    sub_abilities = _DAWN


class Zenith(_Solar):
    sub_abilities = _ZENITH


class Twilight(_Solar):
    sub_abilities = _TWILIGHT


class Night(_Solar):
    sub_abilities = _NIGHT


class Eclipse(_Solar):
    sub_abilities = _ECLIPSE


class _Abyssal(_Solaroid):
    kind = "Abyssal"
    sheet_colors = {"border": "bold black",
                    "stat_value": "red",
                    "stat_supernal": "bold red underline",
                    "stat_favored": "red",
                    "stat_caste": "bold red",
                    "stat_header": "not bold magenta",
                    "power_subcategory": "bold black"
                    }
    supernal_abilities = 1
    supernal_ability_name = "Chthonic"
    chargen_attributes = ["Abyssals distribute 8/6/4 Primary/Secondary/Tertiary points amongst their Attributes. Remember, each begins 1 for free."]


class Dusk(_Abyssal):
    sub_abilities = _DAWN


class Midnight(_Abyssal):
    sub_abilities = _ZENITH


class Daybreak(_Abyssal):
    sub_abilities = _TWILIGHT


class Day(_Abyssal):
    sub_abilities = _NIGHT


class Moonshadow(_Abyssal):
    sub_abilities = _ECLIPSE


class _Infernal(_Solaroid):
    kind = "Infernal"
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


class Azimuth(_Infernal):
    sub_abilities = _DAWN


class Ascendant(_Infernal):
    sub_abilities = _ZENITH


class Horizon(_Infernal):
    sub_abilities = _TWILIGHT


class Nadir(_Infernal):
    sub_abilities = _NIGHT


class Penumbra(_Infernal):
    sub_abilities = _ECLIPSE


class _Lunar(Template):
    kind = "Lunar"
    favored_attributes = 2
    sheet_colors = {"border": "bold cyan",
                    "stat_value": "bold green",
                    "stat_supernal": "bold cyan underline",
                    "stat_favored": "cyan",
                    "stat_caste": "bold cyan",
                    "stat_header": "bold blue",
                    "power_subcategory": "bold cyan"
                    }

    extra_fields = {"Spirit Shape": True,
                    "Tell": True}

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 1) + 15

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 34


class Casteless(_Lunar):
    pass


class _Tattooed(_Lunar):
    caste_attributes = 2


class FullMoon(_Tattooed):
    type_name = "Full Moon"
    sub_attributes = ["Dexterity", "Stamina", "Strength"]


class ChangingMoon(_Tattooed):
    type_name = "Changing Moon"
    sub_attributes = ["Appearance", "Charisma", "Manipulation"]


class NoMoon(_Tattooed):
    type_name = "No Moon"
    sub_attributes = ["Intelligence", "Perception", "Wits"]


class _Sidereal(Template):
    kind = "Sidereal"
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


class Journeys(_Sidereal):
    pass


class Battles(_Sidereal):
    pass


class Endings(_Sidereal):
    pass


class Secrets(_Sidereal):
    pass


class Serenity(_Sidereal):
    pass


class _DragonBlood(Template):
    kind = "Dragon-Blooded"
    favored_abilities = 5
    sub_name = "Aspect"
    sheet_colors = {"border": "bold red",
                    "stat_value": "bold green",
                    "stat_supernal": "bold red underline",
                    "stat_favored": "not bold red",
                    "stat_caste": "bold red",
                    "stat_header": "bold cyan",
                    "power_subcategory": "not bold cyan"
                    }

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 1) + 11

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 23

    def at_object_creation(self):
        super().at_object_creation()
        for abil in self.sub_abilities:
            if (ab := self.story_abilities.data.get(abil, None)):
                ab.model.flag_1 = 2
                ab.model.save(update_fields=["flag_1"])


class Air(_DragonBlood):
    sub_abilities = ["Linguistics", "Lore", "Occult", "Stealth", "Thrown"]


class Earth(_DragonBlood):
    sub_abilities = ["Awareness", "Craft", "Integrity", "Resistance", "War"]


class Fire(_DragonBlood):
    sub_abilities = ["Athletics", "Dodge", "Melee", "Presence", "Socialize"]


class Water(_DragonBlood):
    sub_abilities = ["Brawl", "Bureaucracy", "Investigation", "Larceny", "Sail"]


class Wood(_DragonBlood):
    sub_abilities = ["Archery", "Medicine", "Performance", "Ride", "Survival"]


class _Alchemical(Template):
    kind = "Alchemical"


class Adamant(_Alchemical):
    pass


class Jade(_Alchemical):
    pass


class Moonsilver(_Alchemical):
    pass


class Orichalcum(_Alchemical):
    pass


class Starmetal(_Alchemical):
    pass


class Soulsteel(_Alchemical):
    pass


class _Getimian(Template):
    kind = "Getimian"


class Spring(_Getimian):
    pass


class Summer(_Getimian):
    pass


class Autumn(_Getimian):
    pass


class Winter(_Getimian):
    pass


class _Liminal(Template):
    kind = "Liminal"
    sub_types = ["Blood", "Breath", "Flesh", "Marrow", "Soil"]

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 3) + 10

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 23


class Blood(_Liminal):
    pass


class Breath(_Liminal):
    pass


class Flesh(_Liminal):
    pass


class Marrow(_Liminal):
    pass


class Soil(_Liminal):
    pass


class _CelestialPools(Template):

    def pool_personal_max(self):
        return (self.get_advantage_value("Essence") * 2) + 11

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 6) + 27


class _TerrestrialPools(Template):

    def pool_personal_max(self):
        return self.get_advantage_value("Essence") + 11

    def pool_peripheral_max(self):
        return (self.get_advantage_value("Essence") * 4) + 23


class _Exigent(Template):
    kind = "Exigent"


class Terrestrial(_TerrestrialPools, _Exigent):
    pass


class Celestial(_CelestialPools, _Exigent):
    pass


class DreamSouled(_TerrestrialPools):
    kind = "Dream-Souled"
    sub_name = "Tier"
    type_name = "Dream-Souled"


class Hearteater(_CelestialPools):
    kind = "Hearteater"
    sub_name = "Tier"


class Umbral(_CelestialPools):
    kind = "Umbral"
    sub_name = "Tier"


TEMPLATES = {
    "Mortal": Mortal,
    "Solar": [Dawn, Zenith, Twilight, Night, Eclipse],
    "Abyssal": [Dusk, Midnight, Daybreak, Day, Moonshadow],
    "Infernal": [Azimuth, Ascendant, Horizon, Nadir, Penumbra],
    "Lunar": [Casteless, FullMoon, ChangingMoon, NoMoon],
    "Sidereal": [Journeys, Battles, Endings, Secrets, Serenity],
    "Dragon-Blooded": [Air, Earth, Fire, Water, Wood],
    "Alchemical": [Adamant, Orichalcum, Moonsilver, Jade, Starmetal, Soulsteel],
    "Getimian": [Spring, Summer, Autumn, Winter],
    "Liminal": [Blood, Breath, Flesh, Marrow, Soil],
    "Exigent": [Terrestrial, Celestial],
    "Dream-Souled": DreamSouled,
    "Hearteater": Hearteater,
    "Umbral": Umbral
}


def find_template(name: str):
    if not name:
        raise StoryDBException("Must enter a Template name!")
    words = name.split("/")
    if not (template_name := partial_match(words[0], TEMPLATES.keys())):
        raise StoryDBException(f"Template '{words[0]}' not found. Choices are: {', '.join(TEMPLATES.keys())}")
    choices = TEMPLATES[template_name]

    # just return the first match if the value isn't a list.
    if not isinstance(choices, list):
        return choices

    if len(words) < 2:
        raise StoryDBException(f"Template '{words[0]}' not found. Choices are: {', '.join([getattr(x, 'type_name', x.__name__) for x in choices])}")

    if not (found := partial_match(words[1], choices, key=lambda x: getattr(x, 'type_name', x.__name__))):
        raise StoryDBException(
            f"Template '{words[0]}' not found. Choices are: {', '.join([getattr(x, 'type_name', x.__name__) for x in choices])}")
    return found
