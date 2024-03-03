""" This module provides common operations used by the other modules to compute the metrics. """
from typing import Union

from .. import utilities
from resolv_mir.protobuf import NoteSequence


def get_metric_normalization_factor(note_sequence: NoteSequence) -> Union[int, float]:
    """ Get the normalization factor for metric evaluation.

    This function calculates the normalization factor based on the total quantized steps if the input NoteSequence
    is quantized, otherwise, it uses the total time.

    Args:
        note_sequence (NoteSequence): The NoteSequence for which to calculate the normalization factor.

    Returns:
        Union[int, float]: The normalization factor, either total quantized steps (int) or total time (float).
    """
    return note_sequence.total_quantized_steps if utilities.is_quantized_sequence(note_sequence) else (
        note_sequence.total_time)
