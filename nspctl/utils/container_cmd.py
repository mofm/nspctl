import logging
import os
import pipes
import functools

from nspctl.utils.cmd import run_cmd
from nspctl.utils.args import clean_kwargs

logger = logging.getLogger(__name__)

PATH = "PATH=/bin:/usr/bin:/sbin:/usr/sbin:/opt/bin:/usr/local/bin:/usr/local/sbin"


def _validate(wrapped):
    """
    Decorator for common function argument validation
    """

    @functools.wraps(wrapped)
    def wrapper(*args, **kwargs):
        container_type = kwargs.get("container_type")
        exec_driver = kwargs.get("exec_driver")
        valid_driver = {
            "docker": ("lxc-attach", "nsenter", "docker-exec"),
            "lxc": ("lxc-attach",),
            "nspawn": ("nsenter",),
        }
        if container_type not in valid_driver:
            raise (
                "Invalid container type '{}'. Valid types are: {}".format(
                    container_type, ", ".join(sorted(valid_driver))
                )
            )
        if exec_driver not in valid_driver[container_type]:
            raise (
                "Invalid command execution driver. Valid drivers are: {}".format(
                    ", ".join(valid_driver[container_type])
                )
            )

        return wrapped(*args, **clean_kwargs(**kwargs))

    return wrapper


def _nsenter(pid):
    """
    Return the nsenter command to attach to the named container
    """
    return "nsenter --target {} --mount --uts --ipc --net --pid".format(pid)


@_validate
def cont_run(
    pid,
    cmd,
    container_type=None,
    exec_driver=None,
    is_shell=None,
    keep_env=None,
):
    """
    :param cmd:
    :param container_type:
    :param exec_driver:
    :param keep_env:
    :param pid:
    :param is_shell:
    :return:
    """

    if keep_env is None or isinstance(keep_env, bool):
        to_keep = []
    elif not isinstance(keep_env, (list, tuple)):
        try:
            to_keep = keep_env.split(",")
        except AttributeError:
            logger.warning("Invalid keep_env value, ignoring")
            to_keep = []
    else:
        to_keep = keep_env

    if exec_driver == "nsenter":
        full_cmd = "nsenter --target {} --mount --uts --ipc --net --pid -- ".format(pid)
        if keep_env is not True:
            full_cmd += "env -i "
            if "PATH" not in to_keep:
                full_cmd += "{} ".format(PATH)
        full_cmd += " ".join(
            [
                "{}={}".format(x, pipes.quote(os.environ[x]))
                for x in to_keep
                if x in os.environ
            ]
        )
        full_cmd += " {}".format(cmd)

    proc = run_cmd(
        full_cmd,
        is_shell=is_shell,
        cwd=None
    )

    return proc
