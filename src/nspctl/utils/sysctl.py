from .cmd import run_cmd


def lsmod():
    """
    Return output of lsmod
    """
    ret = []

    with open("/proc/modules", "r") as f:
        lines = f.readlines()

    for line in lines:
        mod = line.split()[0]
        ret.append(mod)

    return ret


def rmmod(mod):
    """
    Return output of rmmod
    """
    cmd = "rmmod {}".format(mod)
    exe_cmd = run_cmd(cmd, is_shell=True)
    if exe_cmd["returncode"] == 0:
        return exe_cmd["stdout"]
    else:
        return exe_cmd["stderr"]


def modprobe(mod):
    """
    Return output of modprobe
    """
    cmd = "modprobe {}".format(mod)
    exe_cmd = run_cmd(cmd, is_shell=True)
    if exe_cmd["returncode"] == 0:
        return exe_cmd["stdout"]
    else:
        return exe_cmd["stderr"]


def sysctlset(name, limit):
    """
    Helper function to set sysctl limits
    """
    if '/' not in name:
        name = '/proc/sys/' + name.replace('.', '/')
        # read limit
    with open(name, 'r') as f:
        oldlimit = f.readline()
        if isinstance(limit, int):
            # compare integer limits before overriding
            if int(oldlimit) < limit:
                with open(name, 'w') as writeFile:
                    writeFile.write("%d" % limit)
        else:
            # overwrite non-integer limits
            with open(name, 'w') as writeFile:
                writeFile.write(limit)
