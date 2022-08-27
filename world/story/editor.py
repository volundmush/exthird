from world.utils import partial_match
from world.story.exceptions import StoryDBException
import inflect
from rich.table import Table
from rich.console import Group
from rich.text import Text
from rich.markup import escape
from rich.box import ASCII2
from rich.columns import Columns

_INFLECT = inflect.engine()

_nodes = ["template", "attributes", "abilities", "merits", "charms", "spells", "evocations", "miscellaneous"]


def _table() -> Table:
    table = Table(safe_box=True, box=ASCII2, show_header=False, expand=True)
    table.add_column()
    return table


def _mode_change(caller, raw_string, **kwargs):
    choices = _nodes
    if not (choice := partial_match(caller.ndb._menu_match.group("args"), choices)):
        caller.msg(f"Invalid mode. Choices are: {', '.join(choices)}")
    return choice


def _sheet(caller):
    target = caller.ndb.target
    caller.msg(target.story_sheet.render())


def _main_options(caller):
    options = list()

    options.append({"key": "mode", "desc": "Change mode.",
                    "syntax": "mode <choice>",
                    "choices": _nodes,
                    "goto": _mode_change})
    options.append({"key": "sheet", "desc": "Display sheet",
                    "syntax": "sheet", "goto": _sheet})

    return options


