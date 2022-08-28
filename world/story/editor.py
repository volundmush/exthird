from world.utils import partial_match
from world.story.exceptions import StoryDBException
import inflect
from rich.table import Table
from rich.console import Group
from rich.text import Text
from rich.markup import escape
from rich.box import ASCII2
from rich.columns import Columns
from world.story.powers import CHARM_CATEGORIES, SPELL_CATEGORIES

_INFLECT = inflect.engine()

_nodes = ["template", "attributes", "abilities", "merits", "powers", "miscellaneous"]


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
    "\nCHARGEN: Please set your sheet to its final state after spending bonus points. Mark down your BP expenditures in a +cg file named Bonus."
]


def template(caller, raw_string, **kwargs):
    options = list()
    options.append({"key": "template", "desc": "Change Template",
                    "syntax": "template <kind[/sub]>",
                    "goto": _template})

    text = list()
    target = caller.ndb.target
    text.append(Text(f"Template: {target}", justify='center', style="bold"))

    from world.story.templates import TEMPLATES

    text.append("Templates:")
    for k, v in TEMPLATES.items():
        if isinstance(v, list):
            text.append(f"{k}: {', '.join([x.get_type_name() for x in v])}")
        else:
            text.append(k)

    if caller.ndb.chargen:
        text.extend(target.chargen_template)

    text.append(f"\n{target} is {_INFLECT.a(target.full_kind_name())}\n")
    if target.extra_fields:
        options.append({"key": "field", "desc": "set field",
                        "syntax": "field <name>=<value>",
                        "goto": _field})

        text.append(f"Extra Fields for {_INFLECT.a(target.full_kind_name())}:")
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
    text.append("")

    if caller.ndb.chargen:
        if target.favored_attributes or target.caste_attributes or target.supernal_attributes:
            text.append(f"\n{_INFLECT.a(target.full_kind_name())} receives:")
            if target.caste_attributes:
                count = [x for x in stats if x.is_caste(ignore_derived=True)]
                text.append(
                    f"{len(count)}/{target.caste_attributes} {target.sub_name} Attributes, chosen from {', '.join(target.sub_attributes)}")
            if target.supernal_attributes:
                count = [x for x in stats if x.is_supernal(ignore_derived=True)]
                text.append(
                    f"{len(count)}/{target.supernal_attributes} {target.supernal_ability_name} Attributes, from among the selected {target.sub_name} Attributes.")
            if target.favored_attributes:
                count = [x for x in stats if x.is_favored(ignore_derived=True)]
                text.append(
                    f"{len(count)}/{target.favored_attributes} Favored Attributes.")
        if target.dots_attributes:
            physical = sum([x.true_value() - 1 for x in target.story_attributes.all_physical()])
            social = sum([x.true_value() - 1 for x in target.story_attributes.all_social()])
            mental = sum([x.true_value() -1 for x in target.story_attributes.all_mental()])
            count = sum([physical, social, mental])
            text.append(
                f"{count}/{target.dots_attributes} Attribute Dots (Physical: {physical}, Social: {social}, Mental: {mental})")
        text.extend(target.chargen_attributes)

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
    try:
        target = caller.ndb.target
        stat, value = target.story_abilities.set(caller.ndb._menu_match.group("lsargs"),
                                                  caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {stat} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _favor_ability(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_abilities.set_favored(caller.ndb._menu_match.group("args"), toggle=True)
        outcome = "now Favored" if value else "no longer Favored"
        target.msg(f"Your {stat} is {outcome}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is {outcome}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _caste_ability(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_abilities.set_caste(caller.ndb._menu_match.group("args"), toggle=True)
        outcome = f"now {_INFLECT.a(target.sub_name)} Ability" if value else f"no longer {_INFLECT.a(target.sub_name)} Ability"
        target.msg(f"Your {stat} is {outcome}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is {outcome}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _supernal_ability(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_abilities.set_supernal(caller.ndb._menu_match.group("args"), toggle=True)
        outcome = f"now {_INFLECT.a(target.supernal_ability_name)} Ability" if value else f"no longer {_INFLECT.a(target.supernal_ability_name)} Ability"
        target.msg(f"Your {stat} is {outcome}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is {outcome}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _craft(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_crafts.set(caller.ndb._menu_match.group("lsargs"),
                                                 caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {stat} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _style(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        stat, value = target.story_styles.set(caller.ndb._menu_match.group("lsargs"),
                                                  caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {stat} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {stat} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _format_ability(stat, target, ignore_extra=False):
    out = f"{str(stat)}: {stat.calculated_value()}"
    par = list()
    if not ignore_extra:
        if stat.is_favored():
            par.append("Favored")
        if stat.is_caste():
            par.append(target.sub_name)
        if stat.is_supernal():
            par.append(target.supernal_ability_name)
    if par:
        return f"{out} ({', '.join(par)})"
    return out


def abilities(caller, raw_string, **kwargs):
    options = list()
    target = caller.ndb.target
    text = list()
    text.append(Text(f"Abilities: {target}", justify='center', style="bold"))

    stats = target.story_abilities.all()
    columns = Columns([_format_ability(x, target) for x in stats])

    text.append(columns)

    if (crafts := target.story_crafts.all()):
        text.append(Text(f"Crafts", justify='center', style="bold"))
        columns = Columns([_format_ability(x, target, ignore_extra=True) for x in crafts])
        text.append(columns)
        text.append("")

    if (styles := target.story_styles.all()):
        text.append(Text(f"Styles", justify='center', style="bold"))
        columns = Columns([_format_ability(x, target, ignore_extra=True) for x in styles])
        text.append(columns)
        text.append("")

    text.append("Martial Arts and Craft cannot be assigned a rating directly. Their displayed rating is equal to the highest taken Crafts or MA Style.")
    if target.caste_abilities or target.favored_abilities:
        text.append(f"Martial Arts cannot be picked as a Favored or {target.sub_name} Ability directly.")
        text.append(f"It inherits the status of Brawl.")
        if target.supernal_abilities:
            text.append(f"Martial Art can be chosen as a {target.supernal_ability_name} Ability if Brawl is a {target.sub_name} Ability.")

    if caller.ndb.chargen:
        if target.favored_abilities or target.caste_abilities or target.supernal_abilities:
            text.append(f"\n{_INFLECT.a(target.full_kind_name())} receives:")
            if target.caste_abilities:
                count = [x for x in stats if x.is_caste(ignore_derived=True)]
                text.append(f"{len(count)}/{target.caste_abilities} {target.sub_name} Abilities, chosen from {', '.join(target.sub_abilities)}")
            if target.supernal_abilities:
                count = [x for x in stats if x.is_supernal(ignore_derived=True)]
                text.append(
                    f"{len(count)}/{target.supernal_abilities} {target.supernal_ability_name} Abilities, from among the selected {target.sub_name} Abilities.")
            if target.favored_abilities:
                count = [x for x in stats if x.is_favored(ignore_derived=True)]
                text.append(
                    f"{len(count)}/{target.favored_abilities} Favored Abilities.")
            if target.dots_abilities:
                count = sum([x.true_value() for x in stats])
                styles = sum([x.true_value() for x in target.story_styles.all()])
                craft_count = sum([x.true_value() for x in crafts])
                text.append(f"{sum([count, styles, craft_count])}/{target.dots_abilities} Ability Dots (Crafts: {craft_count}, Styles: {styles})")
            if target.dots_specialties:
                count = len(target.story_abilities.all_specialties())
                text.append(f"{count}/{target.dots_specialties} Specialtiy Dots")
        text.extend(target.chargen_abilities)


    if caller.ndb.chargen:
        text.extend(_CHARGEN)

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

    options.append({"key": "craft", "desc": "Set Craft Rating",
                    "syntax": "craft <craft>=<value>",
                    "goto": _craft})

    options.append({"key": "style", "desc": "Set Style Rating",
                    "syntax": "style <style>=<value>",
                    "goto": _style})

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


def _charm(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_charms.add(caller.ndb._menu_match.group("lsargs"),
                                              caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _delcharm(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_charms.remove(caller.ndb._menu_match.group("lsargs"),
                                               caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _spell(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_spells.add(caller.ndb._menu_match.group("lsargs"),
                                               caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _delspell(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_spells.remove(caller.ndb._menu_match.group("lsargs"),
                                                  caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _ocharm(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        args = caller.ndb._menu_match.group("lsargs").split("/")
        if len(args) != 2:
            raise StoryDBException("usage: ocharm <kind>/<category>=<name>")
        power, value = target.story_charms.add(args[1],
                                               caller.ndb._menu_match.group("rsargs"), main_category=args[0])
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _delocharm(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        args = caller.ndb._menu_match.group("lsargs").split("/")
        if len(args) != 2:
            raise StoryDBException("usage: ocharm <kind>/<category>=<name>")
        power, value = target.story_charms.remove(args[1],
                                               caller.ndb._menu_match.group("rsargs"), main_category=args[0])
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _macharm(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_charms.add(caller.ndb._menu_match.group("lsargs"),
                                               caller.ndb._menu_match.group("rsargs"),
                                               main_category="Martial Arts")
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _delmacharm(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_charms.remove(caller.ndb._menu_match.group("lsargs"),
                                               caller.ndb._menu_match.group("rsargs"),
                                               main_category="Martial Arts")
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _evocation(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_evocations.add(caller.ndb._menu_match.group("lsargs"),
                                               caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _delevocation(caller, raw_string, **kwargs):
    try:
        target = caller.ndb.target
        power, value = target.story_evocations.remove(caller.ndb._menu_match.group("lsargs"),
                                                   caller.ndb._menu_match.group("rsargs"))
        target.msg(f"Your {power} is now: {value}")
        if caller != target:
            caller.msg(f"{target}'s {power} is now: {value}")
    except StoryDBException as err:
        caller.msg(f"ERROR: {err}")


def _format_power(power, target, ignore_extra=False):
    if power.value > 1:
        return f"{power} ({power.value})"
    return str(power)


def powers(caller, raw_string, **kwargs):
    options = list()
    text = list()
    target = caller.ndb.target
    text.append(Text(f"Powers: {target}", justify='center', style="bold"))

    if (charms := target.story_charms.all_main()):
        text.append(Text(f"Charms", justify='center', style="bold"))
        for category, _subcat in charms.items():
            for subcat, entries in _subcat.items():
                text.append(Text(f"{category}: {subcat}", justify='center', style='bold'))
                columns = Columns([_format_power(x, target, ignore_extra=True) for x in entries])
                text.append(columns)
        text.append("")

    if (spells := target.story_spells.all_main()):
        text.append(Text(f"Spells", justify='center', style="bold"))
        for category, _subcat in spells.items():
            for subcat, entries in _subcat.items():
                text.append(Text(f"{category}: {subcat}", justify='center', style='bold'))
                columns = Columns([_format_power(x, target, ignore_extra=True) for x in entries])
                text.append(columns)
        text.append("")

    if (evocations := target.story_evocations.all_main()):
        for category, entries in evocations["Evocations"].items():
            text.append(Text(f"Evocations: {category}", justify='center', style='bold'))
            columns = Columns([_format_power(x, target, ignore_extra=True) for x in entries])
            text.append(columns)
        text.append("")

    if caller.ndb.chargen:
        text.append(f"\n{_INFLECT.a(target.full_kind_name())} receives:")
        if target.starting_charms:
            charms_count = target.story_charms.count()
            spells_count = target.story_spells.count()
            evocations_count = target.story_evocations.count()
            text.append(f"{charms_count+spells_count+evocations_count}/{target.starting_charms} starting Charms/Spells/Evocations.")
        text.extend(target.chargen_powers)


    if CHARM_CATEGORIES.get(target.native_charm_category()):
        options.append({"key": "charm", "desc": "Add a native Charm. Add again to repurchase.",
                        "syntax": "charm <category>=<name>",
                        "goto": _charm})

    if charms.pop(target.native_charm_category(), None):
        options.append({"key": "delcharm", "desc": "Remove a native Charm purchase.",
                        "syntax": "delcharm <category>=<name>",
                        "goto": _delcharm})

    if target.story_styles.count():
        options.append({"key": "macharm", "desc": "Add a Martial Arts Charm. Add again to repurchase.",
                        "syntax": "macharm <style>=<name>",
                        "goto": _macharm})

    if charms.pop("Martial Arts", None):
        options.append({"key": "delmacharm", "desc": "Remove a Martial Arts Charm purchase.",
                        "syntax": "delmacharm <style>=<name>",
                        "goto": _delmacharm})

    options.append({"key": "spell", "desc": "Add a Sorcery/Necromancy Spell.",
                    "syntax": "spell <category>=<name>",
                    "goto": _spell})

    if spells:
        options.append({"key": "delspell", "desc": "Remove a Sorcery/Necromancy Spell.",
                        "syntax": "delspell <category>=<name>",
                        "goto": _delspell})

    options.append({"key": "evocation", "desc": "Add Evocations. Again to repurchase.",
                    "syntax": "evocation <category>=<name>",
                    "goto": _evocation})

    if evocations:
        options.append({"key": "delevocation", "desc": "Remove Evocations.",
                        "syntax": "delevocation <category>=<name>",
                        "goto": _delevocation})

    options.append({"key": "ocharm", "desc": "Add non-native Charms. Again to repurchase.",
                    "syntax": "ocharm <kind>/<category>=<name>",
                    "goto": _ocharm})

    if charms:
        options.append({"key": "delocharm", "desc": "Remove non-native Charm Purchases.",
                        "syntax": "delocharm <kind>/<category>=<name>",
                        "goto": _delocharm})

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
