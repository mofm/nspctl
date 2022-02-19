import logging
import types

logger = logging.getLogger(__name__)


def alias_function(fun, name, doc=None):
    """
    Copy a function
    """
    alias_fun = types.FunctionType(
        fun.__code__,
        fun.__globals__,
        str(name),
        fun.__defaults__,
        fun.__closure__,
    )
    alias_fun.__dict__.update(fun.__dict__)

    if doc and isinstance(doc, str):
        alias_fun.__doc__ = doc
    else:
        orig_name = fun.__name__
        alias_msg = "\nThis function is an alias of ``{}``.\n".format(orig_name)
        alias_fun.__doc__ = alias_msg + (fun.__doc__ or "")

    return alias_fun
