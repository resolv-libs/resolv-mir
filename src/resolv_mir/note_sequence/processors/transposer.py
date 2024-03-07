""" This processor module contains functions used to transpose a NoteSequence proto. """
from typing import Tuple

from .. import constants
from ...protobuf import NoteSequence


def transpose_note_sequence(note_sequence: NoteSequence,
                            amount: int,
                            min_allowed_pitch: int = constants.MIN_MIDI_PITCH,
                            max_allowed_pitch: int = constants.MAX_MIDI_PITCH,
                            transpose_chords: bool = True,
                            in_place: bool = False) -> Tuple[NoteSequence, int]:
    """ Transposes note sequence specified amount, deleting out-of-bound notes.

    Args:
        note_sequence (NoteSequence): The NoteSequence proto to be transposed.
        amount (int): Number of half-steps to transpose up or down.
        min_allowed_pitch (int): Minimum pitch allowed in transposed NoteSequence. Notes assigned lower pitches will
            be deleted.
        max_allowed_pitch (int): Maximum pitch allowed in transposed NoteSequence. Notes assigned higher pitches will
            be deleted.
        transpose_chords (int): If True, also transpose chord symbol text annotations. If False, chord symbols will be
            removed.
        in_place (int): If True, the input note_sequence is edited directly.

    Returns:
      (Tuple[NoteSequence, int]): The transposed NoteSequence and a count of how many notes were deleted.

    Raises:
      ChordSymbolError: If a chord symbol is unable to be transposed.
    """
    if not in_place:
        new_ns = NoteSequence()
        new_ns.CopyFrom(note_sequence)
        note_sequence = new_ns

    new_note_list = []
    deleted_note_count = 0
    end_time = 0

    for note in note_sequence.notes:
        new_pitch = note.pitch + amount
        if (min_allowed_pitch <= new_pitch <= max_allowed_pitch) or note.is_drum:
            end_time = max(end_time, note.end_time)

            if not note.is_drum:
                note.pitch += amount
                # The pitch name, if present, will no longer be valid.
                note.pitch_name = NoteSequence.UNKNOWN_PITCH_NAME

            new_note_list.append(note)
        else:
            deleted_note_count += 1

    if deleted_note_count > 0:
        del note_sequence.notes[:]
        note_sequence.notes.extend(new_note_list)

    # Since notes were deleted, we may need to update the total time.
    note_sequence.total_time = end_time

    if transpose_chords:
        # Also update the chord symbol text annotations. This can raise a
        # ChordSymbolError if a chord symbol cannot be interpreted.
        for ta in note_sequence.text_annotations:
            if ta.annotation_type == NoteSequence.TextAnnotation.CHORD_SYMBOL and ta.text != constants.NO_CHORD:
                ta.text = modules.libs.mir.note_sequence.chord_symbols.transposer.transpose_chord_symbol(ta.text, amount)
    else:
        # Remove chord symbol text annotations.
        text_annotations_to_keep = []
        for ta in note_sequence.text_annotations:
            if ta.annotation_type != NoteSequence.TextAnnotation.CHORD_SYMBOL:
                text_annotations_to_keep.append(ta)
        if len(text_annotations_to_keep) < len(note_sequence.text_annotations):
            del note_sequence.text_annotations[:]
            note_sequence.text_annotations.extend(text_annotations_to_keep)

    # Also transpose key signatures.
    for ks in note_sequence.key_signatures:
        ks.key = (ks.key + amount) % 12

    return note_sequence, deleted_note_count
