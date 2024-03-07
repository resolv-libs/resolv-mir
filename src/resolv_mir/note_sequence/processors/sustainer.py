""" This processor module contains functions used to sustain a NoteSequence proto. """
import collections
import copy
import logging
import operator

from .. import exceptions, utilities
from ...protobuf import NoteSequence

# Constants for processing the note/sustain stream.
# The order here matters because we want to process 'on' events before we process 'off' events, and we want to process
# sustain events before note events.
_SUSTAIN_ON = 0
_SUSTAIN_OFF = 1
_NOTE_ON = 2
_NOTE_OFF = 3


def apply_sustain_control_changes(note_sequence: NoteSequence, sustain_control_number: int = 64) -> NoteSequence:
    """ Returns a new NoteSequence with sustain pedal control changes applied.

    Extends each note within a sustain to either the beginning of the next note of the same pitch or the end of the
    sustain period, whichever happens first. This is done on a per-instrument basis, so notes are only affected by
    sustain events for the same instrument. Drum notes will not be modified.

    Args:
        note_sequence (NoteSequence): The NoteSequence for which to apply sustain. This object will not be modified.
        sustain_control_number (int): The MIDI control number for sustain pedal. Control events with this number and
            value 0-63 will be treated as sustain pedal OFF events, and control events with this number and value
            64-127 will be treated as sustain pedal ON events.

    Returns:
      (NoteSequence): A copy of note_sequence but with note end times extended to account for sustain.

    Raises:
      QuantizationStatusError: If `note_sequence` is quantized. Sustain can only be applied to un-quantized note
        sequences.
    """
    if utilities.is_quantized_sequence(note_sequence):
        raise exceptions.QuantizationStatusError('Can only apply sustain control changes to un-quantized NoteSequence.')

    sequence = copy.deepcopy(note_sequence)

    # Sort all note on/off and sustain on/off events.
    events = []
    events.extend([(note.start_time, _NOTE_ON, note) for note in sequence.notes if not note.is_drum])
    events.extend([(note.end_time, _NOTE_OFF, note) for note in sequence.notes if not note.is_drum])

    for cc in sequence.control_changes:
        if cc.control_number != sustain_control_number:
            continue
        value = cc.control_value
        if value < 0 or value > 127:
            logging.warning('Sustain control change has out of range value: %d', value)
        if value >= 64:
            events.append((cc.time, _SUSTAIN_ON, cc))
        elif value < 64:
            events.append((cc.time, _SUSTAIN_OFF, cc))

    # Sort, using the time and event type constants to ensure the order events are processed.
    events.sort(key=operator.itemgetter(0, 1))

    # Lists of active notes, keyed by instrument.
    active_notes = collections.defaultdict(list)
    # Whether sustain is active for a given instrument.
    sus_active = collections.defaultdict(lambda: False)

    # Iterate through all sustain on/off and note on/off events in order.
    time = 0
    for time, event_type, event in events:
        if event_type == _SUSTAIN_ON:
            sus_active[event.instrument] = True
        elif event_type == _SUSTAIN_OFF:
            sus_active[event.instrument] = False
            # End all notes for the instrument that were being extended.
            new_active_notes = []
            for note in active_notes[event.instrument]:
                if note.end_time < time:
                    # This note was being extended because of sustain.
                    # Update the end time and don't keep it in the list.
                    note.end_time = time
                    if time > sequence.total_time:
                        sequence.total_time = time
                else:
                    # This note is actually still active, keep it.
                    new_active_notes.append(note)
            active_notes[event.instrument] = new_active_notes
        elif event_type == _NOTE_ON:
            if sus_active[event.instrument]:
                # If sustain is on, end all previous notes with the same pitch.
                new_active_notes = []
                for note in active_notes[event.instrument]:
                    if note.pitch == event.pitch:
                        note.end_time = time
                        if note.start_time == note.end_time:
                            # This note now has no duration because another note of the same
                            # pitch started at the same time. Only one of these notes should
                            # be preserved, so delete this one.
                            # TODO(fjord): A more correct solution would probably be to
                            # preserve both notes and make the same duration, but that is a
                            # little more complicated to implement. Will keep this solution
                            # until we find that we need the more complex one.
                            sequence.notes.remove(note)
                    else:
                        new_active_notes.append(note)
                active_notes[event.instrument] = new_active_notes
            # Add this new note to the list of active notes.
            active_notes[event.instrument].append(event)
        elif event_type == _NOTE_OFF:
            if sus_active[event.instrument]:
                # Note continues until another note of the same pitch or sustain ends.
                pass
            else:
                # Remove this particular note from the active list.
                # It may have already been removed if a note of the same pitch was
                # played when sustain was active.
                if event in active_notes[event.instrument]:
                    active_notes[event.instrument].remove(event)
        else:
            raise AssertionError('Invalid event_type: %s' % event_type)

    # End any notes that were still active due to sustain.
    for instrument in active_notes.values():
        for note in instrument:
            note.end_time = time
            sequence.total_time = time

    return sequence
