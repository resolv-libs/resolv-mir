""" TODO - Module doc """
from typing import List

from .. import utilities
from ...protobuf import NoteSequence

HOLD_NOTE_SYMBOL = 128
SILENCE_SYMBOL = 129


def pitch_sequence_representation(note_sequence: NoteSequence) -> List[int]:
    utilities.assert_is_quantized_sequence(note_sequence)
    representation = [SILENCE_SYMBOL] * note_sequence.total_quantized_steps
    for note in note_sequence.notes:
        representation[note.quantized_start_step] = note.pitch
        for i in range(note.quantized_start_step + 1, note.quantized_end_step):
            representation[i] = HOLD_NOTE_SYMBOL
    return representation
