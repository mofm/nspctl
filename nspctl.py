import logging
import os
import re

from nspctl.utils.systemd import systemd_booted, systemd_version
from nspctl.utils.platform import is_linux
from nspctl.utils.cmd import run_cmd
from nspctl.utils.args import invalid_kwargs, clean_kwargs
from nspctl.utils.container_cmd import cont_run

logger = logging.getLogger(__name__)

__virtualname__ = "nspawn"
WANT = "/etc/systemd/system/multi-user.target.wants/systemd-nspawn@{0}.service"
EXEC_DRIVER = "nsenter"


def __virtual__():
    """
    Only work on systems that have been booted with systemd
    """
    if is_linux() and systemd_booted():
        if systemd_version() is None:
            logger.error("nspctl: Unable to determine systemd version")
        else:
            return __virtualname__
    return (
        False,
        "The nspctl command failed to load: "
        "only work on systems that have been booted with systemd.",
    )


def _sd_version():
    """
    Returns systemd version
    """
    return systemd_version()


def _ensure_exists(name):
    if not exists(name):
        return "Container '{}' does not exist".format(name)


def _root(name="", all_roots=False):
    """
    Return the container root directory. Starting with systemd 219, new
    images go into /var/lib/machines.
    """
    if _sd_version() >= 219:
        if all_roots:
            return [
                os.path.join(x, name)
                for x in ("/var/lib/machines", "/var/lib/container")
            ]
        else:
            return os.path.join("/var/lib/machines", name)
    else:
        ret = os.path.join("/var/lib/container", name)
        if all_roots:
            return [ret]
        else:
            return ret


def _make_container_root(name):
    """
    Make the container root directory
    """
    path = _root(name)
    if os.path.exists(path):
        raise Exception("Container {} already exists".format(name))
    else:
        try:
            os.makedirs(path)
            return path
        except OSError as exc:
            raise exc(
                "Unable to make container root directory {}: {}".format(name, exc)
            )


def _ensure_running(name):
    """
    Raise an exception if the container does not exist
    """
    if state(name) == "running":
        return True
    else:
        return start(name)


def _ensure_systemd(version):
    """
    Raises an exception if the systemd version is not greater than the
    passed version.
    """
    try:
        version = int(version)
    except ValueError:
        return "Invalid version '{}'".format(version)

    try:
        installed = _sd_version()
        logger.debug("nspawn: detected systemd %s", installed)
    except (IndexError, ValueError):
        return "nspawn: Unable to get systemd version"

    if installed < version:
        return "This function requires systemd >= {} (Detected version: {}).".format(
                version, installed
            )


def list_all():
    """
    Lists all nspawn containers
    """
    ret = []
    con_all = _machinectl("list-images")["stdout"]
    if _sd_version() >= 219 and con_all is not None:
        for line in con_all.splitlines():
            try:
                ret.append(line.split()[0])
            except IndexError:
                continue
    else:
        rootdir = _root()
        try:
            for dirname in os.listdir(rootdir):
                if os.path.isdir(os.path.join(rootdir, dirname)):
                    ret.append(dirname)
        except OSError:
            pass
    return ret


def list_running():
    """
    Lists running nspawn containers
    """
    ret = []
    con_running = _machinectl("list")["stdout"]
    if con_running is not None:
        for line in con_running.splitlines():
            try:
                ret.append(line.split()[0])
                return sorted(ret)
            except IndexError:
                pass
    else:
        return ret


def list_stopped():
    """
    Lists stopped nspawn containers
    """
    return sorted(set(list_all()) - set(list_running()))


def exists(name):
    """
    Return true if the named container exists
    """
    if name in list_all():
        return True
    else:
        return False


def _machinectl(cmd):
    """
    Helper function to run machinectl
    """
    prefix = "machinectl --no-legend --no-pager"
    return run_cmd("{} {}".format(prefix, cmd), is_shell=True)


def _run(
    name,
    cmd,
    is_shell=None,
    output=None,
    preserve_state=False,
    keep_env=None,
):
    """
    Common logic for run functions
    """
    orig_state = state(name)
    pid = con_pid(name)
    exc = None
    try:
        ret = cont_run(
            pid,
            cmd,
            container_type=__virtualname__,
            exec_driver=EXEC_DRIVER,
            is_shell=is_shell,
            keep_env=keep_env
        )
    finally:
        # Make sure we stop the container if necessary, even if an exception
        # was raised.
        if preserve_state and orig_state == "stopped" and state(name) != "stopped":
            stop(name)

    c_output = {"stdout": "stdout", "stderr": "stderr", "returncode": "returncode"}
    if output is not None:
        output = c_output[output]
        return ret[output]
    else:
        return ret


