import argparse

from nspctl import _nspctl


# Create a decorator pattern that maintains a registry
def makeregistrar():
    """Decorator that keeps track of tagged functions."""
    registry = {}

    def registrar(func):
        """Store the function pointer."""
        registry[func.__name__] = func
        # normally a decorator returns a wrapped function,
        # but here we return func unmodified, after registering it
        return func
    registrar.all = registry
    return registrar


# Create the decorator
command = makeregistrar()

class NspctlCmd(object):

    def __init__(self):
        self.parser = None
        self.cmd = None
        self.resp_string = None

    def setup_parser(self, _parser):
        self.parser = _parser


    def action(self, args):
        if self.cmd is not None:
            return False

        func = args['func']
        del args['func']

        self.cmd = func(args=args)
        self.resp_string = self.run_action(self.cmd, args)

        return True

    def run_action(self, cmd, args):

        del args['subcommand']

        cmd = cmd.lstrip("-").replace("-", "_")
        method = getattr(_nspctl, cmd)
        result = method(**args)

        if isinstance(result, list):
            result = ' \n'.join(result)

        return result

    def get_result(self):
        if self.resp_string is None:
            raise Exception("Call action function first")

        return self.resp_string

    @command
    def help(self, args=None, subparsers=None):
        if subparsers is not None:
            sp = subparsers.add_parser("help", aliases=['h'])
            sp.set_defaults(func=self.help)
            return

        args = 'help'
        return args

    @command
    def info(self, args=None, subparsers=None):
        if subparsers is not None:
            sp = subparsers.add_parser("info")
            sp.add_argument("name")
            sp.set_defaults(func=self.info)
            return
        args = 'info'
        return args

    @command
    def list_all(self, args=None, subparsers=None):
        if subparsers is not None:
            sp = subparsers.add_parser("list-all")
            sp.set_defaults(func=self.list_all)
            return

        args = 'list-all'
        return args

    @command
    def list_running(self, args=None, subparsers=None):
        if subparsers is not None:
            sp = subparsers.add_parser("list-running")
            sp.set_defaults(func=self.list_running)
            return

        args = 'list-running'
        return args

    @command
    def list_stopped(self, args=None, subparsers=None):
        if subparsers is not None:
            sp = subparsers.add_parser("list-stopped")
            sp.set_defaults(func=self.list_stopped)
            return

        args = 'list-stopped'
        return args
