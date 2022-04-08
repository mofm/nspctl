import logging
import ctypes
import ctypes.util
import errno
import os
from pathlib import Path
from contextlib import ExitStack


logger = logging.getLogger(__name__)

NAMESPACES = frozenset(["mnt", "uts", "ipc", "net", "pid", "user", "cgroup"])


class NsEnter(object):
    """
    Entering namespace class
    """
    _libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

    def __init__(self, pid, ns_type, proc="/proc"):
        if ns_type not in NAMESPACES:
            raise ValueError("ns_type must be one of {}".format(", ".join(NAMESPACES)))

        self.pid = pid
        self.ns_type = ns_type
        self.proc = proc

        try:
            pid = int(pid)
            self.target_fd = self._nsfd(pid, ns_type).open()
        except ValueError:
            self.target_fd = Path(pid).open()

        self.target_fileno = self.target_fd.fileno()
        self.parent_fd = self._nsfd("self", ns_type).open()
        self.parent_fileno = self.parent_fd.fileno()

    __init__.__annotations__ = {'pid': str, 'ns_type': str}

    def _nsfd(self, pid, ns_type):
        """
        Path instance pointing at the
        requested namespace entry
        """
        return Path(self.proc) / str(pid) / "ns" / ns_type

    _nsfd.__annotations__ = {'process': str, 'ns_type': str, 'return': Path}

    def _close_files(self):
        """
        close open file handles
        """
        try:
            self.target_fd.close()
        except:
            pass

        if self.parent_fd is not None:
            self.parent_fd.close()

    def __enter__(self):
        logger.debug("Entering {} namespace {}".format(self.ns_type, self.pid))

        if self._libc.setns(self.target_fileno, 0) == -1:
            exc = ctypes.get_errno()
            self._close_files()
            raise OSError(exc, errno.errorcode[exc])

    def __exit__(self, type, value, tb):
        logger.debug("Leaving {} namespace {}".format(self.ns_type, self.pid))

        if self._libc.setns(self.parent_fileno, 0) == -1:
            exc = ctypes.get_errno()
            self._close_files()
            raise OSError(exc, errno.errorcode[exc])

        self._close_files()


def _is_usable_namespace(target, ns_type):
    """
    Check target namespace
    """
    ns_path = lambda t, n: os.path.join("/proc", t, "ns", n)

    if not os.path.exists(ns_path(target, ns_type)):
        return False

    # It is not permitted to use setns(2) to reenter the caller's
    # current user namespace; see setns(2) man page for more details.
    if ns_type == "user":
        if os.stat(ns_path(target, ns_type)).st_ino == os.stat(ns_path("self", ns_type)).st_ino:
            return False

    return True


def all_namespaces(target, command=None):
    """
    Enter all the namespaces
    """
    if not command:
        command = ["/bin/sh"]

    try:
        with ExitStack() as stack:
            namespaces = []
            for ns in NAMESPACES:
                if _is_usable_namespace(target, ns):
                    namespaces.append(NsEnter(target, ns))

            for ns in namespaces:
                stack.enter_context(ns)

            os.execlp(command[0], *command)
    except IOError as exc:
        raise Exception("Unable to access PID: {}".format(exc))
