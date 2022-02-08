import subprocess
import shlex


def run_cmd(cmd, is_shell, cwd=None):
    assert is_shell is not None, "is_shell param must exist"

    if is_shell:
        args = cmd
    else:
        args = shlex.split(cmd)

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
