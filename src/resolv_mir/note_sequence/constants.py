""" This module defines all the constants used in the note_sequence package.
Constants are related to MIDI, music processing, mathematical operations, ecc...
"""

# MIDI programs see https://soundprogramming.net/file-formats/general-midi-instrument-list/
PIANO_PROGRAMS = range(0, 8)
CHROMATIC_PERCUSSION_PROGRAMS = range(8, 16)
ORGAN_PROGRAMS = range(16, 24)
GUITAR_PROGRAMS = range(24, 32)
BASS_PROGRAMS = range(32, 40)
STRING_PROGRAMS = range(40, 56)
BRASS_PROGRAMS = range(56, 64)
REED_PROGRAMS = range(64, 72)
PIPE_PROGRAMS = range(72, 80)
SYNTH_LEAD_PROGRAMS = range(80, 88)
SYNTH_PAD_PROGRAMS = range(88, 96)
SYNTH_EFFECTS_PROGRAMS = range(96, 104)
ETHNIC_PROGRAMS = range(104, 112)
PERCUSSIVE_PROGRAMS = range(112, 119)
SOUND_EFFECTS_PROGRAMS = range(119, 128)
UN_PITCHED_PROGRAMS = list(SYNTH_EFFECTS_PROGRAMS) + list(PERCUSSIVE_PROGRAMS) + list(SOUND_EFFECTS_PROGRAMS)

# Meter-related constants.
DEFAULT_QUARTERS_PER_MINUTE = 120
DEFAULT_STEPS_PER_BAR = 16  # 4/4 music sampled at 4 steps per quarter note.
DEFAULT_STEPS_PER_QUARTER = 4

# Default absolute quantization.
DEFAULT_STEPS_PER_SECOND = 100

# Standard pulses per quarter. https://en.wikipedia.org/wiki/Pulses_per_quarter_note
STANDARD_PPQ = 220

# Special melody events.
NUM_SPECIAL_MELODY_EVENTS = 2
MELODY_NOTE_OFF = -1
MELODY_NO_EVENT = -2

# Other melody-related constants.
MIN_MELODY_EVENT = -2
MAX_MELODY_EVENT = 127
MIN_MIDI_PITCH = 0  # Inclusive.
MAX_MIDI_PITCH = 127  # Inclusive.
PIANO_MIN_MIDI_PITCH = 21
PIANO_MAX_MIDI_PITCH = 108
NUM_MIDI_PITCHES = MAX_MIDI_PITCH - MIN_MIDI_PITCH + 1
NUM_PIANO_MIDI_PITCHES = PIANO_MAX_MIDI_PITCH - PIANO_MIN_MIDI_PITCH + 1
NOTES_PER_OCTAVE = 12
MEL_PROGRAMS = (list(PIANO_PROGRAMS) + list(CHROMATIC_PERCUSSION_PROGRAMS) + list(ORGAN_PROGRAMS) +
                list(GUITAR_PROGRAMS) + list(STRING_PROGRAMS) + list(REED_PROGRAMS) + list(PIPE_PROGRAMS)
                + list(SYNTH_LEAD_PROGRAMS) + list(ETHNIC_PROGRAMS))

# Velocity-related constants.
DEFAULT_MIDI_VELOCITY = 64
MIN_MIDI_VELOCITY = 1  # Inclusive.
MAX_MIDI_VELOCITY = 127  # Inclusive.

# Program-related constants.
DEFAULT_MIDI_PROGRAM = 0  # Default MIDI Program (0 = grand piano)
DEFAULT_MIDI_CHANNEL = 0  # Default MIDI Channel (0 = first channel)
MIN_MIDI_PROGRAM = 0
MAX_MIDI_PROGRAM = 127

# Chord symbol for "no chord".
NO_CHORD = 'N.C.'

# The indices of the pitch classes in a major scale.
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]

# NOTE_KEYS[note] = The major keys that note belongs to.
# ex. NOTE_KEYS[0] lists all the major keys that contain the note C,
# which are:
# [0, 1, 3, 5, 7, 8, 10]
# [C, C#, D#, F, G, G#, A#]
#
# 0 = C
# 1 = C#
# 2 = D
# 3 = D#
# 4 = E
# 5 = F
# 6 = F#
# 7 = G
# 8 = G#
# 9 = A
# 10 = A#
# 11 = B
#
# NOTE_KEYS can be generated using the code below, but is explicitly declared
# for readability:
# NOTE_KEYS = [[j for j in range(12) if (i - j) % 12 in MAJOR_SCALE]
#              for i in range(12)]
NOTE_KEYS = [
    [0, 1, 3, 5, 7, 8, 10],
    [1, 2, 4, 6, 8, 9, 11],
    [0, 2, 3, 5, 7, 9, 10],
    [1, 3, 4, 6, 8, 10, 11],
    [0, 2, 4, 5, 7, 9, 11],
    [0, 1, 3, 5, 6, 8, 10],
    [1, 2, 4, 6, 7, 9, 11],
    [0, 2, 3, 5, 7, 8, 10],
    [1, 3, 4, 6, 8, 9, 11],
    [0, 2, 4, 5, 7, 9, 10],
    [1, 3, 5, 6, 8, 10, 11],
    [0, 2, 4, 6, 7, 9, 11]
]

# Splitter
DEFAULT_SUBSEQUENCE_PRESERVE_CONTROL_NUMBERS = (
    64,  # sustain
    66,  # sostenuto
    67   # una corda
)

# Set the quantization cutoff.
# Note events before this cutoff are rounded down to nearest step. Notes above this cutoff are rounded up to nearest
# step. The cutoff is given as a fraction of a step.
# For example, with quantize_cutoff = 0.75 using 0-based indexing,
# if .75 < event <= 1.75, it will be quantized to step 1.
# If 1.75 < event <= 2.75 it will be quantized to step 2.
# A number close to 1.0 gives less wiggle room for notes that start early, and they will be snapped to the previous
# step.
QUANTIZE_CUTOFF = 0.75

# Math related constants
FLOAT_RELATIVE_TOLERANCE = 1e-09
FLOAT_ABSOLUTE_TOLERANCE = 0.0
