import logging
import os
import re

from .path import which
from .cmd import run_cmd

logger = logging.getLogger(__name__)


def systemd_booted():
    """
    Check if systemd is booted
    """
    try:
        sdb = bool(os.stat("/run/systemd/system"))
    except OSError:
        sdb = False

    return sdb


def systemd_offline():
    """
    Check if systemd is offline
    """
    sdo = not systemd_booted() and which("systemctl")
    return sdo


def systemd_version():
    """
    Return systemd version
    """
    cmd = "systemctl --version"
    stdout = run_cmd(cmd, is_shell=True)["stdout"]
    outstr = str(stdout)
    try:
        sdv = int(re.search(r"\w+ ([0-9]+)", outstr.splitlines()[0]).group(1))
    except (AttributeError, IndexError, ValueError):
        logger.error(
            "Unable to determine systemd version from systemctl "
            "--version, output follows:\n%s",
            outstr,
        )
        return None

    return sdv
