"""
Object

The Object is the "naked" base class for things in the game world.

Note that the default Character, Room and Exit does not inherit from
this Object, but from their respective default implementations in the
evennia library. If you want to use this class as a parent to change
the other types, you can do so by adding this as a multiple
inheritance.

"""
from evennia.objects.objects import DefaultObject
from itertools import chain
from django.core.exceptions import ObjectDoesNotExist
from evennia.utils.utils import make_iter, to_str, logger
from twisted.internet.defer import inlineCallbacks, returnValue
from world.plays.models import PlayDB


class ObjectParent:
    """
    This is a mixin that can be used to override *all* entities inheriting at
    some distance from DefaultObject (Objects, Exits, Characters and Rooms).

    Just add any method that exists on `DefaultObject` to this class. If one
    of the derived classes has itself defined that same hook already, that will
    take precedence.

    """
    cmd_objects_sort_priority = 100

    def get_cmd_objects(self):
        if (puppeteer := self.get_puppeteer()):
            return puppeteer.get_cmd_objects()
        return {"puppet": self}

    @inlineCallbacks
    def get_location_cmdsets(self, caller, current, cmdsets):
        """
        Retrieve Cmdsets from nearby Objects.
        """
        try:
            location = self.location
        except Exception:
            location = None

        if not location:
            returnValue(list())

        local_objlist = yield (
                location.contents_get(exclude=self) + self.contents_get() + [location]
        )
        local_objlist = [o for o in local_objlist if not o._is_deleted]
        for lobj in local_objlist:
            try:
                # call hook in case we need to do dynamic changing to cmdset
                object.__getattribute__(lobj, "at_cmdset_get")(caller=caller)
            except Exception:
                logger.log_trace()
        # the call-type lock is checked here, it makes sure an account
        # is not seeing e.g. the commands on a fellow account (which is why
        # the no_superuser_bypass must be True)
        local_obj_cmdsets = yield list(
            chain.from_iterable(
                lobj.cmdset.cmdset_stack
                for lobj in local_objlist
                if (lobj.cmdset.current and lobj.access(caller, access_type="call", no_superuser_bypass=True))
            )
        )
        for cset in local_obj_cmdsets:
            # This is necessary for object sets, or we won't be able to
            # separate the command sets from each other in a busy room. We
            # only keep the setting if duplicates were set to False/True
            # explicitly.
            cset.old_duplicates = cset.duplicates
            cset.duplicates = True if cset.duplicates is None else cset.duplicates

        if current.no_exits:
            local_obj_cmdsets = [
                cmdset for cmdset in local_obj_cmdsets if cmdset.key != "ExitCmdSet"
            ]

        returnValue((local_obj_cmdsets, local_objlist))

    @inlineCallbacks
    def get_extra_cmdsets(self, caller, current, cmdsets):
        """
        Called by the CmdHandler to retrieve extra cmdsets from this object.
        For DefaultObject, that's cmdsets from nearby Objects.
        """
        extra = list()
        if not current.no_objs:
            obj_cmdsets, local_objlist = yield self.get_location_cmdsets(caller, current, cmdsets)
            extra.extend(obj_cmdsets)
        returnValue(extra)

    def get_play(self):
        return PlayDB.objects.filter(id=self).first()

    def get_puppeteer(self):
        try:
            if hasattr(self, "puppeteer") and self.puppeteer.db_account:
                return self.puppeteer
        except ObjectDoesNotExist:
            return None

    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        # try send hooks
        if from_obj:
            for obj in make_iter(from_obj):
                try:
                    obj.at_msg_send(text=text, to_obj=self, **kwargs)
                except Exception:
                    logger.log_trace()
        kwargs["options"] = options
        try:
            if not self.at_msg_receive(text=text, from_obj=from_obj, **kwargs):
                # if at_msg_receive returns false, we abort message to this object
                return
        except Exception:
            logger.log_trace()

        if text is not None:
            if not isinstance(text, str):
                if isinstance(text, tuple):
                    first = text[0]
                    if hasattr(first, "__rich_console__"):
                        text = first
                    elif isinstance(first, str):
                        text = first
                    else:
                        try:
                            text = to_str(first)
                        except Exception:
                            text = repr(first)
                elif hasattr(text, "__rich_console__"):
                    text = text
                else:
                    try:
                        text = to_str(text)
                    except Exception:
                        text = repr(text)

        # relay to Play object
        if (puppeteer := self.get_puppeteer()):
            puppeteer.msg(text=text, session=session, **kwargs)

    @property
    def is_connected(self):
        return (play := self.get_play()) or (puppeteer := self.get_puppeteer())

    @property
    def has_account(self):
        return self.is_connected

    @property
    def is_superuser(self):
        if (play := self.get_play()) and play.is_superuser:
            return True
        if (puppeteer := self.get_puppeteer()) and puppeteer.is_superuser:
            return True
        return False

    @property
    def idle_time(self):
        """
        Returns the idle time of the least idle session in seconds. If
        no sessions are connected it returns nothing.

        """
        if (play := self.get_play()):
            return play.idle_time
        if (puppeteer := self.get_puppeteer()):
            return puppeteer.idle_time
        return None

    @property
    def connection_time(self):
        if (play := self.get_play()):
            return play.connection_time
        if (puppeteer := self.get_puppeteer()):
            return puppeteer.connection_time
        return None

    def at_possess(self, play):
        pass

    def at_unpossess(self, play):
        pass


