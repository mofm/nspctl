import argparse

options = [
    "info",
    "list",
    "start",
    "stop",
    "reboot",
    "enable",
    "disable",
    "shell",
    "remove",
    "pull-raw",
    "pull-tar",
    "pull-docker",
    "bootstrap",
    "copy-to",
    "version"
]

shortmap = {
    "sh": "shell",
    "rm": "remove",
    "ls": "list",
    "v": "version",
    "pd": "pull-docker",
    "pt": "pull-tar",
    "pr": "pull-raw",
    "cpt": "copy-to",
    "h": "help",
}
