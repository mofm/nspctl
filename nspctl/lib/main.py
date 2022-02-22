import argparse

from nspctl import _nspctl
from nspctl.lib.output import nprint


# Create a decorator pattern that maintains a registry
def makeregistrar():
    """
    Decorator that keeps track of tagged functions
    """
    registry = {}

    def registrar(func):
        """
        Store the function pointer
        """
        registry[func.__name__] = func
        # normally a decorator returns a wrapped function,
        # but here we return func unmodified, after registering it
        return func
    registrar.all = registry
    return registrar


# Create the decorator
command = makeregistrar()


class NspctlCmd(object):
    """
    NspctlCmd object
    """

    def __init__(self):
        self.parser = None
        self.cmd = None
        self.resp_string = None

    def setup_parser(self, _parser):
        """
        Sets the class variable to what is passed in
        """
        self.parser = _parser

    def action(self, args):
        """
        Calls the function
        """
        if self.cmd is not None:
            return False

        func = args['func']
        del args['func']

        self.cmd = func(args=args)
        self.resp_string = self.run_action(self.cmd, args)

        return True

    def run_action(self, cmd, args):
        """
        Run the function from _nspctl.py
        """
        del args['subcommand']

        cmd = cmd.lstrip("-").replace("-", "_")
        method = getattr(_nspctl, cmd)
        result = method(*args)
        fancy_result = nprint(result)

        return fancy_result

    def get_result(self):
        """
        Returns the response
        """
        if self.resp_string is None:
            raise Exception("Call action function first")

        return self.resp_string

    @command
    def info(self, args=None, subparsers=None):
        """
        Returns container information
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("info")
            sp.add_argument("name")
            sp.set_defaults(func=self.info)
            return
        args = 'info'
        return args

    @command
    def list_all(self, args=None, subparsers=None):
        """
        Returns all installed Containers
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("list-all", aliases=['lsa'])
            sp.set_defaults(func=self.list_all)
            return

        args = 'list-all'
        return args

    @command
    def list_running(self, args=None, subparsers=None):
        """
        Returns running Containers
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("list-running", aliases=['lsr', 'list'])
            sp.set_defaults(func=self.list_running)
            return

        args = 'list-running'
        return args

    @command
    def list_stopped(self, args=None, subparsers=None):
        """
        Returns stopped Containers
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("list-stopped", aliases=['lss'])
            sp.set_defaults(func=self.list_stopped)
            return

        args = 'list-stopped'
        return args

    @command
    def start(self, args=None, subparsers=None):
        """
        Start the container
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("start")
            sp.add_argument("name")
            sp.set_defaults(func=self.start)
            return

        args = 'start'
        return args

    @command
    def stop(self, args=None, subparsers=None):
        """
        Stop the container
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("stop")
            sp.add_argument("name")
            sp.set_defaults(func=self.stop)
            return

        args = 'stop'
        return args

    @command
    def poweroff(self, args=None, subparsers=None):
        """
        A clean shutdown to the container
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("poweroff")
            sp.add_argument("name")
            sp.set_defaults(func=self.poweroff)
            return

        args = 'poweroff'
        return args

    @command
    def terminate(self, args=None, subparsers=None):
        """
        Kill all processes in the container
        Not a clean shutdown
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("terminate")
            sp.add_argument("name")
            sp.set_defaults(func=self.terminate)
            return

        args = 'terminate'
        return args

    @command
    def reboot(self, args=None, subparsers=None):
        """
        Reboot the container
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("reboot")
            sp.add_argument("name")
            sp.set_defaults(func=self.reboot)
            return

        args = 'reboot'
        return args

    @command
    def enable(self, args=None, subparsers=None):
        """
        Set the named container to be launched at boot
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("enable")
            sp.add_argument("name")
            sp.set_defaults(func=self.enable)
            return

        args = 'enable'
        return args

    @command
    def disable(self, args=None, subparsers=None):
        """
        Set the named container disable at boot
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("disable")
            sp.add_argument("name")
            sp.set_defaults(func=self.disable)
            return

        args = 'disable'
        return args

    @command
    def remove(self, args=None, subparsers=None):
        """
        Remove the named container
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("remove")
            sp.add_argument("name")
            sp.set_defaults(func=self.remove)
            return

        args = 'remove'
        return args

    @command
    def shell(self, args=None, subparsers=None):
        """
        logins container shell
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("shell")
            sp.add_argument("name")
            sp.set_defaults(func=self.shell)
            return

        args = 'shell'
        return args

    @command
    def pull_raw(self, args=None, subparsers=None):
        """
        Execute a ``machinectl pull-raw`` to download a .qcow2 or raw disk image
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("pull-raw")
            sp.add_argument("url")
            sp.add_argument("name")
            sp.add_argument("verify", nargs="?", const=False)
            sp.set_defaults(func=self.pull_raw)
            return

        args = 'pull_raw'
        return args

    @command
    def pull_tar(self, args=None, subparsers=None):
        """
        Execute a ``machinectl pull-tar`` to download a .tar container image
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("pull-tar")
            sp.add_argument("url")
            sp.add_argument("name")
            sp.add_argument("verify", nargs="?", const=False)
            sp.set_defaults(func=self.pull_tar)
            return

        args = 'pull_tar'
        return args

    @command
    def pull_dkr(self, args=None, subparsers=None):
        """
        Execute a ``machinectl pull-dkr`` to download a docker image
        All parameters are mandatory
        """
        if subparsers is not None:
            sp = subparsers.add_parser("pull-dkr")
            sp.add_argument("url")
            sp.add_argument("name")
            sp.add_argument("index")
            sp.set_defaults(func=self.pull_dkr)
            return

        args = 'pull_dkr'
        return args
