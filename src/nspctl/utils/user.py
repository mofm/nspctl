import logging
import os
import pwd

logger = logging.getLogger(__name__)


def get_uid(user=None):
    """
    Get the uid a given username or
    no username given the current username
    will be returned.
    """
    if user is None:
        try:
            return os.geteuid()
        except AttributeError:
            return None
    else:
        try:
            return pwd.getpwnam(user).pw_uid
        except KeyError:
            return None
