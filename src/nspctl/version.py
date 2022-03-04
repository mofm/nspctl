__version__ = "0.0.1-dev01"
__version_info__ = (0, 0, 1, 1)
# if "dev" in __version__:
#     try:
#         import os
#         import subprocess
#         if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".git")):
#             r = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
#             __version__ = "{}-{}".format(__version__, r)
#     except Exception as e:
#         print(e)
