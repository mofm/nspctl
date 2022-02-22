import json

_styles = {}
"""Maps style class to tuple of attribute names."""

codes = {}
"""Maps attribute name to ansi code."""

esc_seq = "\x1b["

codes["normal"] = esc_seq + "0m"
codes["reset"] = esc_seq + "39;49;00m"

codes["bold"] = esc_seq + "01m"
codes["faint"] = esc_seq + "02m"
codes["standout"] = esc_seq + "03m"
codes["underline"] = esc_seq + "04m"
codes["blink"] = esc_seq + "05m"
codes["overline"] = esc_seq + "06m"
codes["reverse"] = esc_seq + "07m"
codes["invisible"] = esc_seq + "08m"

codes["no-attr"] = esc_seq + "22m"
codes["no-standout"] = esc_seq + "23m"
codes["no-underline"] = esc_seq + "24m"
codes["no-blink"] = esc_seq + "25m"
codes["no-overline"] = esc_seq + "26m"
codes["no-reverse"] = esc_seq + "27m"

codes["bg_black"] = esc_seq + "40m"
codes["bg_darkred"] = esc_seq + "41m"
codes["bg_darkgreen"] = esc_seq + "42m"
codes["bg_brown"] = esc_seq + "43m"
codes["bg_darkblue"] = esc_seq + "44m"
codes["bg_purple"] = esc_seq + "45m"
codes["bg_teal"] = esc_seq + "46m"
codes["bg_lightgray"] = esc_seq + "47m"
codes["bg_default"] = esc_seq + "49m"
codes["bg_darkyellow"] = codes["bg_brown"]


def color(fg, bg="default", attr=["normal"]):
    """
    Create color from given attributes
    """
    mystr = codes[fg]
    for i in [bg] + attr:
        mystr += codes[i]
    return mystr


ansi_codes = []
for x in range(30, 38):
    ansi_codes.append("%im" % x)
    ansi_codes.append("%i;01m" % x)

rgb_ansi_colors = [
    "0x000000",
    "0x555555",
    "0xAA0000",
    "0xFF5555",
    "0x00AA00",
    "0x55FF55",
    "0xAA5500",
    "0xFFFF55",
    "0x0000AA",
    "0x5555FF",
    "0xAA00AA",
    "0xFF55FF",
    "0x00AAAA",
    "0x55FFFF",
    "0xAAAAAA",
    "0xFFFFFF",
]

for x in range(len(rgb_ansi_colors)):
    codes[rgb_ansi_colors[x]] = esc_seq + ansi_codes[x]

del x

codes["black"] = codes["0x000000"]
codes["darkgray"] = codes["0x555555"]

codes["red"] = codes["0xFF5555"]
codes["darkred"] = codes["0xAA0000"]

codes["green"] = codes["0x55FF55"]
codes["darkgreen"] = codes["0x00AA00"]

codes["yellow"] = codes["0xFFFF55"]
codes["brown"] = codes["0xAA5500"]

codes["blue"] = codes["0x5555FF"]
codes["darkblue"] = codes["0x0000AA"]

codes["fuchsia"] = codes["0xFF55FF"]
codes["purple"] = codes["0xAA00AA"]

codes["turquoise"] = codes["0x55FFFF"]
codes["teal"] = codes["0x00AAAA"]

codes["white"] = codes["0xFFFFFF"]
codes["lightgray"] = codes["0xAAAAAA"]

codes["darkteal"] = codes["turquoise"]
# Some terminals have darkyellow instead of brown.
codes["0xAAAA00"] = codes["brown"]
codes["darkyellow"] = codes["0xAAAA00"]

# styles
_styles["BAD"] = ("red", )
_styles["BRACKET"] = ("blue", )
_styles["ERR"] = ("red", )
_styles["GOOD"] = ("green", )
_styles["HILITE"] = ("teal", )
_styles["INFO"] = ("darkgreen", )
_styles["LOG"] = ("green", )
_styles["NORMAL"] = ("normal", )
_styles["QAWARN"] = ("brown", )
_styles["WARN"] = ("yellow", )


def resetcolor():
    """
    Reset the color code
    """
    return codes["reset"]


def style_to_ansi_code(style):
    """
    A string containing one or more ansi escape codes that are
    used to render the given style.
    """
    ret = ""
    for attr_name in _styles[style]:
        ret += codes.get(attr_name, attr_name)
    return ret


def colormap():
    """
    Create new colormap
    """
    mycolors = []
    for c in ("GOOD", "WARN", "BAD", "HILITE", "BRACKET", "NORMAL"):
        mycolors.append("%s=$'%s'" % (c, style_to_ansi_code(c)))
    return "\n".join(mycolors)


def colorize(color_key, text):
    """
    Colorize the given string
    """
    if color_key in codes:
        return codes[color_key] + text + codes["reset"]
    if color_key in _styles:
        return style_to_ansi_code(color_key) + text + codes["reset"]
    return text


compat_functions_colors = [
    "bold",
    "white",
    "teal",
    "turquoise",
    "darkteal",
    "fuchsia",
    "purple",
    "blue",
    "darkblue",
    "green",
    "darkgreen",
    "yellow",
    "brown",
    "darkyellow",
    "red",
    "darkred",
]


class CreateColor:
    __slots__ = ("_color_key",)

    def __init__(self, color_key):
        self._color_key = color_key

    def __call__(self, text):
        return colorize(self._color_key, text)


# create dynamically colorize
for c in compat_functions_colors:
    globals()[c] = CreateColor(c)


class NspctlOutput(object):
    """
    This is Nspctl output object
    """

    def __init__(self):
        self.new_msg = None

    def pprint(self, msg):
        """
        This is main print method
        """
        self._repr(msg)
        return self.new_msg

    def _list_to_str(self, msg):
        """
        Converts and returns string
        list to str
        """
        new_str = ""
        if msg:
            for line in msg:
                new_str += colorize("GOOD", " * ") + line + "\n"
            return new_str
        else:
            new_str = "nspctl nothing to show \n"
            return "{}".format(colorize("WARN", new_str))

    def _bool_to_str(self, msg):
        """
        Converts and returns string
        boolean to str
        """
        if msg is True:
            new_str = "Command is executed successfully \n"
            return "{}".format(colorize("GOOD", new_str))
        else:
            new_str = "Command is executed failed! \n"
            return "{}".format(colorize("BAD", new_str))

    def _dict_to_str(self, msg):
        """
        Converts and returns string
        dict to str
        """
        if msg:
            cln_msg = eval(str(msg).encode('ascii', 'ignore').decode())
            new_str = json.dumps(cln_msg, indent=2, default=str)
            return new_str
        else:
            new_str = "nspctl nothing to show \n"
            return "{}".format(colorize("WARN", new_str))

    def _str_to_str(self, msg):
        """
        Converts and returns string
        str to str
        """
        if msg:
            return msg
        else:
            new_str = "nspctl nothing to show \n"
            return "{}".format(colorize("WARN", new_str))

    def _repr(self, msg):
        """
        Call the type methods
        """
        typ = type(msg)
        assert typ in _builtin_types, "Invalid data type"

        func = "_" + typ.__name__ + "_to_str"
        self.new_msg = getattr(self, func)(msg)


_builtin_types = frozenset(
    {
        str,
        bool,
        dict,
        list
    }
)


def nprint(msg):
    """
    Print a Python object
    with nspctl output styles
    """
    output = NspctlOutput()
    fancy_output = output.pprint(msg)
    return fancy_output
