from . import constants
from .exceptions import ChordSymbolError


def split_chord_symbol(figure):
    """Split a chord symbol into root, kind, degree modifications, and bass."""
    match = constants.CHORD_SYMBOL_REGEX.match(figure)
    if not match:
        raise ChordSymbolError('Unable to parse chord symbol: %s' % figure)
    root_str, kind_str, modifications_str, bass_str = match.groups()
    return root_str, kind_str, modifications_str, bass_str
