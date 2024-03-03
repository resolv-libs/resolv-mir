""" This module contains functions to compute metrics regarding the rhythmic of a NoteSequence proto. """
import numpy as np

from modules.libs.mir.note_sequence import constants, utilities
from modules.libs.mir.protobuf.protos.symbolic_music_pb2 import NoteSequence


def toussaint(note_sequence: NoteSequence, bars: int = None, binary: bool = True) -> float:
    """ Compute Toussaint metric for a quantized NoteSequence proto.

    Toussaint metric measures the degree of syncopation in rhythm patterns.

    Args:
        note_sequence (NoteSequence): The input quantized NoteSequence proto.
        bars (int, optional): The number of bars to consider. Defaults to None.
            If None, it's calculated from the note sequence.
        binary (bool, optional): If True, treat all note onsets equally (binary).
            If False, consider note velocities in the calculation. Defaults to True.

    Returns:
        (float): The Toussaint metric value.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    utilities.assert_is_relative_quantized_sequence(note_sequence)

    if not note_sequence.notes:
        return 0.0

    if bars is None:
        bars = utilities.bars_in_quantized_sequence(note_sequence)

    hierarchy = np.array([5, 1, 2, 1, 3, 1, 2, 1, 4, 1, 2, 1, 3, 1, 2, 1]).repeat(bars)
    max_sum = np.cumsum(np.sort(hierarchy)[::-1])

    n_pulses = len(hierarchy)
    n_onsets = utilities.count_onsets(note_sequence)

    velocity = np.zeros(n_pulses)
    for note in note_sequence.notes:
        velocity[note.quantized_start_step] = 1. if binary else note.velocity / constants.MAX_MIDI_VELOCITY

    metricity = np.sum(hierarchy * velocity)
    metric = max_sum[n_onsets-1] - metricity

    return metric


def note_density(note_sequence: NoteSequence, bars: int = None, binary: bool = True) -> float:
    """ Compute the note density metric for the given NoteSequence.

     Note density measures the density of note onsets or note velocities within the sequence.

     Args:
         note_sequence (NoteSequence): The input NoteSequence.
         bars (int, optional): The number of bars to consider. Defaults to None.
             If None, it's calculated from the note sequence.
         binary (bool, optional): If True, calculate density based on note onsets (binary).
             If False, calculate density based on note velocities. Defaults to True.

     Returns:
         (float): The note density metric value.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
     """
    utilities.assert_is_relative_quantized_sequence(note_sequence)
    if not note_sequence.notes:
        return 0.0
    if bars is None:
        bars = utilities.bars_in_quantized_sequence(note_sequence)
    count = utilities.count_onsets(note_sequence) if binary else np.sum(utilities.get_velocity_list(note_sequence))
    total_steps = utilities.steps_per_bar_in_quantized_sequence(note_sequence) * bars
    return count / total_steps
