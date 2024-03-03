""" This processor module contains functions used to truncate a NoteSequence proto. """
from modules.libs.mir.note_sequence import utilities
from modules.libs.mir.protobuf.protos.symbolic_music_pb2 import NoteSequence


def truncate_quantized_sequence_at_step(note_sequence: NoteSequence, end_step: int):
    """ Truncates a quantized NoteSequence at a specified step.

    This function truncates a given quantized NoteSequence at the specified end step. All notes that extend beyond the
    end step are shortened to end at the specified step.

    Args:
        note_sequence (NoteSequence): The input quantized NoteSequence to be truncated.
        end_step (int): The step at which to truncate the NoteSequence.

    Returns:
        (NoteSequence): The truncated NoteSequence

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    utilities.assert_is_relative_quantized_sequence(note_sequence)
    del_note_index = 0
    steps_per_second = note_sequence.quantization_info.steps_per_second
    for idx, note in enumerate(note_sequence.notes):
        if note.quantized_end_step > end_step:
            del_note_index = idx + 1
            note.quantized_end_step = end_step
            note.end_time = end_step / steps_per_second

    del note_sequence.notes[:del_note_index]
    return note_sequence


def truncate_quantized_sequence_at_bar(note_sequence: NoteSequence, end_bar: int) -> NoteSequence:
    """ Truncates a quantized NoteSequence at a specified bar.

    This function truncates a given quantized NoteSequence at the specified end bar. All notes that extend beyond the
    end bar are shortened to end at the last step of the specified bar.

    Args:
        note_sequence (NoteSequence): The input quantized NoteSequence to be truncated.
        end_bar (int): The bar at which to truncate the NoteSequence.

    Returns:
        (NoteSequence): The truncated NoteSequence

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    utilities.assert_is_relative_quantized_sequence(note_sequence)
    end_step = utilities.steps_per_bar_in_quantized_sequence(note_sequence) * end_bar
    return truncate_quantized_sequence_at_step(note_sequence, end_step)
