"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent
from evennia.utils.utils import lazy_property

from world.story import stats
from world.story.templates import TemplateHandler
from world.story.powers import CharmHandler, SpellHandler
from world.story.sheet import SheetHandler


class Character(ObjectParent, DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_post_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    @lazy_property
    def story_template(self):
        return TemplateHandler(self)

    @lazy_property
    def story_advantages(self):
        return stats.AdvantageHandler(self)

    @lazy_property
    def story_attributes(self):
        return stats.AttributeHandler(self)

    @lazy_property
    def story_abilities(self):
        return stats.AbilityHandler(self)

    @lazy_property
    def story_styles(self):
        return stats.StyleHandler(self)

    @lazy_property
    def story_crafts(self):
        return stats.CraftHandler(self)

    @lazy_property
    def story_charms(self):
        return CharmHandler(self)

    @lazy_property
    def story_spells(self):
        return SpellHandler(self)

    @lazy_property
    def story_sheet(self):
        return SheetHandler(self)
