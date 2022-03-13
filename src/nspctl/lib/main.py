import argparse
import logging
import sys

from ..utils.platform import is_linux
from ..utils.systemd import systemd_booted, systemd_version
from .output import nprint
from .. import _nspctl, __version__
from .usage import nspctl_usage

logger = logging.getLogger(__name__)


def check_system():
    """
    Only work on systems that have been booted with systemd
    """
    if is_linux() and systemd_booted():
        if systemd_version() is None:
            logger.error("nspctl: Unable to determine systemd version")
        else:
            return True
    return False


no_args = {
    "usage": {
        "aliases": ["use"],
        "help": "Display this usage information and exit",
    },
    "version": {
        "aliases": ["v"],
        "help": "Output version information and exit",
    },
    "list-all": {
        "aliases": ["lsa"],
        "help": "List all containers",
    },
    "list-stopped": {
        "aliases": ["lss"],
        "help": "List stopped containers",
    },
    "list-running": {
        "aliases": ["lsr", "ls", "list"],
        "help": "List currently running containers",
    },
    "clean": {
        "help": "Remove hidden VM or container images",
    },
    "clean-all": {
        "help": "Remove all VM or container images"
    },
}

one_args = {
    "info": {
        "help": "Show properties of container",
    },
    "start": {
        "help": "Start a container as system service",
    },
    "stop": {
        "help": "Stop a container. Shutdown cleanly",
    },
    "reboot": {
        "help": "Reboot a container",
    },
    "terminate": {
        "help": "Immediately terminates container without cleanly shutting it down",
    },
    "poweroff": {
        "help": "Poweroff a container. Shutdown cleanly",
    },
    "enable": {
        "aliases": ["en"],
        "help": "Enable a container as a system service at system boot",
    },
    "disable": {
        "aliases": ["dis"],
        "help": "Disable a container as a system service at system boot",
    },
    "remove": {
        "aliases": ["rm"],
        "help": "Remove a container completely",
    },
    "shell": {
        "aliases": ["sh"],
        "help": "Open an interactive shell session in a container",
    },
}

pull_args = {
    "pull-raw": {
        "help": "Downloads a .raw container from the specified URL (qcow2 or compressed as gz, xz, bz2)",
    },
    "pull-tar": {
        "help": "Downloads a .tar container image from the specified URL (tar, tar.gz, tar.xz, tar.bz2)",
    },
}

import_args = {
    "import-raw": {
        "help": "Execute a `machinectl import-raw` to import a .qcow2 or raw disk image",
    },
    "import-tar": {
        "help": "Execute a `machinectl import-tar` to import a .tar container image",
    },
    "import-fs": {
        "help": "Execute a `machinectl import-fs` to import a directory image",
    },
}


def parser_opts():
    """
    Common parser function
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    for myopt, kwargs in no_args.items():
        sargs = [myopt]
        sp = subparsers.add_parser(*sargs, **kwargs)
        sp.set_defaults(func=myopt)

    for myopt, kwargs in one_args.items():
        sargs = [myopt]
        sp = subparsers.add_parser(*sargs, **kwargs)
        sp.add_argument("name")
        sp.set_defaults(func=myopt)

    for myopt, kwargs in pull_args.items():
        sargs = [myopt]
        sp = subparsers.add_parser(*sargs, **kwargs)
        sp.add_argument("url")
        sp.add_argument("name")
        sp.add_argument("verify", nargs="?", const=False)
        sp.set_defaults(func=myopt)

    for myopt, kwargs in import_args.items():
        sargs = [myopt]
        sp = subparsers.add_parser(*sargs, **kwargs)
        sp.add_argument("image")
        sp.add_argument("name")
        sp.set_defaults(func=myopt)

    # rename arguments
    sp = subparsers.add_parser("rename",
                               help="Renames a container or VM image",
                               )
    sp.add_argument("name")
    sp.add_argument("newname")
    sp.set_defaults(func="rename")

    # bootstrap arguments
    sp = subparsers.add_parser("bootstrap",
                               help="Bootstrap a container from package servers",
                               )
    sp.add_argument("name")
    sp.add_argument("dist")
    sp.add_argument("version", nargs="?")
    sp.set_defaults(func="bootstrap")

    # copy_to arguments
    sp = subparsers.add_parser("copy-to",
                               aliases=["cpt"],
                               help="Copies files from the host system into a running container",
                               )
    sp.add_argument("name")
    sp.add_argument("source")
    sp.add_argument("dest")
    sp.set_defaults(func="copy-to")

    # exec arguments
    sp = subparsers.add_parser("exec",
                               help="Run a new command in a running container",
                               )
    sp.add_argument("name")
    sp.add_argument("cmd")
    sp.set_defaults(func="exec-run")

    vargs = parser.parse_args()
    return vargs


class NspctlCmd(object):
    """
    NspctlCmd object
    """

    def __init__(self):
        self.cmd = None
        self.resp_string = None

    def action(self, args):
        """
        Calls the function
        """
        if self.cmd is not None:
            return False

        self.cmd = args['func']
        del args['func']
        self.resp_string = self.run_action(self.cmd, args)

        return True

    def run_action(self, cmd, args):
        """
        Run the function from _nspctl.py
        """
        cmd = cmd.lstrip("-").replace("-", "_")
        method = getattr(_nspctl, cmd)
        result = method(**args)
        fancy_result = nprint(result)

        return fancy_result

    def get_result(self):
        """
        Returns the response
        """
        if self.resp_string is None:
            raise Exception("Call action function first")

        return self.resp_string


def nspctl_main(args=None):
    """
    command arguments (default: usage)
    """
    if args is None:
        args = sys.argv[1:]

    args = parser_opts()
    args_map = vars(args)

    if not args_map or args_map['func'] in ('usage', None):
        nspctl_usage()
    elif args_map['func'] == "version":
        print(__version__ + "\n")
    else:
        nsp = NspctlCmd()
        nsp.action(args_map)
        rev = nsp.get_result()
        print(rev)
