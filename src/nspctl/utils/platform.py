import sys


def is_linux():
    """
    Simple function to return if a host is Linux or not.
    """
    return sys.platform.startswith("linux")