def _template(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        if not target.change_type(caller.ndb._menu_match.group("args")):
            caller.msg(f"{target} is already of that nature!")
            return
        kind = _INFLECT.a(target.full_kind_name())
        target.msg(f"You are now {kind}")
        if caller != target:
            caller.msg(f"{target} is now {kind}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _field(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        choice, value = target.set_extra_field(caller.ndb._menu_match.group("lsargs"), caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {choice} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {choice} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


_CHARGEN = [
    "\nCHARGEN: Please set your sheet to its final state after spending bonus points. Mark down your BP expenditures in a +bg file named Bonus."
]


def template(caller, raw_string, **kwargs):
    options = list()
    options.append({"key": "template", "desc": "Change Template",
                    "syntax": "template <kind[/sub]>",
                    "goto": _template})

    text = list()
    target = caller.ndb.target
    text.append(Text(f"Template: {target}", justify='center', style="bold"))
    text.append(f"{target} is {_INFLECT.a(target.full_kind_name())}")

    for k, v in target.extra_fields.items():
        match v:
            case True:
                text.append(f"REQUIRED FIELD: {k}")
            case False:
                text.append(f"OPTIONAL FIELD: {k}")
            case _:
                if isinstance(v, list):
                    text.append(f"CHOICES FIELD: {k} - {', '.join(v)}")
                else:
                    text.append(f"UNKNOWN FIELD: {k}")
        text.append(f"CURRENTLY: {target.get_extra_field(k)}")

    if caller.ndb.chargen:
        text.extend(_CHARGEN)

    if target.extra_fields:
        options.append({"key": "field", "desc": "set field",
                        "syntax": "field <name>=<value>",
                        "goto": _field})

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options


def _attribute(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_attributes.set(caller.ndb._menu_match.group("lsargs"),
                                               caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {stat} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _favor_attribute(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_attributes.set_favored(caller.ndb._menu_match.group("args"), toggle=True)
        outcome = "now Favored" if value else "no longer Favored"
        target.msg(f"Your {stat} is {outcome}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is {outcome}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _caste_attribute(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_attributes.set_caste(caller.ndb._menu_match.group("args"), toggle=True)
        outcome = f"now {_INFLECT.a(target.sub_name)} Attribute" if value else f"no longer {_INFLECT.a(target.sub_name)} Attribute"
        target.msg(f"Your {stat} is {outcome}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is {outcome}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _supernal_attribute(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_attributes.set_supernal(caller.ndb._menu_match.group("args"), toggle=True)
        outcome = f"now {_INFLECT.a(target.supernal_attribute_name)} Attribute" if value else f"no longer {_INFLECT.a(target.supernal_attribute_name)} Attribute"
        target.msg(f"Your {stat} is {outcome}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is {outcome}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _format_attribute(stat, target):
    out = f"{str(stat)}: {stat.calculated_value()}"
    par = list()
    if stat.is_favored():
        par.append("Favored")
    if stat.is_caste():
        par.append(target.sub_name)
    if stat.is_supernal():
        par.append(target.supernal_attribute_name)
    if par:
        return f"{out} ({', '.join(par)})"
    return out


def attributes(caller, raw_string, **kwargs):
    options = list()
    target = caller.ndb.target
    text = list()

    text.append(Text(f"Attributes: {target}", justify='center', style="bold"))
    stats = target.story_attributes.all()
    columns = Columns([_format_attribute(x, target) for x in stats])

    text.append(columns)

    options.append({"key": "set", "desc": "Set Attribute Rating",
                    "syntax": "set <attribute>=<value>",
                    "goto": _attribute})

    if target.favored_attributes:
        options.append({"key": "favor", "desc": "Favor an Attribute",
                        "syntax": "favor <attribute>",
                        "goto": _favor_attribute})

    if target.caste_attributes:
        options.append({"key": target.sub_name.lower(), "desc": f"Set an Attribute {target.sub_name}",
                        "syntax": f"{target.sub_name.lower()} <attribute>",
                        "goto": _caste_attribute})

    if target.supernal_attributes:
        options.append({"key": target.supernal_attribute_name.lower(), "desc": f"Set an Attribute {target.supernal_attribute_name}",
                        "syntax": f"{target.supernal_attribute_name.lower()} <attribute>",
                        "goto": _supernal_attribute})


    if caller.ndb.chargen:
        text.extend(_CHARGEN)

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options


def _ability(caller, raw_string, **kwargs):
    pass


def _favor_ability(caller, raw_string, **kwargs):
    pass


def _caste_ability(caller, raw_string, **kwargs):
    pass


def _supernal_ability(caller, raw_string, **kwargs):
    pass


def _craft(caller, raw_string, **kwargs):
    pass


def _style(caller, raw_string, **kwargs):
    pass


def abilities(caller, raw_string, **kwargs):
    options = list()
    target = caller.ndb.target
    text = list()
    text.append(Text(f"Abilities: {target}", justify='center', style="bold"))
    if caller.ndb.chargen:
        text.extend(_CHARGEN)
    text.append(f"ABILITIES: {', '.join([str(x) for x in target.story_abilities.all()])}")

    options.append({"key": "set", "desc": "Set Ability Rating",
                    "syntax": "set <ability>=<value>",
                    "goto": _ability})

    if target.favored_abilities:
        options.append({"key": "favor", "desc": "Favor an Ability",
                        "syntax": "favor <ability>",
                        "goto": _favor_ability})

    if target.caste_abilities:
        options.append({"key": target.sub_name.lower(), "desc": f"Set an Ability {target.sub_name}",
                        "syntax": f"{target.sub_name.lower()} <ability>",
                        "goto": _caste_ability})

    if target.supernal_abilities:
        options.append({"key": target.supernal_ability_name.lower(), "desc": f"Set an Ability {target.supernal_ability_name}",
                        "syntax": f"{target.supernal_ability_name.lower()} <ability>",
                        "goto": _supernal_ability})

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options


def merits(caller, raw_string, **kwargs):
    options = list()
    text = list()
    target = caller.ndb.target
    text.append(Text(f"Merits: {target}", justify='center', style="bold"))
    if caller.ndb.chargen:
        text.extend(_CHARGEN)

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options


def charms(caller, raw_string, **kwargs):
    options = list()
    text = list()
    target = caller.ndb.target
    text.append(Text(f"Charms: {target}", justify='center', style="bold"))
    if caller.ndb.chargen:
        text.extend(_CHARGEN)

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options


def spells(caller, raw_string, **kwargs):
    options = list()
    text = list()
    target = caller.ndb.target
    text.append(Text(f"Spells: {target}", justify='center', style="bold"))
    if caller.ndb.chargen:
        text.extend(_CHARGEN)

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options


def evocations(caller, raw_string, **kwargs):
    options = list()
    text = list()
    target = caller.ndb.target
    text.append(Text(f"Evocations: {target}", justify='center', style="bold"))
    if caller.ndb.chargen:
        text.extend(_CHARGEN)

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options


def miscellaneous(caller, raw_string, **kwargs):
    options = list()
    text = list()
    target = caller.ndb.target
    text.append(Text(f"Miscellaneous: {target}", justify='center', style="bold"))

    table = _table()

    text = [escape(t) if isinstance(t, str) else t for t in text]
    table.add_row(Group(*text))

    options.extend(_main_options(caller))
    return table, options
