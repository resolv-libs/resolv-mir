"""Input and output wrappers for converting between MIDI and other formats."""
import collections
import io
import sys
from pathlib import Path
from typing import Dict, Union, Any

import pretty_midi

from .utilities import populate_sequence_metadata
from .. import constants
from ..exceptions import MIDIConversionError
from resolv_mir.protobuf import NoteSequence

# Allow pretty_midi to read MIDI files with absurdly high tick rates.
# Useful for reading the MAPS dataset.
# https://github.com/craffel/pretty-midi/issues/112
# pretty_midi.pretty_midi.MAX_TICK = 1e10   TODO - pretty_midi.MAX_TICK: find another way for the MAPS dataset

# The offset used to change the mode of a key from major to minor when
# generating a PrettyMIDI KeySignature.
_PRETTY_MIDI_MAJOR_TO_MINOR_OFFSET = 12


def midi_to_note_sequence(midi_data: Union[pretty_midi.PrettyMIDI, bytes], metadata: Dict[str, Any] = None) \
        -> NoteSequence:
    """ Convert MIDI file content to a NoteSequence proto.

    Converts a MIDI file encoded as a string into a NoteSequence. Decoding errors are very common when working with
    large sets of MIDI files, so be sure to handle MIDIConversionError exceptions.

    Args:
        midi_data (Union[pretty_midi.PrettyMIDI, bytes]): A string containing the contents of a MIDI file or a
            populated pretty_midi.PrettyMIDI object.
        metadata (Dict[str, Any]): A dictionary containing metadata relative to the MIDI file (title, release, ecc...).

    Returns:
        (NoteSequence) A NoteSequence proto.

    Raises:
        MIDIConversionError: If improper MIDI data were supplied.
    """
    # In practice many MIDI files cannot be decoded with pretty_midi. Catch all
    # errors here and try to log a meaningful message. So many different
    # exceptions are raised in pretty_midi.PrettyMidi that it is cumbersome to
    # catch them all only for the purpose of error logging.
    # pylint: disable=bare-except
    if isinstance(midi_data, pretty_midi.PrettyMIDI):
        midi = midi_data
    else:
        try:
            midi = pretty_midi.PrettyMIDI(io.BytesIO(midi_data))
        except:
            raise MIDIConversionError('MIDI %s decoding error %s: %s' % (metadata['filepath'], sys.exc_info()[0],
                                                                         sys.exc_info()[1]))
    # pylint: enable=bare-except

    sequence = NoteSequence()

    # Populate header.
    sequence.ticks_per_quarter = midi.resolution
    sequence.source_info.parser = NoteSequence.SourceInfo.PRETTY_MIDI
    sequence.source_info.encoding_type = NoteSequence.SourceInfo.MIDI

    # Populate time signatures.
    for midi_time in midi.time_signature_changes:
        time_signature = sequence.time_signatures.add()
        time_signature.time = midi_time.time
        time_signature.numerator = midi_time.numerator
        try:
            # Denominator can be too large for int32.
            time_signature.denominator = midi_time.denominator
        except ValueError:
            raise MIDIConversionError('Invalid time signature denominator %d' %
                                      midi_time.denominator)

    # Populate key signatures.
    for midi_key in midi.key_signature_changes:
        key_signature = sequence.key_signatures.add()
        key_signature.time = midi_key.time
        key_signature.key = midi_key.key_number % 12
        midi_mode = midi_key.key_number // 12
        if midi_mode == 0:
            key_signature.mode = key_signature.MAJOR
        elif midi_mode == 1:
            key_signature.mode = key_signature.MINOR
        else:
            raise MIDIConversionError('Invalid midi_mode %i' % midi_mode)

    # Populate tempo changes.
    tempo_times, tempo_qpms = midi.get_tempo_changes()
    for time_in_seconds, tempo_in_qpm in zip(tempo_times, tempo_qpms):
        tempo = sequence.tempos.add()
        tempo.time = time_in_seconds
        tempo.qpm = tempo_in_qpm

    # Populate notes by gathering them all from the midi's instruments.
    # Also set the sequence.total_time as the max end time in the notes.
    midi_notes = []
    midi_pitch_bends = []
    midi_control_changes = []
    for num_instrument, midi_instrument in enumerate(midi.instruments):
        # Populate instrument name from the midi's instruments
        if midi_instrument.name:
            instrument_info = sequence.instrument_infos.add()
            instrument_info.name = midi_instrument.name
            instrument_info.instrument = num_instrument
        for midi_note in midi_instrument.notes:
            if not sequence.total_time or midi_note.end > sequence.total_time:
                sequence.total_time = midi_note.end
            midi_notes.append((midi_instrument.program, num_instrument,
                               midi_instrument.is_drum, midi_note))
        for midi_pitch_bend in midi_instrument.pitch_bends:
            midi_pitch_bends.append(
                (midi_instrument.program, num_instrument,
                 midi_instrument.is_drum, midi_pitch_bend))
        for midi_control_change in midi_instrument.control_changes:
            midi_control_changes.append(
                (midi_instrument.program, num_instrument,
                 midi_instrument.is_drum, midi_control_change))

    for program, instrument, is_drum, midi_note in midi_notes:
        note = sequence.notes.add()
        note.instrument = instrument
        note.program = program
        note.start_time = midi_note.start
        note.end_time = midi_note.end
        note.pitch = midi_note.pitch
        note.velocity = midi_note.velocity
        note.is_drum = is_drum

    for program, instrument, is_drum, midi_pitch_bend in midi_pitch_bends:
        pitch_bend = sequence.pitch_bends.add()
        pitch_bend.instrument = instrument
        pitch_bend.program = program
        pitch_bend.time = midi_pitch_bend.time
        pitch_bend.bend = midi_pitch_bend.pitch
        pitch_bend.is_drum = is_drum

    for program, instrument, is_drum, midi_control_change in midi_control_changes:
        control_change = sequence.control_changes.add()
        control_change.instrument = instrument
        control_change.program = program
        control_change.time = midi_control_change.time
        control_change.control_number = midi_control_change.number
        control_change.control_value = midi_control_change.value
        control_change.is_drum = is_drum

    # TODO - MIDI conversion: Estimate note type (e.g. quarter note) and populate note.numerator and note.denominator.

    sequence = populate_sequence_metadata(sequence, 'midi', metadata)

    return sequence


