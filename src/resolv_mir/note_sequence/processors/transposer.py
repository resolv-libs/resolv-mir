""" This processor module contains functions used to transpose a NoteSequence proto. """
from typing import Tuple

from .. import constants
from ..chord_symbols import transposer as chord_transposer
from ...protobuf import NoteSequence


def transpose_note_sequence(note_sequence: NoteSequence,
                            amount: int,
                            min_allowed_pitch: int = constants.MIN_MIDI_PITCH,
                            max_allowed_pitch: int = constants.MAX_MIDI_PITCH,
                            transpose_chords: bool = True,
                            in_place: bool = False,
                            delete_notes: bool = True) -> Tuple[NoteSequence, int]:
    """ Transposes note sequence specified amount.

    Args:
        note_sequence (NoteSequence): The NoteSequence proto to be transposed.
        amount (int): Number of half-steps to transpose up or down.
        min_allowed_pitch (int): Minimum pitch allowed in transposed NoteSequence. Notes assigned lower pitches will
            be deleted.
        max_allowed_pitch (int): Maximum pitch allowed in transposed NoteSequence. Notes assigned higher pitches will
            be deleted.
        transpose_chords (int): If True, also transpose chord symbol text annotations. If False, chord symbols will be
            removed.
        in_place (bool): If True, the input note_sequence is edited directly.
        delete_notes (bool): if True, out-of-bound notes will be deleted, else the transposed note will be transposed
            again up or down by octaves until it lays inside the desired bounds. Note: if the specified bound doesn't
            contain the transposed note (in any octave) it will be deleted anyway.

    Returns:
      (Tuple[NoteSequence, int]): The transposed NoteSequence and a count of how many notes were deleted.

    Raises:
      ChordSymbolError: If a chord symbol is unable to be transposed.
    """
    def transpose_note_pitch(n: NoteSequence.Note):
        new_pitch = n.pitch + amount
        if not delete_notes:
            while new_pitch > max_allowed_pitch:
                new_pitch -= constants.NOTES_PER_OCTAVE
            while new_pitch < min_allowed_pitch:
                new_pitch += constants.NOTES_PER_OCTAVE
        return new_pitch

    if min_allowed_pitch > max_allowed_pitch:
        raise ValueError('min_allowed_pitch should be <= max_allowed_pitch')

    if not in_place:
        new_ns = NoteSequence()
        new_ns.CopyFrom(note_sequence)
        note_sequence = new_ns

    new_note_list = []
    deleted_note_count = 0
    end_time = 0
    for note in note_sequence.notes:
        if note.is_drum:
            end_time = max(end_time, note.end_time)
            new_note_list.append(note)
        else:
            transposed_pitch = transpose_note_pitch(note)
            if min_allowed_pitch <= transposed_pitch <= max_allowed_pitch:
                end_time = max(end_time, note.end_time)
                note.pitch = transposed_pitch
                # The pitch name, if present, will no longer be valid.
                # TODO - populate the correct transposed pitch name (also according to key)
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
                ta.text = chord_transposer.transpose_chord_symbol(ta.text, amount)
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
        ks.key = (ks.key + amount) % constants.NOTES_PER_OCTAVE

    return note_sequence, deleted_note_count


def transpose_note_sequence_to_key(note_sequence: NoteSequence,
                                   key: NoteSequence.KeySignature.Key,
                                   transpose_chords: bool = True,
                                   in_place: bool = False) -> Tuple[NoteSequence, int]:
    if key is None:
        return note_sequence
    # TODO - Transpose to key implementation
    return note_sequence
