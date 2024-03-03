""" This module provides utility functions for working with NoteSequence protos in symbolic music processing.

It includes functions for checking quantization status, computing various properties of quantized NoteSequence
protos such as number of bars, length in seconds, and steps per bar, as well as functions for manipulating note
pitches, velocities, and detecting onsets.

Additionally, it provides functions for comparing NoteSequence protos for equality, asserting quantization status,
and handling floating-point number comparisons with tolerance.

"""
import math
from typing import List, Callable, TypeVar

import numpy as np

from . import constants, exceptions
from resolv_mir.protobuf import NoteSequence


# ---------------------------------------- NOTE SEQUENCE ----------------------------------------

def is_quantized_sequence(note_sequence: NoteSequence) -> bool:
    """ Returns whether a NoteSequence proto has been quantized.

    Args:
      note_sequence: A NoteSequence proto.

    Returns:
      (bool): True if `note_sequence` is quantized, otherwise False.
    """
    return (note_sequence.quantization_info.steps_per_quarter > 0
            or note_sequence.quantization_info.steps_per_second > 0)


def is_relative_quantized_sequence(note_sequence: NoteSequence) -> bool:
    """ Returns whether a NoteSequence proto has been quantized relative to tempo.

    Args:
        note_sequence: A NoteSequence proto.

    Returns:
        (bool): True if note_sequence is quantized relative to tempo, otherwise False.
    """
    return note_sequence.quantization_info.steps_per_quarter > 0


def is_absolute_quantized_sequence(note_sequence: NoteSequence) -> bool:
    """ Returns whether a NoteSequence proto has been quantized by absolute time.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.

    Returns:
        (bool): True if note_sequence is quantized by absolute time, otherwise False.
    """
    return note_sequence.quantization_info.steps_per_second > 0


def quarters_per_beat_in_quantized_sequence(note_sequence) -> float:
    """ Compute the number of quarters per beat in a quantized NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto that has been quantized relative to tempo.

    Returns:
        quarters_per_beat (float): The number of quarters per beat in note_sequence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    assert_is_relative_quantized_sequence(note_sequence)
    # A quantized NoteSequence must have only one time signature so the value per single beat in a bar is given by:
    beat_value = note_sequence.time_signatures[0].denominator
    quarters_per_beat = 4.0 / beat_value
    return quarters_per_beat


def bars_in_quantized_sequence(note_sequence: NoteSequence) -> int:
    """ Compute the total number of bars in a quantized NoteSequence proto.
    The total number is rounded to the next integer value.

    Args:
      note_sequence (NoteSequence): A NoteSequence proto that has been quantized relative to tempo.

    Returns:
      bar_count (int): Number of bars in note_sequence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """

    bar_count = note_sequence.total_quantized_steps / steps_per_bar_in_quantized_sequence(note_sequence)
    return math.ceil(bar_count)


def bars_length_in_quantized_sequence(note_sequence: NoteSequence, n_bars: int) -> float:
    """ Compute the length in seconds of n bars in a quantized NoteSequence proto

    Args:
      note_sequence (NoteSequence): A NoteSequence proto that has been quantized relative to tempo.
      n_bars (int): Number of bars for which to compute the length in seconds

    Returns:
      bars_length (float): Length in seconds of n bars in note_sequence

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    assert_is_relative_quantized_sequence(note_sequence)
    total_steps = steps_per_bar_in_quantized_sequence(note_sequence) * n_bars
    steps_per_second = steps_per_second_in_quantized_sequence(note_sequence)
    bars_length = total_steps / steps_per_second
    return bars_length


def quarters_per_bar_in_quantized_sequence(note_sequence: NoteSequence) -> float:
    """ Compute the number of quarters per bar in a quantized NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto that has been quantized relative to tempo.

    Returns:
        quarters_per_bar (float): The number of quarters per bar in note_sequence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    assert_is_relative_quantized_sequence(note_sequence)
    # A quantized NoteSequence must have only one time signature so total numbers of beats in a bar is given by:
    beat_per_bar = note_sequence.time_signatures[0].numerator
    quarters_per_beat = quarters_per_beat_in_quantized_sequence(note_sequence)
    quarters_per_bar = quarters_per_beat * beat_per_bar
    return quarters_per_bar


def steps_per_bar_in_quantized_sequence(note_sequence: NoteSequence) -> float:
    """ Compute the number of steps per bar in a quantized NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto that has been quantized relative to tempo.

    Returns:
        steps_per_bar (float): The number of steps per bar in note_sequence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    quarters_per_bar = quarters_per_bar_in_quantized_sequence(note_sequence)
    steps_per_bar = note_sequence.quantization_info.steps_per_quarter * quarters_per_bar
    return steps_per_bar


