from itertools import chain
from django.core.exceptions import ObjectDoesNotExist
from evennia.utils.utils import make_iter, to_str, logger
from twisted.internet.defer import inlineCallbacks, returnValue


class MixObj:
