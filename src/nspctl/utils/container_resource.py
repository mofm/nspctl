import logging
import os
import pipes
import functools
from contextlib import ExitStack

from .args import clean_kwargs
from ..lib.namespace import all_ns
from .cmd import run_cmd, popen

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
    Common logic function for running containers
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
        full_cmd = ""
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

    try:
        with ExitStack() as stack:
            for ns in all_ns(pid):
                stack.enter_context(ns)

            ret = run_cmd(full_cmd, is_shell=is_shell)

            return ret
    except IOError as exc:
        raise Exception("Unable to run command: {}".format(exc))


@_validate
def cont_cpt(
        pid,
        source,
        dest,
        state,
        container_type=None,
        exec_driver=None,
        overwrite=False,
        makedirs=False,
):
    """
    Common logic copying files to containers
    """
    if state != "running":
        raise Exception("Container is not running")

    source_dir, source_name = os.path.split(source)

    if not os.path.isabs(source):
        raise Exception("Source path must be absolute")
    elif not os.path.exists(source):
        raise Exception("Source file {} does not exist".format(source))
    elif not os.path.isfile(source):
        raise Exception("Source must be regular file")

    if not os.path.isabs(dest):
        raise Exception("Destination path must be absolute")
    if (
        cont_run(pid, "test -d {}".format(dest),
                 container_type=container_type,
                 exec_driver=exec_driver,
                 is_shell=True)["returncode"]
        == 0
    ):
        dest = os.path.join(dest, source_name)
    else:
        dest_dir, dest_name = os.path.split(dest)
        if (
            cont_run(pid, "test -d {}".format(dest_dir),
                     container_type=container_type,
                     exec_driver=exec_driver,
                     is_shell=True)["returncode"]
            != 0
        ):
            if makedirs:
                res = cont_run(pid, "mkdir -p {}".format(dest_dir),
                               container_type=container_type,
                               exec_driver=exec_driver,
                               is_shell=True)
                if res["returncode"] != 0:
                    error = (
                        "Unable to create destination directory {} "
                        "in container".format(dest_dir)
                    )
                    if res["stderr"]:
                        error += ": {}".format(res["stderr"])
                    raise Exception(error)
            else:
                raise Exception("Directory does not exist in container")

    if (
        not overwrite and
        cont_run(pid, "test -e {}".format(dest),
                 container_type=container_type,
                 exec_driver=exec_driver,
                 is_shell=True)["returncode"]
        == 0
    ):
        raise Exception(
            "Destination path {} already exists. Use overwrite=True to "
            "overwrite it".format(dest)
        )

    if exec_driver == "nsenter":
        copy_cmd = 'cat "{}" | {} env -i {} tee "{}"'.format(
            source, _nsenter(pid), PATH, dest)
        cmd_exec = run_cmd(copy_cmd, is_shell=True)
        if cmd_exec["returncode"] != 0:
            raise Exception("Failed copying the file!")
        else:
            return "Copy command completed!"


@_validate
def con_init(
        pid,
        state,
        container_type=None,
        exec_driver=None,
        is_shell=None,
        keep_env=None,
):
    """
    Detect container init systems
    """
    if state != "running":
        raise Exception("Container is not running")

    cmd = "stat /run/systemd/system"

    if (
        cont_run(
            pid,
            cmd,
            container_type=container_type,
            exec_driver=exec_driver,
            is_shell=is_shell,
            keep_env=keep_env
        )["returncode"]
        == 0
    ):
        return True
    else:
        return False


@_validate
def login_shell(
        pid,
        container_type=None,
        exec_driver=None,
        is_shell=None,
):
    """
    Common login shell function
    """
    if exec_driver == "nsenter":
        shell_cmd = "/bin/sh -l"
        full_cmd = "env -i {} {}".format(PATH, shell_cmd)
        try:
            with ExitStack() as stack:
                for ns in all_ns(pid):
                    stack.enter_context(ns)

                popen(full_cmd, is_shell=is_shell)
        except IOError as exc:
            raise Exception("Unable to login shell: {}".format(exc))
    else:
        raise Exception("no valid exec_driver")
