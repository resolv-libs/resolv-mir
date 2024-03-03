""" This module contains functions to compute metrics regarding the dynamic of a NoteSequence proto. """
from math import floor
from typing import List

from . import common
from .. import constants, processors, utilities
from resolv_mir.protobuf import NoteSequence


def dynamic_range(note_sequence: NoteSequence) -> float:
    """ Compute the dynamic range of a NoteSequence proto.

    The dynamic range is defined as the difference between the maximum and minimum velocities
    of the notes in the NoteSequence, normalized by the maximum MIDI velocity.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto.

    Returns:
        (float): The dynamic range of the NoteSequence, normalized between 0 and 1.
    """
    notes_velocity = [n.velocity for n in note_sequence.notes]
    return (max(notes_velocity) - min(notes_velocity)) / constants.MAX_MIDI_VELOCITY


def length_longest_repetitive_section(note_sequence: NoteSequence, min_repetitions: int = 2) -> float:
    """ Compute the length of the longest repetitive section in a NoteSequence proto.

    A repetitive section is defined as a note that consecutively repeats at least 'min_repetitions' times
    within the NoteSequence.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto.
        min_repetitions (int, optional): The minimum number of repetitions required to consider a section
            as repetitive. Defaults to 2.

    Returns:
        (float): The length of the longest repetitive section normalized by the total duration of the sequence,
            or 0.0 if no repetitive sections are found.
    """
    repetitive_subsequences = processors.extractor.extract_repetitive_subsequences(note_sequence, min_repetitions)
    normalization_factor = common.get_metric_normalization_factor(note_sequence)
    return max([len(ns.notes) for ns in repetitive_subsequences]) / normalization_factor if repetitive_subsequences \
        else 0.0


def ratio_note_change(note_sequence: NoteSequence) -> float:
    """ Compute the ratio of note changes to the total duration of a NoteSequence.

    A note change is counted each time a note with different pitch.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto

    Returns:
        (float): The ratio of note changes to the total duration of the sequence.
    """
    change_count = 0
    previous_note = None
    for note in sorted(note_sequence.notes, key=lambda n: n.start_time):
        if previous_note and not utilities.equal_notes(previous_note, note):
            change_count += 1
        previous_note = note
    normalization_factor = common.get_metric_normalization_factor(note_sequence)
    return change_count / normalization_factor


def ratio_repetitive_sections(note_sequence: NoteSequence, min_repetitions: int = 4) -> float:
    """ Compute the ratio of the number of repetitive sections to the total duration of a NoteSequence.

    A repetitive section is a note that repeats consecutively at least `min_repetitions` times.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto.
        min_repetitions (int, optional): The minimum number of repetitions required for a section to be considered
            repetitive. Defaults to 4.

    Returns:
        (float): The ratio of the number of repetitive sections to the total duration of the sequence.
    """
    repetitive_subsequences = processors.extractor.extract_repetitive_subsequences(note_sequence, min_repetitions)
    normalization_factor = floor(common.get_metric_normalization_factor(note_sequence) / min_repetitions)
    return len(repetitive_subsequences) / normalization_factor if repetitive_subsequences else 0.0


def ratio_hold_note_steps(note_sequence: NoteSequence) -> float:
    """ Compute the ratio of total steps where a note is hold to the total number of steps in a quantized NoteSequence.

    Args:
        note_sequence (NoteSequence): The input quantized NoteSequence proto.

    Returns:
        (float): The ratio of total "hold" steps to the total number of steps in the sequence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    utilities.assert_is_quantized_sequence(note_sequence)
    total_hold_note_steps = 0
    notes_by_start_time: List[NoteSequence.Note] = sorted(note_sequence.notes, key=lambda n: n.start_time)
    for note in notes_by_start_time:
        hold_note_steps = note.quantized_end_step - note.quantized_start_step
        total_hold_note_steps += hold_note_steps - 1
    return total_hold_note_steps / note_sequence.total_quantized_steps


def ratio_note_off_steps(note_sequence: NoteSequence) -> float:
    """ Compute the ratio of the total number of note off steps (silence, no notes playing) to the total number of
    steps in a quantized NoteSequence.

    Args:
        note_sequence (NoteSequence): The input quantized NoteSequence proto.

    Returns:
        (float): The ratio of the total number of note off steps to the total number of steps in the sequence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    utilities.assert_is_quantized_sequence(note_sequence)
    notes_by_start_time: List[NoteSequence.Note] = sorted(note_sequence.notes, key=lambda n: n.start_time)
    previous_note: NoteSequence.Note = notes_by_start_time[0]
    total_note_off_steps = previous_note.quantized_start_step
    for note in notes_by_start_time[1:]:
        silence_steps_between_notes = note.quantized_start_step - previous_note.quantized_end_step
        total_note_off_steps += silence_steps_between_notes
        previous_note = note
    total_note_off_steps += note_sequence.total_quantized_steps - previous_note.quantized_end_step
    return total_note_off_steps / note_sequence.total_quantized_steps