class Object(ObjectParent, DefaultObject):
    """
    This is the root typeclass object, implementing an in-game Evennia
    game object, such as having a location, being able to be
    manipulated or looked at, etc. If you create a new typeclass, it
    must always inherit from this object (or any of the other objects
    in this file, since they all actually inherit from BaseObject, as
    seen in src.object.objects).

    The BaseObject class implements several hooks tying into the game
    engine. By re-implementing these hooks you can control the
    system. You should never need to re-implement special Python
    methods, such as __init__ and especially never __getattribute__ and
    __setattr__ since these are used heavily by the typeclass system
    of Evennia and messing with them might well break things for you.


    * Base properties defined/available on all Objects

     key (string) - name of object
     name (string)- same as key
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation

     account (Account) - controlling account (if any, only set together with
                       sessid below)
     sessid (int, read-only) - session id (if any, only set together with
                       account above). Use `sessions` handler to get the
                       Sessions directly.
     location (Object) - current location. Is None if this is a room
     home (Object) - safety start-location
     has_account (bool, read-only)- will only return *connected* accounts
     contents (list of Objects, read-only) - returns all objects inside this
                       object (including exits)
     exits (list of Objects, read-only) - returns all exits from this
                       object, if any
     destination (Object) - only set if this object is an exit.
     is_superuser (bool, read-only) - True/False if this user is a superuser

    * Handlers available

     aliases - alias-handler: use aliases.add/remove/get() to use.
     permissions - permission-handler: use permissions.add/remove() to
                   add/remove new perms.
     locks - lock-handler: use locks.add() to add new lock strings
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().
     sessions - sessions-handler. Get Sessions connected to this
                object with sessions.get()
     attributes - attribute-handler. Use attributes.add/remove/get.
     db - attribute-handler: Shortcut for attribute-handler. Store/retrieve
            database attributes using self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create
            a database entry when storing data

    * Helper methods (see src.objects.objects.py for full headers)

     search(ostring, global_search=False, attribute_name=None,
             use_nicks=False, location=None, ignore_errors=False, account=False)
     execute_cmd(raw_string)
     msg(text=None, **kwargs)
     msg_contents(message, exclude=None, from_obj=None, **kwargs)
     move_to(destination, quiet=False, emit_to_obj=None, use_destination=True)
     copy(new_key=None)
     delete()
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False)
     check_permstring(permstring)

    * Hooks (these are class methods, so args should start with self):

     basetype_setup()     - only called once, used for behind-the-scenes
                            setup. Normally not modified.
     basetype_posthook_setup() - customization in basetype, after the object
                            has been created; Normally not modified.

     at_object_creation() - only called once, when object is first created.
                            Object customizations go here.
     at_object_delete() - called just before deleting an object. If returning
                            False, deletion is aborted. Note that all objects
                            inside a deleted object are automatically moved
                            to their <home>, they don't need to be removed here.

     at_init()            - called whenever typeclass is cached from memory,
                            at least once every server restart/reload
     at_cmdset_get(**kwargs) - this is called just before the command handler
                            requests a cmdset from this object. The kwargs are
                            not normally used unless the cmdset is created
                            dynamically (see e.g. Exits).
     at_pre_puppet(account)- (account-controlled objects only) called just
                            before puppeting
     at_post_puppet()     - (account-controlled objects only) called just
                            after completing connection account<->object
     at_pre_unpuppet()    - (account-controlled objects only) called just
                            before un-puppeting
     at_post_unpuppet(account) - (account-controlled objects only) called just
                            after disconnecting account<->object link
     at_server_reload()   - called before server is reloaded
     at_server_shutdown() - called just before server is fully shut down

     at_access(result, accessing_obj, access_type) - called with the result
                            of a lock access check on this object. Return value
                            does not affect check result.

     at_pre_move(destination)             - called just before moving object
                        to the destination. If returns False, move is cancelled.
     announce_move_from(destination)         - called in old location, just
                        before move, if obj.move_to() has quiet=False
     announce_move_to(source_location)       - called in new location, just
                        after move, if obj.move_to() has quiet=False
     at_post_move(source_location)          - always called after a move has
                        been successfully performed.
     at_object_leave(obj, target_location)   - called when an object leaves
                        this object in any fashion
     at_object_receive(obj, source_location) - called when this object receives
                        another object

     at_traverse(traversing_object, source_loc) - (exit-objects only)
                              handles all moving across the exit, including
                              calling the other exit hooks. Use super() to retain
                              the default functionality.
     at_post_traverse(traversing_object, source_location) - (exit-objects only)
                              called just after a traversal has happened.
     at_failed_traverse(traversing_object)      - (exit-objects only) called if
                       traversal fails and property err_traverse is not defined.

     at_msg_receive(self, msg, from_obj=None, **kwargs) - called when a message
                             (via self.msg()) is sent to this obj.
                             If returns false, aborts send.
     at_msg_send(self, msg, to_obj=None, **kwargs) - called when this objects
                             sends a message to someone via self.msg().

     return_appearance(looker) - describes this object. Used by "look"
                                 command by default
     at_desc(looker=None)      - called by 'look' whenever the
                                 appearance is requested.
     at_get(getter)            - called after object has been picked up.
                                 Does not stop pickup.
     at_drop(dropper)          - called when this object has been dropped.
     at_say(speaker, message)  - by default, called if an object inside this
                                 object speaks

    """

    pass
