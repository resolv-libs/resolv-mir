""" This processor module contains functions used to extend the duration of a NoteSequence proto. """
from modules.libs.mir.note_sequence import utilities
from modules.libs.mir.protobuf.protos.symbolic_music_pb2 import NoteSequence


def extend_quantized_sequence_with_silence(note_sequence: NoteSequence):
    """ Extend a quantized NoteSequence with silence until the end of the last bar.

    This function extends a quantized NoteSequence with silence to fill the gap between the last note and the end of
    the last bar in the sequence. The added silence ensures that the NoteSequence covers the entire duration up to the
    end of the last bar, maintaining the quantization structure. Extension happens in place, thus no new NoteSequence
    is returned.

    Args:
        note_sequence (NoteSequence): The quantized NoteSequence to extend with silence.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    def _get_silence(end_step):
        s = NoteSequence.Note()
        s.start_time = note_sequence.total_quantized_steps / steps_per_second
        s.end_time = end_step / steps_per_second
        s.quantized_start_step = note_sequence.total_quantized_steps
        s.quantized_end_step = end_step
        s.velocity = 0
        return s

    utilities.assert_is_relative_quantized_sequence(note_sequence)
    steps_per_bar = utilities.steps_per_bar_in_quantized_sequence(note_sequence)
    steps_per_second = note_sequence.quantization_info.steps_per_second
    silence_end_step = utilities.bars_in_quantized_sequence(note_sequence) * steps_per_bar
    if silence_end_step != note_sequence.total_quantized_steps:
        silence = _get_silence(silence_end_step)
        note_sequence.notes.append(silence)
        note_sequence.total_quantized_steps = silence.quantized_end_step
        note_sequence.total_time = silence.end_time
