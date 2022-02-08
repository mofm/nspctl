import logging

logger = logging.getLogger(__name__)


def clean_kwargs(**kwargs):
    """
    kwargs = __utils__['args.clean_kwargs'](**kwargs)
    """
    ret = {}
    for key, val in kwargs.items():
        if not key.startswith("__"):
            ret[key] = val
    return ret


def invalid_kwargs(invalid_kwargs, raise_exc=True):
    """
    Raise Error if invalid_kwargs is non-empty
    """
    if invalid_kwargs:
        if isinstance(invalid_kwargs, dict):
            new_invalid = ["{}={}".format(x, y) for x, y in invalid_kwargs.items()]
            invalid_kwargs = new_invalid
    msg = "The following keyword arguments are not valid: {}".format(
        ", ".join(invalid_kwargs)
    )
    if raise_exc:
        return msg
    else:
        return msg
