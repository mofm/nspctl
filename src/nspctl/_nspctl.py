import errno
import logging
import os
import re
import functools
import shutil

from nspctl.utils.systemd import systemd_booted, systemd_version
from nspctl.utils.platform import is_linux
from nspctl.utils.cmd import run_cmd, popen
from nspctl.utils.args import invalid_kwargs, clean_kwargs
from nspctl.utils.container_resource import cont_run, copy_to, con_init, login_shell
from nspctl.utils.path import which
from nspctl.lib.functools import alias_function
from nspctl.utils.user import get_uid

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


def _ensure_exists(wrapped):
    """
    Decorator to ensure that the named container exists
    """

    @functools.wraps(wrapped)
    def check_exits(name, *args, **kwargs):
        if not exists(name):
            raise Exception("Container '{}' does not exist".format(name))
        return wrapped(name, *args, **clean_kwargs(**kwargs))

    return check_exits


def _check_useruid(wrapped):
    """
    Decorator check to user has root privileges
    """
    @functools.wraps(wrapped)
    def check_uid(*args, **kwargs):
        if get_uid() != 0:
            raise Exception("This command requires root privileges!")
        return wrapped(*args, **clean_kwargs(**kwargs))

    return check_uid


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


def _build_failed(dest, name):
    """
    build failed function
    """
    try:
        shutil.rmtree(dest)
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            raise Exception(
                "Unable to cleanup container root directory {}".format(dest)
            )
    raise Exception("Container {} failed to build".format(name))


def _bootstrap_arch(name, **kwargs):
    """
    Bootstrap an Arch Linux container
    """
    if not which("pacstrap"):
        raise Exception(
            "pacstrap not found, is the arch-install-scripts package installed?"
        )
    dest = _make_container_root(name)
    cmd = "pacstrap -c -d {} base".format(dest)
    ret = run_cmd(cmd, is_shell=True)
    if ret["returncode"] != 0:
        _build_failed(dest, name)
    return ret


def _bootstrap_debian(name, **kwargs):
    """
    Bootstrap a Debian Linux container
    """
    if not which("debootstrap"):
        raise Exception(
            "debootstrap not found, is the debootstrap package installed?"
        )

    version = kwargs.get("version", False)
    if not version:
        version = "stable"

    releases = [
        "jessie",
        "stretch",
        "buster",
        "bullseye",
        "stable",
    ]
    if version not in releases:
        raise Exception(
            'Unsupported Debian version "{}". '
            'Only "stable" or "jessie" and newer are supported'.format(version)
        )

    dest = _make_container_root(name)
    cmd = "debootstrap --arch=amd64 {} {}".format(version, dest)
    ret = run_cmd(cmd, is_shell=True)
    if ret["returncode"] != 0:
        _build_failed(dest, name)
    return ret


def _bootstrap_ubuntu(name, **kwargs):
    """
    Bootstrap a Ubuntu Linux container
    """
    if not which("debootstrap"):
        raise Exception(
            "debootstrap not found, is the debootstrap package installed?"
        )

    version = kwargs.get("version", False)
    if not version:
        version = "focal"

    releases = [
        "xenial",
        "bionic",
        "focal",
    ]
    if version not in releases:
        raise Exception(
            'Unsupported Ubuntu version "{}". '
            '"xenial" and newer are supported'.format(version)
        )

    dest = _make_container_root(name)
    cmd = "debootstrap --arch=amd64 {} {}".format(version, dest)
    ret = run_cmd(cmd, is_shell=True)
    if ret["returncode"] != 0:
        _build_failed(dest, name)
    return ret


@_check_useruid
def bootstrap_container(name, dist=None, version=None):
    """
    Bootstrap a container from package servers
    """
    distro = [
        "debian",
        "ubuntu",
        "arch",
    ]

    if dist not in distro and dist is None:
        raise Exception(
            'Unsupported distribution "{}"'.format(dist)
        )
    try:
        return globals()["_bootstrap_{}".format(dist)](name, version=version)
    except KeyError:
        raise Exception('Unsupported distribution "{}"'.format(dist))


bootstrap = alias_function(bootstrap_container, "bootstrap")


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


