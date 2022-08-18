"""
Input functions

Input functions are always called from the client (they handle server
input, hence the name).

This module is loaded by being included in the
`settings.INPUT_FUNC_MODULES` tuple.

All *global functions* included in this module are considered
input-handler functions and can be called by the client to handle
input.

An input function must have the following call signature:

    cmdname(session, *args, **kwargs)

Where session will be the active session and *args, **kwargs are extra
incoming arguments and keyword properties.

A special command is the "default" command, which is will be called
when no other cmdname matches. It also receives the non-found cmdname
as argument.

    default(session, cmdname, *args, **kwargs)

"""

from commands.cmdhandler import cmdhandler
from evennia.server.inputfuncs import _IDLE_COMMAND


def text(session, *args, **kwargs):
    """
    Main text input from the client. This will execute a command
    string on the server.

    Args:
        session (Session): The active Session to receive the input.
        text (str): First arg is used as text-command input. Other
            arguments are ignored.

    """
    # from evennia.server.profiling.timetrace import timetrace
    # text = timetrace(text, "ServerSession.data_in")

    txt = args[0] if args else None

    # explicitly check for None since text can be an empty string, which is
    # also valid
    if txt is None:
        return
    # this is treated as a command input
    # handle the 'idle' command
    if txt.strip() in _IDLE_COMMAND:
        session.update_session_counters(idle=True)
        return
    if session.account:
        # nick replacement
        puppet = session.puppet
        if puppet:
            txt = puppet.nicks.nickreplace(
                txt, categories=("inputline", "channel"), include_account=True
            )
        else:
            txt = session.account.nicks.nickreplace(
                txt, categories=("inputline", "channel"), include_account=False
            )
    kwargs.pop("options", None)
    cmdhandler(session, txt, callertype="session", session=session, **kwargs)
    session.update_session_counters()
