import re

from . import constants


def parse_pitch_class(pitch_class_str):
    """Parse pitch class from string, returning scale step and alteration."""
    match = re.match(constants.PITCH_CLASS_REGEX, pitch_class_str)
    step, alter = match.groups()
    return step, len(alter) * (1 if '#' in alter else -1)


def parse_root(root_str):
    """Parse chord root from string."""
    return parse_pitch_class(root_str)


def parse_degree(degree_str):
    """Parse scale degree from string (from internal kind representation)."""
    match = constants.SCALE_DEGREE_REGEX.match(degree_str)
    alter, degree = match.groups()
    return int(degree), len(alter) * (1 if '#' in alter else -1)


def parse_kind(kind_str):
    """Parse chord kind from string, returning a scale degree dictionary."""
    degrees = constants.CHORD_KINDS_BY_ABBREV[kind_str]
    # Here we make the assumption that each scale degree can be present in a chord
    # at most once. This is not generally true, as e.g. a chord could contain both
    # b9 and #9.
    return dict(parse_degree(degree_str) for degree_str in degrees)


def parse_modifications(modifications_str):
    """Parse scale degree modifications from string.

    This returns a list of function-degree-alteration triples. The function, when
    applied to the list of scale degrees, the degree to modify, and the
    alteration, performs the modification.

    Args:
      modifications_str: A string containing the scale degree modifications to
          apply to a chord, in standard chord symbol format.

    Returns:
      A Python list of scale degree modification tuples, each of which contains a)
      a function that applies the modification, b) the integer scale degree to
      which to apply the modifications, and c) the number of semitones in the
      modification.
    """
    modifications = []
    while modifications_str:
        match = constants.MODIFICATION_REGEX.match(modifications_str)
        type_str, degree_str = match.groups()
        mod_fn, alter = constants.DEGREE_MODIFICATIONS[type_str]
        modifications.append((mod_fn, int(degree_str), alter))
        modifications_str = modifications_str[match.end():]
        assert match.end() > 0
    return modifications


def parse_bass(bass_str):
    """Parse bass, returning scale step and alteration or None if no bass."""
    if bass_str:
        return parse_pitch_class(bass_str[1:])
    else:
        return None
