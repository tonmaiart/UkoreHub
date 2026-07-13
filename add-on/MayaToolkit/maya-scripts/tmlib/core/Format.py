import re


def cname(tag_name=None, name=None, type=None, position=None):
    if tag_name is None:
        new_name = "{}_{}".format(name, type)
    else:
        new_name = "{}_{}_{}".format(tag_name, name, type)

    return new_name


def get_exist_axis(list_axis):
    """
    Identifies the axes from {'x', 'y', 'z'} that are present
    in the input arguments.

    Args:
        args (list): A list of strings, typically from sys.argv,
                     representing the command-line arguments.

    Returns:
        str: A string containing the existing axes, or an empty string
             if no axes are present.
    """

    ref_axis = ["x", "y", "z"]

    for axis in list_axis:
        axis_main = axis.replace("-", "")
        ref_axis.remove(axis_main)

    return ref_axis[0]


def get_rgb_from_index(index):
    """Return rgb color by given index"""
    """
    Get the RGB color corresponding to a Maya index color.

    :param index: Index color value (integer between 0 and 31).
    :return: A tuple of (R, G, B) values in the range [0, 1].
    :raises ValueError: If the index is not between 0 and 31.
    """
    index_to_rgb = {
        0: (0.0, 0.0, 0.0),
        1: (0.247, 0.247, 0.247),
        2: (0.498, 0.498, 0.498),
        3: (0.608, 0.0, 0.157),
        4: (0.0, 0.016, 0.373),
        5: (0.0, 0.0, 0.561),
        6: (0.0, 0.275, 0.094),
        7: (0.145, 0.0, 0.263),
        8: (0.780, 0.0, 0.780),
        9: (0.537, 0.278, 0.2),
        10: (0.243, 0.133, 0.122),
        11: (0.600, 0.145, 0.0),
        12: (0.392, 0.216, 0.0),
        13: (0.263, 0.275, 0.0),
        14: (0.0, 0.467, 0.0),
        15: (0.0, 0.275, 0.392),
        16: (0.0, 0.18, 0.537),
        17: (0.0, 0.0, 0.612),
        18: (0.216, 0.0, 0.6),
        19: (0.475, 0.0, 0.537),
        20: (0.6, 0.0, 0.325),
        21: (0.627, 0.275, 0.216),
        22: (0.62, 0.51, 0.216),
        23: (0.0, 0.58, 0.0),
        24: (0.255, 0.6, 0.459),
        25: (0.0, 0.6, 0.6),
        26: (0.0, 0.4, 0.6),
        27: (0.325, 0.475, 0.6),
        28: (0.537, 0.537, 0.6),
        29: (0.6, 0.6, 0.6),
        30: (0.784, 0.784, 0.784),
        31: (1.0, 1.0, 1.0),
    }

    if index not in index_to_rgb:
        raise ValueError("Index must be an integer between 0 and 31.")

    return index_to_rgb[index]


def get_single_axis_enum():
    return ["X", "Y", "Z", "-X", "-Y", "-Z"]


def get_single_axis_enum_pos():
    return ["X", "Y", "Z"]


def get_triple_axis_enum():
    return ["xyz", "xzy", "yxz", "yzx", "zyx", "zxy"]


def get_tuple_axis(direction: str):
    # Define a mapping from input string to the corresponding tuple
    direction_map = {
        "x": (1, 0, 0),
        "y": (0, 1, 0),
        "z": (0, 0, 1),
        "-x": (-1, 0, 0),
        "-y": (0, -1, 0),
        "-z": (0, 0, -1),
        # Add more mappings here based on your needs
    }

    # Return the tuple corresponding to the input, or None if the input is not valid
    return direction_map.get(direction, None)


def convert_single_axis_enum(index):
    return ["x", "y", "z", "-x", "-y", "-z"][index]


def convert_single_axis_enum_pos(index):
    return ["x", "y", "z"][index]


def convert_triple_axis_enum(index):
    return ["xyz", "xzy", "yxz", "yzx", "zyx", "zxy"][index]


def del_neg(text):
    return text.replace("-", "").replace(" ", "")


def get_axis_double3(input, minusValue=True, invert=False):
    list_return = [0, 0, 0]
    list_axis_ref = ["x", "y", "z"]
    list_axis_ref_minus = ["-x", "-y", "-z"]

    dict_axis = {
        "x": (1, 0, 0),
        "y": (0, 1, 0),
        "z": (0, 0, 1),
        "-x": (-1, 0, 0),
        "-y": (0, -1, 0),
        "-z": (0, 0, -1),
    }

    if input not in dict_axis.keys():
        raise Exception("Invalid Input")

    output = dict_axis[input]

    if invert:
        output = [value * -1 for value in output]

    return output


def to_pascal_case(text):
    """
    Converts a space-separated string to PascalCase.

    Each word is capitalized and concatenated without spaces.

    Args:
        text (str): The input string (e.g., "controller editor").

    Returns:
        str: The converted string in PascalCase (e.g., "ControllerEditor").
    """
    words = text.strip().split()
    return "".join(word.capitalize() for word in words)


def to_abbreviation_case(text):
    # Start with the first character
    initials = text[0]

    # Add each uppercase character (start of new word)
    initials += "".join(c for c in text[1:] if c.isupper())

    # Lowercase if needed
    result = initials.lower()

    return result


def to_camel_case(text):
    """
    Converts a space-separated string to camelCase.

    The first word is in lowercase and each subsequent word is capitalized.

    Args:
        text (str): The input string (e.g., "controller editor").

    Returns:
        str: The converted string in camelCase (e.g., "controllerEditor").
    """
    words = text.strip().split()
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def split_camel_pascal(text):
    """
    Converts camelCase or PascalCase strings into space-separated words.

    Examples:
        "controllerEditor" → "Controller Editor"
        "ControllerEditor" → "Controller Editor"

    Args:
        text (str): The camelCase or PascalCase string.

    Returns:
        str: A human-readable string with spaces between words.
    """
    if not text:
        return ""
    words = re.sub(r"(?<!^)(?=[A-Z])", " ", text)
    return words[0].upper() + words[1:]


def check_neg(input):
    list_input = []

    if type(input) is list:
        list_input = input
    elif type(input) is str:
        list_input.append(input)
    else:
        raise Exception("Invalid Input")

    for item in list_input:
        if "-" in item:
            raise Exception("Must Be Absolute Axis , {}".format(item))
