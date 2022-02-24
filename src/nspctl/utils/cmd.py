import subprocess
import shlex


def run_cmd(cmd, is_shell, cwd=None):
    """
    Execute command on the given shell
    """
    assert is_shell is not None, "is_shell param must exist"

    if is_shell:
        args = cmd
    else:
        args = shlex.split(cmd)

    try:
        proc = subprocess.run(args,
                              shell=is_shell,
                              cwd=cwd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True
                              )

        cmd_output = {
            'returncode': proc.returncode,
            'stdout': (proc.stdout.rstrip()
                       if proc.stdout else None),
            'stderr': (proc.stderr.rstrip()
                       if proc.stderr else None
                       )
        }
        return cmd_output
    except OSError as e:
        raise e


def popen(cmd, is_shell, cwd=None):
    """
    subprocess Popen function
    """
    assert is_shell is not None, "is_shell param must exist"
    if is_shell:
        args = cmd
    else:
        args = shlex.split(cmd)

    try:
        proc = subprocess.Popen(
            '{}'.format(args),
            shell=is_shell,
            cwd=cwd,
            universal_newlines=True
        )
        out, err = proc.communicate()
    except OSError as e:
        raise e