@_ensure_exists
def _ensure_consystemd(name):
    """
    Detect container init systems:
    systemd or other init systems
    """
    orig_state = state(name)
    pid = con_pid(name)
    return con_init(
        pid,
        state=orig_state,
        container_type=__virtualname__,
        exec_driver=EXEC_DRIVER,
        is_shell=True,
        keep_env=True,
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
            except IndexError:
                pass

    return ret


# 'machinectl list' shows only running containers, so allow this to work as an
# alias to list_running
list = alias_function(list_running, "list")


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


@_ensure_exists
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


@_ensure_exists
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


@_ensure_exists
def state(name):
    """
    Return state of container (running or stopped)
    """
    try:
        cmd = "show {} --property=State".format(name)
        return _machinectl(cmd)["stdout"].split("=")[-1]
    except AttributeError:
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


@_ensure_exists
@_check_useruid
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


@_ensure_exists
@_check_useruid
def stop(name, kill=False):
    """
    This is a compatibility function which provides the logic for
    poweroff and terminate.
    """
    if _ensure_consystemd(name):
        if kill:
            action = "terminate"
        else:
            action = "poweroff"
        ret = _machinectl("{} {}".format(action, name))
    else:
        # systemd-nspawn does not stop another init system.
        # or "systemctl stop" command gives timeout.
        cmd = "poweroff"
        ret = run(name, cmd)

    if ret["returncode"] != 0:
        return False

    return True


def poweroff(name):
    """
    A clean shutdown to the container
    """
    return stop(name, kill=False)


def terminate(name):
    """
    Kill all processes in the container. Not a clean shutdown.
    """
    return stop(name, kill=True)


@_ensure_exists
@_check_useruid
def enable(name):
    """
    Set the named container to be launched at boot
    """
    cmd = "systemctl enable systemd-nspawn@{}".format(name)
    if run_cmd(cmd, is_shell=True)["returncode"] != 0:
        return False

    return True


@_ensure_exists
@_check_useruid
def disable(name):
    """
    Set the named container disable at boot
    """
    cmd = "systemctl disable systemd-nspawn@{}".format(name)
    if run_cmd(cmd, is_shell=True)["returncode"] != 0:
        return False

    return True


@_ensure_exists
@_check_useruid
def reboot(name):
    """
    reboot the container
    """
    if state(name) == "running":
        if _ensure_consystemd(name):
            ret = _machinectl("reboot {}".format(name))
        else:
            cmd = "reboot"
            ret = run(name, cmd)
    else:
        return start(name)

    if ret["returncode"] != 0:
        return False

    return True


@_ensure_exists
@_check_useruid
def remove(name, stop=False):
    """
    Remove the named container
    """
    if not stop and state(name) != "stopped":
        raise Exception("Cantainer '{}' is not stopped".format(name))

    def _failed_remove(name, exc):
        raise Exception("Unable to remove container '{}': '{}'".format(name, exc))

    if _sd_version() >= 219:
        ret = _machinectl("remove {}".format(name))
        if ret["returncode"] != 0:
            _failed_remove(name, ret["stderr"])
    else:
        try:
            shutil.rmtree(os.path.join(_root(), name))
        except OSError as exc:
            _failed_remove(name, exc)

    return True


@_ensure_exists
@_check_useruid
def con_copy(name, source, dest, overwrite=False, makedirs=False):
    """
    Copy a file from host in to a container
    """
    if _ensure_consystemd(name):
        ret = _machinectl("copy-to {} {} '{}'".format(name, source, dest))
        if ret["returncode"] != 0:
            raise Exception("Failed to copying file/s")
        else:
            return ret
    else:
        orig_state = state(name)
        pid = con_pid(name)
        ret = copy_to(
            pid,
            source,
            dest,
            state=orig_state,
            container_type=__virtualname__,
            exec_driver=EXEC_DRIVER,
            overwrite=overwrite,
            makedirs=makedirs,
        )
        return ret


@_ensure_exists
@_check_useruid
def shell(name):
    """
    login container shell
    """
    _ensure_running(name)
    if _ensure_consystemd(name):
        cmd = "machinectl shell '{}'".format(name)
        ret = popen(cmd, is_shell=True)
    else:
        pid = con_pid(name)
        ret = login_shell(
            pid,
            container_type=__virtualname__,
            exec_driver=EXEC_DRIVER,
            is_shell=True,
        )
    return True


def _pull_image(img_type, image, name, **kwargs):
    """
    Common logic function for pulling images
    """
    _ensure_systemd(219)
    if exists(name):
        raise Exception("Container '{}' already exists".format(name))
    if img_type in ("raw", "tar"):
        valid_kwargs = ("verify",)
    elif img_type == "dkr":
        valid_kwargs = ("index",)
    else:
        raise Exception("Unsupported image type '{}'".format(img_type))

    kwargs = clean_kwargs(**kwargs)
    bad_kwargs = {
        x: y
        for x, y in clean_kwargs(**kwargs).items()
        if x not in valid_kwargs
    }

    if bad_kwargs:
        invalid_kwargs(bad_kwargs)

    pull_opt = []
    if img_type in ("raw", "tar"):
        verify = kwargs.get("verify", False)
        if not verify:
            pull_opt.append("--verify=no")
        else:

            def _bad_verify():
                raise Exception(
                    "'verify' must be one of the following: signature, checksum"
                )

            try:
                verify = verify.lower()
            except AttributeError:
                _bad_verify()
            else:
                if verify not in ("signature", "checksum"):
                    _bad_verify()
                pull_opt.append("--verify={}".format(verify))

    elif img_type == "dkr":
        if "index" in kwargs:
            pull_opt.append("--dkr-index-url={}".format(kwargs["index"]))

    cmd = "pull-{} {} {} {}".format(img_type, " ".join(pull_opt), image, name)
    ret = _machinectl(cmd)
    if ret["returncode"] != 0:
        msg = (
            "Error occurred while pulling image. Stderr from the pull command"
            "(if any) follows:"
        )
        if ret["stderr"]:
            msg += "\n\n{}".format(ret["stderr"])
        raise Exception(msg)
    return True


def pull_raw(url, name, verify=False):
    """
    Execute a ``machinectl pull-raw`` to download a .qcow2 or raw disk image,
    and add it to /var/lib/machines as a new container.
    """
    return _pull_image("raw", url, name, verify=verify)


def pull_tar(url, name, verify=False):
    """
    Execute a ``machinectl pull-tar`` to download a .tar container image,
    and add it to /var/lib/machines as a new container.
    """
    return _pull_image("tar", url, name, verify=verify)


def pull_dkr(url, name, index):
    """
    Execute a ``machinectl pull-dkr`` to download a docker image and add it to
    /var/lib/machines as a new container.
    """
    return _pull_image("dkr", url, name, index=index)
