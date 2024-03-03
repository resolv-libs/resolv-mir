""" This module contains functions to compute metrics regarding the pitch of a NoteSequence proto. """
from math import perm

import numpy as np

from modules.libs.mir.note_sequence import constants, processors, utilities
from modules.libs.mir.note_sequence.metrics import common
from modules.libs.mir.protobuf.protos.symbolic_music_pb2 import NoteSequence


def pitch_range(note_sequence: NoteSequence, num_midi_pitches: int = constants.NUM_PIANO_MIDI_PITCHES) -> float:
    """ Compute the pitch range of a NoteSequence proto.

    The pitch range is defined as the ratio of the difference between the highest and lowest pitch to the total number
    of MIDI pitches considered.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto.
        num_midi_pitches (int, optional): The total number of MIDI pitches to consider. Defaults to 88 (piano range).

    Returns:
        (float): The pitch range of the NoteSequence.
    """
    if not note_sequence.notes:
        return 0.0
    pitch_list = utilities.get_pitch_list(note_sequence)
    metric = (np.max(pitch_list) - np.min(pitch_list)) / num_midi_pitches
    return metric


def contour(note_sequence: NoteSequence, num_midi_pitches: int = constants.NUM_PIANO_MIDI_PITCHES) -> float:
    """ Compute the contour of a NoteSequence proto.

    The contour is defined as the ratio of the sum of the absolute differences between adjacent pitches to the total
    number of MIDI pitches considered.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto.
        num_midi_pitches (int, optional): The total number of MIDI pitches to consider. Defaults to 88 (piano range).

    Returns:
        (float): The contour of the NoteSequence.
    """
    if not note_sequence.notes:
        return 0.0
    pitch_list = utilities.get_pitch_list(note_sequence)
    metric = np.sum(np.abs(np.diff(pitch_list))) / num_midi_pitches
    return metric


def ratio_unique_notes(note_sequence: NoteSequence, num_midi_pitches: int = constants.NUM_PIANO_MIDI_PITCHES) -> float:
    """ Compute the ratio of unique notes in a given NoteSequence proto.

    The ratio of unique notes is defined with respect to the total number of MIDI pitches considered and the length of
    the sequence.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto.
        num_midi_pitches (int, optional): The total number of MIDI pitches to consider. Defaults to 88 (piano range).

    Returns:
        (float): The ratio of unique notes in the NoteSequence.
    """
    unique_notes = utilities.get_unique_notes(note_sequence)
    normalization_factor = common.get_metric_normalization_factor(note_sequence) * num_midi_pitches
    return len(unique_notes) / normalization_factor


def ratio_unique_ngrams(note_sequence: NoteSequence, n: int = 2,
                        num_midi_pitches: int = constants.NUM_PIANO_MIDI_PITCHES) -> float:
    """ Compute the ratio of unique n-grams in a given NoteSequence.

    The ratio of unique n-grams is defined with respect to the length of the sequence.

    Args:
        note_sequence (NoteSequence): The input NoteSequence.
        n (int, optional): The size of n-grams to consider. Defaults to 2.
        num_midi_pitches (int, optional): The total number of MIDI pitches to consider.
            Defaults to 88 (piano range).

    Returns:
        (float): The ratio of unique n-grams in the NoteSequence.
    """
    note_sequence_ngrams = processors.extractor.extract_ngrams_from_note_sequence(note_sequence, n)
    unique_ngrams = utilities.get_unique_note_sequences(note_sequence_ngrams)
    normalization_factor = common.get_metric_normalization_factor(note_sequence)
    max_number_unique_ngrams = perm(num_midi_pitches, n)
    return len(unique_ngrams) / normalization_factor