def con_pid(name):
    """
    Returns the PID of a container
    """
    try:
        return int(info(name).get("PID"))
    except (TypeError, ValueError) as exc:
        raise exc(
            "Unable to get PID for container '{}': {}".format(name, exc)
        )


def run(
    name,
    cmd,
    is_shell=True,
    preserve_state=True,
    keep_env=None,
):
    """
    Run command within a container
    """
    return _run(
        name,
        cmd,
        is_shell=is_shell,
        preserve_state=preserve_state,
        keep_env=keep_env,
    )


def run_stdout(
    name,
    cmd,
    is_shell=True,
    preserve_state=True,
    keep_env=None,
):
    """
    Run command within a container and response output stdout
    """
    return _run(
        name,
        cmd,
        output="stdout",
        is_shell=is_shell,
        preserve_state=preserve_state,
        keep_env=keep_env,
    )


def run_stderr(
    name,
    cmd,
    is_shell=True,
    preserve_state=True,
    keep_env=None,
):
    """
    Run command within a container and response output stderr
    """
    return _run(
        name,
        cmd,
        output="stderr",
        is_shell=is_shell,
        preserve_state=preserve_state,
        keep_env=keep_env,
    )


def retcode(
    name,
    cmd,
    is_shell=True,
    preserve_state=True,
    keep_env=None,
):
    """
    Run command within a container and response returncode
    """
    return _run(
        name,
        cmd,
        output="returncode",
        is_shell=is_shell,
        preserve_state=preserve_state,
        keep_env=keep_env,
    )


def state(name):
    """
    Return state of container (running or stopped)
    """
    try:
        cmd = "show {} --property=State".format(name)
        return _machinectl(cmd)["stdout"].split("=")[-1]
    except IndexError:
        return "stopped"


def info(name, **kwargs):
    """
    Return info about a container
    """
    kwargs = clean_kwargs(**kwargs)
    start_ = kwargs.pop("start", False)
    if kwargs:
        invalid_kwargs(kwargs)

    if not start_:
        _ensure_running(name)
    elif name not in list_running():
        start(name)

    # Have to parse 'machinectl status' here since 'machinectl show' doesn't
    # contain IP address info or OS info. *shakes fist angrily*
    c_info = _machinectl("status {}".format(name))
    if c_info["returncode"] != 0:
        return "Unable to get info for container '{}'".format(name)
    # Better human-readable names. False means key should be ignored.
    key_name_map = {
        "Iface": "Network Interface",
        "Leader": "PID",
        "Service": False,
        "Since": "Running Since",
    }
    ret = {}
    kv_pair = re.compile(r"^\s+([A-Za-z]+): (.+)$")
    tree = re.compile(r"[|`]")
    lines = c_info["stdout"].splitlines()
    multiline = False
    cur_key = None
    for idx, line in enumerate(lines):
        match = kv_pair.match(line)
        if match:
            key, val = match.groups()
            # Get a better key name if one exists
            key = key_name_map.get(key, key)
            if key is False:
                continue
            elif key == "PID":
                try:
                    val = val.split()[0]
                except IndexError:
                    pass
            cur_key = key
            if multiline:
                multiline = False
            ret[key] = val
        else:
            if cur_key is None:
                continue
            if tree.search(lines[idx]):
                # We've reached the process tree, bail out
                break
            if multiline:
                ret[cur_key].append(lines[idx].strip())
            else:
                ret[cur_key] = [ret[key], lines[idx].strip()]
                multiline = True
    return ret


def start(name):
    """
    Start the named container
    """
    if _sd_version() >= 219:
        ret = _machinectl("start {}".format(name))
    else:
        cmd = "systemctl start systemd-nspawn@{}".format(name)
        ret = run_cmd(cmd, is_shell=True)

    if ret["returncode"] != 0:
        return False

    return True


def stop(name, kill=False):
    """
    This is a compatibility function which provides the logic for
    poweroff and terminate.
    """
    if _sd_version() >= 219:
        if kill:
            action = "terminate"
        else:
            action = "poweroff"
        ret = _machinectl("{} {}".format(action, name))
    else:
        cmd = "systemctl stop systemd-nspawn@{}".format(name)
        ret = run_cmd(cmd, is_shell=True)

    if ret["returncode"] != 0:
        return False

    return True