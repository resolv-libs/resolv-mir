""" This processor module contains functions used to stretch a NoteSequence proto. """
import itertools

from .. import exceptions, utilities
from ...protobuf import NoteSequence


def stretch_note_sequence(note_sequence: NoteSequence, stretch_factor: float, in_place: bool = False):
    """ Apply a constant temporal stretch to a NoteSequence proto.

    Args:
        note_sequence (NoteSequence): The NoteSequence proto to stretch.
        stretch_factor (float): How much to stretch the NoteSequence. Values greater than one increase the length of
            the NoteSequence (making it "slower"). Values less than one decrease the length of the NoteSequence
            (making it "faster").
        in_place (bool): If True, the input note_sequence is edited directly.

    Returns:
        (NoteSequence): A stretched copy of the original NoteSequence.

    Raises:
        QuantizationStatusError: If the `note_sequence` is quantized. Only un-quantized NoteSequences can be stretched.
    """
    if utilities.is_quantized_sequence(note_sequence):
        raise exceptions.QuantizationStatusError('Can only stretch un-quantized NoteSequence.')

    if in_place:
        stretched_sequence = note_sequence
    else:
        stretched_sequence = NoteSequence()
        stretched_sequence.CopyFrom(note_sequence)

    if stretch_factor == 1.0:
        return stretched_sequence

    # Stretch all notes.
    for note in stretched_sequence.notes:
        note.start_time *= stretch_factor
        note.end_time *= stretch_factor
    stretched_sequence.total_time *= stretch_factor

    # Stretch all other event times.
    events = itertools.chain(
        stretched_sequence.time_signatures, stretched_sequence.key_signatures,
        stretched_sequence.tempos, stretched_sequence.pitch_bends,
        stretched_sequence.control_changes, stretched_sequence.text_annotations)
    for event in events:
        event.time *= stretch_factor

    # Stretch tempos.
    for tempo in stretched_sequence.tempos:
        tempo.qpm /= stretch_factor

    return stretched_sequence
