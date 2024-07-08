"""
Author: Matteo Pettenò.
Package Name: attributes.
Description: Package providing functions to compute metrics relative to a NoteSequence proto.
Copyright (c) 2024, Matteo Pettenò
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
import functools

from . import dynamics
from . import pitch
from . import rhythmic

from resolv_mir.protobuf import NoteSequence


def compute_attribute(note_sequence: NoteSequence, attribute_name: str, **kwargs) -> float:
    attribute_fn = ATTRIBUTE_FN_MAP[attribute_name]
    return attribute_fn(note_sequence=note_sequence, **kwargs)


ATTRIBUTE_FN_MAP = {
    'toussaint': rhythmic.toussaint,
    'note_density': rhythmic.note_density,
    'pitch_range': pitch.pitch_range,
    'contour': pitch.contour,
    'unique_notes_ratio': pitch.ratio_unique_notes,
    'unique_bigrams_ratio': functools.partial(pitch.ratio_unique_ngrams, n=2),
    'unique_trigrams_ratio': functools.partial(pitch.ratio_unique_ngrams, n=3),
    'dynamic_range': dynamics.dynamic_range,
    'note_change_ratio': dynamics.ratio_note_change,
    'ratio_note_off_steps': dynamics.ratio_note_off_steps,
    'ratio_hold_note_steps': dynamics.ratio_hold_note_steps,
    'repetitive_section_ratio': dynamics.ratio_repetitive_sections,
    'len_longest_rep_section': dynamics.length_longest_repetitive_section
}
