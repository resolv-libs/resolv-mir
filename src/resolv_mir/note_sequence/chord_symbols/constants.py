import re

from . import common

# Intervals between scale steps.
STEPS_ABOVE = {'A': 2, 'B': 1, 'C': 2, 'D': 2, 'E': 1, 'F': 2, 'G': 2}

# List of chord kinds with abbreviations and scale degrees. Scale degrees are
# represented as strings here a) for human readability, and b) because the
# number of semitones is insufficient when the chords have scale degree
# modifications.
CHORD_KINDS = [
    # major triad
    (['', 'maj', 'M'],
     ['1', '3', '5']),

    # minor triad
    (['m', 'min', '-'],
     ['1', 'b3', '5']),

    # augmented triad
    (['+', 'aug'],
     ['1', '3', '#5']),

    # diminished triad
    (['o', 'dim'],
     ['1', 'b3', 'b5']),

    # dominant 7th
    (['7'],
     ['1', '3', '5', 'b7']),

    # major 7th
    (['maj7', 'M7'],
     ['1', '3', '5', '7']),

    # minor 7th
    (['m7', 'min7', '-7'],
     ['1', 'b3', '5', 'b7']),

    # diminished 7th
    (['o7', 'dim7'],
     ['1', 'b3', 'b5', 'bb7']),

    # augmented 7th
    (['+7', 'aug7'],
     ['1', '3', '#5', 'b7']),

    # half-diminished
    (['m7b5', '-7b5', '/o', '/o7'],
     ['1', 'b3', 'b5', 'b7']),

    # minor triad with major 7th
    (['mmaj7', 'mM7', 'minmaj7', 'minM7', '-maj7', '-M7',
      'm(maj7)', 'm(M7)', 'min(maj7)', 'min(M7)', '-(maj7)', '-(M7)'],
     ['1', 'b3', '5', '7']),

    # major 6th
    (['6'],
     ['1', '3', '5', '6']),

    # minor 6th
    (['m6', 'min6', '-6'],
     ['1', 'b3', '5', '6']),

    # dominant 9th
    (['9'],
     ['1', '3', '5', 'b7', '9']),

    # major 9th
    (['maj9', 'M9'],
     ['1', '3', '5', '7', '9']),

    # minor 9th
    (['m9', 'min9', '-9'],
     ['1', 'b3', '5', 'b7', '9']),

    # augmented 9th
    (['+9', 'aug9'],
     ['1', '3', '#5', 'b7', '9']),

    # 6/9 chord
    (['6/9'],
     ['1', '3', '5', '6', '9']),

    # dominant 11th
    (['11'],
     ['1', '3', '5', 'b7', '9', '11']),

    # major 11th
    (['maj11', 'M11'],
     ['1', '3', '5', '7', '9', '11']),

    # minor 11th
    (['m11', 'min11', '-11'],
     ['1', 'b3', '5', 'b7', '9', '11']),

    # dominant 13th
    (['13'],
     ['1', '3', '5', 'b7', '9', '11', '13']),

    # major 13th
    (['maj13', 'M13'],
     ['1', '3', '5', '7', '9', '11', '13']),

    # minor 13th
    (['m13', 'min13', '-13'],
     ['1', 'b3', '5', 'b7', '9', '11', '13']),

    # suspended 2nd
    (['sus2'],
     ['1', '2', '5']),

    # suspended 4th
    (['sus', 'sus4'],
     ['1', '4', '5']),

    # suspended 4th with dominant 7th
    (['sus7', '7sus'],
     ['1', '4', '5', 'b7']),

    # pedal point
    (['ped'],
     ['1']),

    # power chord
    (['5'],
     ['1', '5'])
]

# Dictionary mapping chord kind abbreviations to names and scale degrees.
CHORD_KINDS_BY_ABBREV = dict((abbrev, degrees) for abbrevs, degrees in CHORD_KINDS for abbrev in abbrevs)

# Scale degree modifications. There are three basic types of modifications:
# addition, subtraction, and alteration. These have been expanded into six types
# to aid in parsing, as each of the three basic operations has its own
# requirements on the scale degree operand:
#
#  - Addition can accept altered and unaltered scale degrees.
#  - Subtraction can only accept unaltered scale degrees.
#  - Alteration can only accept altered scale degrees.
DEGREE_MODIFICATIONS = {
    'add': (common.add_scale_degree, 0),
    'add#': (common.add_scale_degree, 1),
    'addb': (common.add_scale_degree, -1),
    'no': (common.subtract_scale_degree, 0),
    '#': (common.alter_scale_degree, 1),
    'b': (common.alter_scale_degree, -1)
}

# Regular expression for chord root.
# Examples: 'C', 'G#', 'Ab', 'D######'
ROOT_PATTERN = r'[A-G](?:#*|b*)(?![#b])'

# Regular expression for chord kind (abbreviated).
# Examples: '', 'm7b5', 'min', '-13', '+', 'm(M7)', 'dim', '/o7', 'sus2'
CHORD_KIND_PATTERN = '|'.join(re.escape(abbrev) for abbrev in CHORD_KINDS_BY_ABBREV)

# Regular expression for scale degree modifications. (To keep the regex simpler,
# parentheses are not required to match here, e.g. '(#9', 'add2)', '(b5(#9)',
# and 'no5)(b9' will all match.)
# Examples: '#9', 'add6add9', 'no5(b9)', '(add2b5no3)', '(no5)(b9)'
MODIFICATIONS_PATTERN = r'(?:\(?(?:%s)[0-9]+\)?)*' % '|'.join(re.escape(mod) for mod in DEGREE_MODIFICATIONS)

# Regular expression for chord bass.
# Examples: '', '/C', '/Bb', '/F##', '/Dbbbb'
BASS_PATTERN = '|/%s' % ROOT_PATTERN

# Regular expression for full chord symbol.
CHORD_SYMBOL_PATTERN = ''.join('(%s)' % pattern for pattern in [
    ROOT_PATTERN,  # root pitch class
    CHORD_KIND_PATTERN,  # chord kind
    MODIFICATIONS_PATTERN,  # scale degree modifications
    BASS_PATTERN]) + '$'  # bass pitch class
CHORD_SYMBOL_REGEX = re.compile(CHORD_SYMBOL_PATTERN)

# Regular expression for a single pitch class.
# Examples: 'C', 'G#', 'Ab', 'D######'
PITCH_CLASS_PATTERN = r'([A-G])(#*|b*)$'
PITCH_CLASS_REGEX = re.compile(PITCH_CLASS_PATTERN)

# Regular expression for a single scale degree.
# Examples: '1', '7', 'b3', '#5', 'bb7', '13'
SCALE_DEGREE_PATTERN = r'(#*|b*)([0-9]+)$'
SCALE_DEGREE_REGEX = re.compile(SCALE_DEGREE_PATTERN)

# Regular expression for a single scale degree modification. (To keep the regex
# simpler, parentheses are not required to match here, so open or closing paren
# could be missing, e.g. '(#9' and 'add2)' will both match.)
# Examples: '#9', 'add6', 'no5', '(b5)', '(add9)'
MODIFICATION_PATTERN = r'\(?(%s)([0-9]+)\)?' % '|'.join(re.escape(mod) for mod in DEGREE_MODIFICATIONS)
MODIFICATION_REGEX = re.compile(MODIFICATION_PATTERN)
