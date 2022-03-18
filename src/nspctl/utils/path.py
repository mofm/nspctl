import os


def which(exe=None):
    """
    identify the location of a given executable
    """
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, exe)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
