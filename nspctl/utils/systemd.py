import logging
import os
import re
import subprocess

import nspctl.utils.path

logger = logging.getLogger(__name__)


def systemd_booted():
    try:
        sdb = bool(os.stat("/run/systemd/system"))
    except OSError:
        sdb = False

    return sdb


def systemd_offline():
    sdb = not systemd_booted() and nspctl.utils.path.which("systemctl")
    return sdb


def systemd_version():
    stdout = subprocess.Popen(
        ["systemctl", "--version"],
        close_fds=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).communicate()[0]
    outstr = str(stdout)
    try:
        sdb = int(re.search(r"\w+ ([0-9]+)", outstr.splitlines()[0]).group(1))
    except (AttributeError, IndexError, ValueError):
        logger.error(
            "Unable to determine systemd version from systemctl "
            "--version, output follows:\n%s",
            outstr,
        )
        return None

    return sdb