def steps_per_second_in_quantized_sequence(note_sequence: NoteSequence) -> float:
    """ Compute the number of steps per second in a quantized NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto that has been quantized relative to tempo.

    Returns:
        steps_per_second (float): The number of steps per second in note_sequence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    assert_is_relative_quantized_sequence(note_sequence)
    # A quantized NoteSequence must have only one tempo so its QPM is:
    qpm = note_sequence.tempos[0].qpm
    steps_per_quarter = note_sequence.quantization_info.steps_per_quarter
    return steps_per_quarter_to_steps_per_second(steps_per_quarter, qpm)


def steps_per_quarter_to_steps_per_second(steps_per_quarter: int, qpm: float) -> float:
    """ Convert the number of steps per second to the number of steps per quarter given a QPM.

    Args:
        steps_per_quarter (int): The number of steps per quarter to convert
        qpm (float): the QPM (quarter per minute) associated to steps_per_quarter

    Returns:
        steps_per_second (float): The number of steps per second given steps_per_quarter and QPM
    """
    steps_per_second = steps_per_quarter * qpm / 60.0
    return steps_per_second


def steps_per_second_to_step_per_quarter(steps_per_second: int, qpm: float):
    """ Convert the number of steps per quarter to the number of steps per second given a QPM.

    Args:
        steps_per_second (int): The number of steps per second to convert
        qpm (float): the QPM (quarter per minute) associated to steps_per_second

    Returns:
        steps_per_quarter (float): The number of steps per second given steps_per_second and QPM
    """
    steps_per_quarter = steps_per_second * 60.0 / qpm
    return steps_per_quarter


def get_note_pitches_histogram_for_note_sequence(note_sequence: NoteSequence) -> np.ndarray:
    """ Gets a histogram of the note occurrences in a NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.

    Returns:
        histogram (ndarray): A list of 12 ints, one for each note value (C at index 0 through B at
        index 11). Each int is the total number of times that note occurred in
        the given NoteSequence.
    """
    note_pitches = [note.pitch for note in note_sequence.notes]
    np_notes = np.array(note_pitches, dtype=int)
    histogram = np.bincount(np_notes[np_notes >= constants.MIN_MIDI_PITCH] % constants.NOTES_PER_OCTAVE,
                            minlength=constants.NOTES_PER_OCTAVE)
    return histogram


def count_onsets(note_sequence: NoteSequence) -> int:
    """ Count the number of onset in a NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.

    Returns:
        onsets_count (int): The number of onsets in the given NoteSequence.
    """
    onsets = uniquify_unhashable_obj_list(note_sequence.notes, lambda a, b: float_equal(a.start_time, b.start_time))
    onsets_count = len(onsets)
    return onsets_count


def get_pitch_list(note_sequence: NoteSequence, unique: bool = False) -> List[int]:
    """ Returns a list of all pitches in the given NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.
        unique (bool): If True, returns a list containing only unique pitches. Default to False.

    Returns:
        pitch_list (List[int]): The list of all pitches in note_sequence.
    """
    pitch_list = [note.pitch for note in note_sequence.notes]
    return list(set(pitch_list)) if unique else pitch_list


def get_velocity_list(note_sequence: NoteSequence, unique: bool = False, normalize: bool = True) -> List[int]:
    """ Returns a list of all velocities in the given NoteSequence proto.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.
        unique (bool): If True, returns a list containing only unique velocities. Default to False.
        normalize (bool): If True, normalize the velocities by constants.MAX_MIDI_VELOCITY. Default to True.

    Returns:
        velocity_list (List[int]): The list of all velocities in note_sequence.
    """
    normalization_factor = constants.MAX_MIDI_VELOCITY if normalize else 1
    velocity_list = [note.velocity / normalization_factor for note in note_sequence.notes]
    return list(set(velocity_list)) if unique else velocity_list


def get_unique_notes(note_sequence: NoteSequence) -> List[NoteSequence.Note]:
    """ Returns a list of all unique notes in the given NoteSequence proto.
    Two notes are considered equal according to the function equal_notes (time checks are not included).

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.

    Returns:
        unique_notes_list (List[NoteSequence.Note]): The list of all unique notes in note_sequence.
    """
    unique_notes_list = uniquify_unhashable_obj_list(note_sequence.notes, equal_notes)
    return unique_notes_list


def get_unique_note_sequences(note_sequences: List[NoteSequence]) -> List[NoteSequence]:
    """ Returns a list of all unique NoteSequence proto in the given NoteSequence proto list.
    Two note sequences are considered equal according to the function equal_note_sequences.

    Args:
        note_sequences (List[NoteSequence]): A list of NoteSequence protos.

    Returns:
        unique_note_sequences_list (List[NoteSequence]): The list of unique note sequences.
    """
    unique_note_sequences_list = uniquify_unhashable_obj_list(note_sequences, equal_note_sequences)
    return unique_note_sequences_list


def equal_notes(note_a: NoteSequence.Note, note_b: NoteSequence.Note, check_times: bool = False) -> bool:
    """ Check whether two NoteSequence.Note protos are equal. Two notes are considered equal only if they have the same
    pitch. If check_times is True, also their start and end times must coincide.

    Args:
        note_a (NoteSequence.Note): A NoteSequence.Note proto.
        note_b (NoteSequence.Note): A NoteSequence.Note proto.
        check_times (bool): If True, check notes start and end times too.

    Returns:
        (bool): True if note_a and note_b are equal, False otherwise.
    """
    if note_a is None:
        return note_b is None
    elif note_b is None:
        return False

    times_check = True if not check_times else (float_equal(note_a.start_time, note_b.start_time) and
                                                float_equal(note_a.end_time, note_b.end_time))
    # TODO - equal_notes: Should we also check for velocity or other attributes equality?
    return note_a.pitch == note_b.pitch and times_check


def equal_note_sequences(note_sequence_a: NoteSequence, note_sequence_b: NoteSequence) -> bool:
    """ Check whether two NoteSequence protos are equal. Two note sequences are considered equal only if they have the
    same number of notes and all notes are equal (including time checks).

    Args:
        note_sequence_a (NoteSequence): A NoteSequence proto.
        note_sequence_b (NoteSequence): A NoteSequence proto.

    Returns:
        (bool): True if note_sequence_a and note_sequence_b are equal, False otherwise.
    """
    if len(note_sequence_a.notes) != len(note_sequence_b.notes):
        return False

    for note_a, note_b in zip(note_sequence_a.notes, note_sequence_b.notes):
        # TODO - equal_note_sequences: Should we also check for other attributes equality (CC, ecc) or notes equality
        #  is enough?
        if not equal_notes(note_a, note_b, check_times=True):
            return False

    return True


# ---------------------------------------- ASSERTS ----------------------------------------

def assert_is_quantized_sequence(note_sequence):
    """ Assert that the given NoteSequence proto has been quantized.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.

    Raises:
        QuantizationStatusError: If the sequence is not quantized.
    """
    if not is_quantized_sequence(note_sequence):
        raise exceptions.QuantizationStatusError('NoteSequence %s is not quantized.' % note_sequence.id)


def assert_is_relative_quantized_sequence(note_sequence):
    """ Assert that a NoteSequence proto has been quantized relative to tempo.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.

    Raises:
      QuantizationStatusError: If the sequence is not quantized relative to tempo.
    """
    if not is_relative_quantized_sequence(note_sequence):
        raise exceptions.QuantizationStatusError('NoteSequence %s is not quantized or is quantized based on absolute '
                                                 'timing.' % note_sequence.id)


def assert_is_absolute_quantized_sequence(note_sequence):
    """ Assert that a NoteSequence proto has been quantized by absolute time.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.

    Raises:
      QuantizationStatusError: If the sequence is not quantized by absolute time.
    """
    if not is_absolute_quantized_sequence(note_sequence):
        raise exceptions.QuantizationStatusError('NoteSequence %s is not quantized or is quantized based on relative '
                                                 'timing.' % note_sequence.id)


# ---------------------------------------- MATH ----------------------------------------

def float_equal(a: float, b: float, rel_tol=constants.FLOAT_RELATIVE_TOLERANCE,
                abs_tol=constants.FLOAT_ABSOLUTE_TOLERANCE):
    """ Check if two floating point numbers are approximately equal.

    Args:
        a (float): The first floating point number.
        b (float): The second floating point number.
        rel_tol (float): The relative tolerance parameter for the comparison.
        abs_tol (float): The absolute tolerance parameter for the comparison.

    Returns:
        (bool): True if the two numbers are approximately equal within the specified tolerance, False otherwise.
    """
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def float_less(a: float, b: float, rel_tol=constants.FLOAT_RELATIVE_TOLERANCE,
               abs_tol=constants.FLOAT_ABSOLUTE_TOLERANCE):
    """ Check if the first floating point number is less than the second floating point number.

    Args:
        a (float): The first floating point number.
        b (float): The second floating point number.
        rel_tol (float): The relative tolerance parameter for the comparison.
        abs_tol (float): The absolute tolerance parameter for the comparison.

    Returns:
        (bool): True if a < b within the specified tolerance, False otherwise.
    """
    return not float_equal(a, b, rel_tol, abs_tol) and a < b


def float_great(a: float, b: float, rel_tol=constants.FLOAT_RELATIVE_TOLERANCE,
                abs_tol=constants.FLOAT_ABSOLUTE_TOLERANCE):
    """ Check if the first floating point number is greater than the second floating point number.

    Parameters:
        a (float): The first floating point number.
        b (float): The second floating point number.
        rel_tol (float): The relative tolerance parameter for the comparison.
        abs_tol (float): The absolute tolerance parameter for the comparison.

    Returns:
        (bool): True if a > b within the specified tolerance, False otherwise.
    """
    return not float_equal(a, b, rel_tol, abs_tol) and a > b


def float_less_or_equal(a: float, b: float, rel_tol=constants.FLOAT_RELATIVE_TOLERANCE,
                        abs_tol=constants.FLOAT_ABSOLUTE_TOLERANCE):
    """ Check if the first floating point number is less than or approximately equal to the second floating point
    number.

    Args:
        a (float): The first floating point number.
        b (float): The second floating point number.
        rel_tol (float): The relative tolerance parameter for the comparison.
        abs_tol (float): The absolute tolerance parameter for the comparison.

    Returns:
        (bool): True if a <= b within the specified tolerance, False otherwise.
    """
    return float_equal(a, b, rel_tol, abs_tol) or a < b


def float_great_or_equal(a: float, b: float, rel_tol=constants.FLOAT_RELATIVE_TOLERANCE,
                         abs_tol=constants.FLOAT_ABSOLUTE_TOLERANCE):
    """ Check if the first floating point number is greater than or approximately equal to the second floating point
    number.

    Args:
        a (float): The first floating point number.
        b (float): The second floating point number.
        rel_tol (float): The relative tolerance parameter for the comparison.
        abs_tol (float): The absolute tolerance parameter for the comparison.

    Returns:
        (bool): True if a >= b within the specified tolerance, False otherwise.
    """
    return float_equal(a, b, rel_tol, abs_tol) or a > b


# ---------------------------------------- DATA ----------------------------------------

U = TypeVar('U')


def uniquify_unhashable_obj_list(unhashable_obj_list: List[U], equal_fn: Callable[[U, U], bool]) -> List[U]:
    """ Remove duplicate objects from a list while preserving the order.

    Args:
        unhashable_obj_list (List[U]): The list containing unhashable objects.
        equal_fn (Callable[[U, U], bool]): A function that compares two objects for equality.

    Returns:
        List[U]: A list of unique objects from the input list.
    """
    unique_objs = []
    for obj in unhashable_obj_list:
        if not any(equal_fn(obj, existing_obj) for existing_obj in unique_objs):
            unique_objs.append(obj)
    return unique_objs