def midi_file_to_note_sequence(midi_file: Union[str, Path]) -> NoteSequence:
    """ Convert a MIDI file to a NoteSequence proto.

    Args:
        midi_file (Union[str, Path]): A Path object or string path to a MIDI file.

    Returns:
        (NoteSequence) A NoteSequence proto.

    Raises:
        MIDIConversionError: If improper MIDI data were supplied.
    """
    with open(midi_file, 'rb') as f:
        midi_as_string = f.read()
        return midi_to_note_sequence(midi_as_string)


def note_sequence_to_midi(note_sequence: NoteSequence, drop_events_n_seconds_after_last_note: float = None) \
        -> pretty_midi.PrettyMIDI:
    """ Convert a NoteSequence proto to a PrettyMIDI object.

    Time is stored in the NoteSequence in absolute values (seconds) as opposed to relative values (MIDI ticks). When
    the NoteSequence is translated back to PrettyMIDI the absolute time is retained. The tempo map is also recreated.

    Args:
        note_sequence (NoteSequence): A NoteSequence.
        drop_events_n_seconds_after_last_note (float): Events (e.g., time signature changes) that occur this many
            seconds after the last note will be dropped. If None, then no events will be dropped.

    Returns:
        (pretty_midi.PrettyMIDI): A pretty_midi.PrettyMIDI object or None if sequence could not be decoded.
    """
    ticks_per_quarter = note_sequence.ticks_per_quarter or constants.STANDARD_PPQ

    max_event_time = None
    if drop_events_n_seconds_after_last_note is not None:
        max_event_time = (max([n.end_time for n in note_sequence.notes] or [0]) +
                          drop_events_n_seconds_after_last_note)

    # Try to find a tempo at time zero. The list is not guaranteed to be in order.
    initial_seq_tempo = None
    for seq_tempo in note_sequence.tempos:
        if seq_tempo.time == 0:
            initial_seq_tempo = seq_tempo
            break

    kwargs = {}
    if initial_seq_tempo:
        kwargs['initial_tempo'] = initial_seq_tempo.qpm
    else:
        kwargs['initial_tempo'] = constants.DEFAULT_QUARTERS_PER_MINUTE

    pm = pretty_midi.PrettyMIDI(resolution=ticks_per_quarter, **kwargs)

    # Create an empty instrument to contain time and key signatures.
    instrument = pretty_midi.Instrument(0)
    pm.instruments.append(instrument)

    # Populate time signatures.
    for seq_ts in note_sequence.time_signatures:
        if max_event_time and seq_ts.time > max_event_time:
            continue
        time_signature = pretty_midi.containers.TimeSignature(
            seq_ts.numerator, seq_ts.denominator, seq_ts.time)
        pm.time_signature_changes.append(time_signature)

    # Populate key signatures.
    for seq_key in note_sequence.key_signatures:
        if max_event_time and seq_key.time > max_event_time:
            continue
        key_number = seq_key.key
        if seq_key.mode == seq_key.MINOR:
            key_number += _PRETTY_MIDI_MAJOR_TO_MINOR_OFFSET
        key_signature = pretty_midi.containers.KeySignature(
            key_number, seq_key.time)
        pm.key_signature_changes.append(key_signature)

    # Populate tempos.
    # TODO - MIDI conversion: Update this code if pretty_midi adds the ability to write tempo.
    for seq_tempo in note_sequence.tempos:
        # Skip if this tempo was added in the PrettyMIDI constructor.
        if seq_tempo == initial_seq_tempo:
            continue
        if max_event_time and seq_tempo.time > max_event_time:
            continue
        tick_scale = 60.0 / (pm.resolution * seq_tempo.qpm)
        tick = pm.time_to_tick(seq_tempo.time)
        # pylint: disable=protected-access
        pm._tick_scales.append((tick, tick_scale))
        pm._update_tick_to_time(0)
        # pylint: enable=protected-access

    # Populate instrument names by first creating an instrument map between
    # instrument index and name.
    # Then, going over this map in the instrument event for loop
    inst_infos = {}
    for inst_info in note_sequence.instrument_infos:
        inst_infos[inst_info.instrument] = inst_info.name

    # Populate instrument events by first gathering notes and other event types
    # in lists then write them sorted to the PrettyMidi object.
    instrument_events = collections.defaultdict(lambda: collections.defaultdict(list))
    for seq_note in note_sequence.notes:
        instrument_events[(seq_note.instrument, seq_note.program,
                           seq_note.is_drum)]['notes'].append(
            pretty_midi.Note(
                seq_note.velocity, seq_note.pitch,
                seq_note.start_time, seq_note.end_time))
    for seq_bend in note_sequence.pitch_bends:
        if max_event_time and seq_bend.time > max_event_time:
            continue
        instrument_events[(seq_bend.instrument, seq_bend.program,
                           seq_bend.is_drum)]['bends'].append(
            pretty_midi.PitchBend(seq_bend.bend, seq_bend.time))
    for seq_cc in note_sequence.control_changes:
        if max_event_time and seq_cc.time > max_event_time:
            continue
        instrument_events[(seq_cc.instrument, seq_cc.program,
                           seq_cc.is_drum)]['controls'].append(
            pretty_midi.ControlChange(
                seq_cc.control_number,
                seq_cc.control_value, seq_cc.time))

    for (instr_id, prog_id, is_drum) in sorted(instrument_events.keys()):
        # For instr_id 0 append to the instrument created above.
        if instr_id > 0:
            if is_drum:
                name = 'Drums'
            else:
                name = pretty_midi.program_to_instrument_name(prog_id)
            instrument = pretty_midi.Instrument(prog_id, is_drum, name)
            pm.instruments.append(instrument)
        else:
            instrument.is_drum = is_drum
        # propagate instrument name to the midi file
        instrument.program = prog_id
        if instr_id in inst_infos:
            instrument.name = inst_infos[instr_id]
        instrument.notes = instrument_events[
            (instr_id, prog_id, is_drum)]['notes']
        instrument.pitch_bends = instrument_events[
            (instr_id, prog_id, is_drum)]['bends']
        instrument.control_changes = instrument_events[
            (instr_id, prog_id, is_drum)]['controls']

    return pm


def note_sequence_to_midi_file(note_sequence: NoteSequence, output_file: Union[str, Path],
                               drop_events_n_seconds_after_last_note: float = None):
    """ Convert NoteSequence proto to a MIDI file on disk.

    Time is stored in the NoteSequence in absolute values (seconds) as opposed to relative values (MIDI ticks). When
    the NoteSequence is translated back to MIDI the absolute time is retained. The tempo map is also recreated.

    Args:
        note_sequence (NoteSequence): A NoteSequence.
        output_file (Union[str, Path]): String path to MIDI file that will be written.
        drop_events_n_seconds_after_last_note (float): Events (e.g., time signature changes) that occur this many
            seconds after the last note will be dropped. If None, then no events will be dropped.
    """
    pretty_midi_object = note_sequence_to_midi(note_sequence, drop_events_n_seconds_after_last_note)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    pretty_midi_object.write(open(output_file, 'wb'))
