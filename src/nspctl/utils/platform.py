import sys
import platform


def is_linux():
    """
    Simple function to return if a host is Linux or not.
    """
    return sys.platform.startswith("linux")


def get_arch():
    """
    Simple function to return the architecture
    """
    return platform.machine()
