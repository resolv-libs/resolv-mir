""" TODO - Module doc """
import logging
from typing import List, Dict, Any

from .. import utilities, constants
from ...protobuf import NoteSequence

HOLD_NOTE_SYMBOL = 128
SILENCE_SYMBOL = 129


def pitch_sequence_representation(note_sequence: NoteSequence) -> List[int]:
    utilities.assert_is_quantized_sequence(note_sequence)
    pitch_sequence = [SILENCE_SYMBOL] * note_sequence.total_quantized_steps
    for note in note_sequence.notes:
        pitch_sequence[note.quantized_start_step] = note.pitch
        for i in range(note.quantized_start_step + 1, note.quantized_end_step):
            pitch_sequence[i] = HOLD_NOTE_SYMBOL
    return pitch_sequence


def from_pitch_sequence(
        pitch_sequence: List[int],
        attributes: Dict[str, Any] = None,
        velocity: int = constants.DEFAULT_MIDI_VELOCITY,
        instrument: int = constants.DEFAULT_MIDI_CHANNEL,
        program: int = constants.DEFAULT_MIDI_PROGRAM,
        qpm: float = constants.DEFAULT_QUARTERS_PER_MINUTE) -> NoteSequence:
    # TODO - allow to specify the note sequence fields (tempos, time signature, ecc)
    note_sequence = NoteSequence()
    note_sequence.ticks_per_quarter = constants.STANDARD_PPQ

    if attributes:
        note_sequence.attributes.CopyFrom(NoteSequence.SequenceAttributes(**attributes))

    time_signature = note_sequence.time_signatures.add()
    time_signature.numerator = 4
    time_signature.denominator = 4

    tempo = note_sequence.tempos.add()
    tempo.qpm = qpm

    steps_per_quarter = 4
    total_quantized_steps = len(pitch_sequence)
    note_sequence.quantization_info.CopyFrom(NoteSequence.QuantizationInfo(steps_per_quarter=steps_per_quarter))
    steps_per_second = utilities.steps_per_quarter_to_steps_per_second(steps_per_quarter, tempo.qpm)
    note_sequence.total_quantized_steps = total_quantized_steps
    note_sequence.total_time = total_quantized_steps / steps_per_second

    current_note = None
    for step, pitch in enumerate(pitch_sequence):
        if pitch == HOLD_NOTE_SYMBOL:
            if not current_note:
                logging.warning("The given pitch sequence starts with a HOLD_NOTE symbol."
                                "Considering it as a silence note.")
                continue
        else:
            if current_note:
                current_note.quantized_end_step = step
                current_note.end_time = step / steps_per_second
            if pitch != SILENCE_SYMBOL:
                note = note_sequence.notes.add()
                note.instrument = instrument
                note.program = program
                note.quantized_start_step = step
                note.start_time = step / steps_per_second
                note.pitch = pitch
                note.velocity = velocity
                note.is_drum = False
                current_note = note
            else:
                current_note = None

    if current_note:
        current_note.quantized_end_step = total_quantized_steps
        current_note.end_time = total_quantized_steps / steps_per_second

    return note_sequence
