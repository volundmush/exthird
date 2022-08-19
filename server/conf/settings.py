r"""
Evennia settings file.

The available options are found in the default settings file found
here:

/home/volund/PycharmProjects/evennia/evennia/settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Exalted MUSH"

# more database apps
INSTALLED_APPS.extend([
    "world.plays",
    "world.story"
])

SYSTEMS = [
    "world.systems.PlaySystem"
]

MULTISESSION_MODE = 3

CMD_IGNORE_PREFIXES = ""

SERVER_SESSION_CLASS = "server.conf.serversession.ServerSession"

BASE_PLAY_TYPECLASS = "world.plays.plays.DefaultPlay"
CMDSET_PLAY = "commands.cmdsets.PlayCmdSet"

# The number of characters that can be logged-in per account simultaneously. Builder permissions override this.
# Set to None for unlimited.
PLAYS_PER_ACCOUNT = None

# Number of seconds a Play session can go without Sessions before it's
# forcibly terminated.
PLAY_TIMEOUT_SECONDS = 30.0



######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
