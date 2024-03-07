""" This processor module contains functions used to extract subsequences from a NoteSequence proto. """
import copy
import logging
from typing import List, Tuple, Dict, Any

import numpy as np

from .. import constants, exceptions, processors, statistics, utilities
from ...protobuf import NoteSequence


def extract_melodies_from_note_sequence(quantized_sequence: NoteSequence,
                                        search_start_step: int = 0,
                                        max_bars_truncate: int = None,
                                        min_bars: int = None,
                                        max_bars_discard: int = None,
                                        min_unique_pitches: int = None,
                                        min_pitch: int = constants.PIANO_MIN_MIDI_PITCH,
                                        max_pitch: int = constants.PIANO_MAX_MIDI_PITCH,
                                        gap_bars: int = 1,
                                        ignore_polyphonic_notes: bool = False,
                                        filter_drums: bool = True,
                                        valid_programs: List[int] = constants.MEL_PROGRAMS) -> List[NoteSequence]:
    """ Extracts a list of melodies from the given quantized NoteSequence.

    This function will search through quantized_sequence for monophonic melodies in every track at every time step.

    Once a note-on event in a track is encountered, a melody begins. Gaps of silence in each track will be splitting
    points that divide the track into separate melodies. The minimum size of these gaps are given in gap_bars.
    The size of a bar of music in time steps is computed from the time signature stored in quantized_sequence.

    The melody is then checked for validity. The melody is only used if it is at least min_bars long, and has at
    least min_unique_pitches unique notes (preventing melodies that only repeat a few notes, such as those found in
    some accompaniment tracks, from being used).

    After scanning each instrument track in the quantized sequence, a list of all extracted melodies is returned along
    with some statistic:
        - polyphonic_tracks_discarded: number of discarded polyphonic melodies. Greater than zero only if
            ignore_polyphonic_notes is set to False.
        - non_integer_steps_per_bar_tracks_discarded: number of discarded melodies because of a
            NonIntegerStepsPerBarError exception.
        - melodies_discarded_too_short: number of melodies discarded because shorter than min_bars.
        - melodies_discarded_too_long: number of melodies discarded because longer than max_bars_discard.
        - melodies_truncated: number of melodies discarded because longer than max_bars_truncate.
        - melody_lengths_in_bars: a statistic.Histogram showing the distribution of the length for the extracted
            melodies.

    Args:
        quantized_sequence (NoteSequence): A quantized NoteSequence proto.
        search_start_step (int): Start searching for a melody at this time step. Assumed to be the first step of a bar.
        min_bars (int): Minimum length of melodies in number of bars. Shorter melodies are discarded.
        max_bars_truncate (int): Maximum number of bars in extracted melodies. If defined, longer melodies are truncated
            to this threshold.
        max_bars_discard (int): Maximum number of bars in extracted melodies. If defined, longer melodies are discarded.
        gap_bars (int): A melody comes to an end when this number of bars (measures) of silence is encountered.
        min_unique_pitches (int): Minimum number of unique notes with octave equivalence. Melodies with too few unique
            notes are discarded.
        min_pitch (int): Consider only notes whose pitch is above this number. Default to 21 (the minimum possible
            pitch in a piano)
        max_pitch (int): Consider only notes whose pitch is below this number. Default to 108 (the maximum possible
            pitch in a piano)
        ignore_polyphonic_notes (bool): If True, melodies will be extracted from quantized_sequence tracks that contain
            polyphony (notes start at the same time). If False, tracks with polyphony will be ignored.
        filter_drums (bool): If True, notes for which is_drum is True will be ignored.
        valid_programs (List[int]): Notes whose program is not in this list will be ignored.

    Returns:
        melodies: A python list of Melody instances.
        stats: A dictionary mapping string names to statistics.Statistic objects.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """

    def _init_stats() -> Dict[str, Any]:
        s = dict((stat_name, statistics.Counter(stat_name)) for stat_name in
                 ['polyphonic_tracks_discarded',
                  'non_integer_steps_per_bar_tracks_discarded',
                  'melodies_discarded_too_short',
                  'melodies_discarded_too_few_pitches',
                  'melodies_discarded_too_long',
                  'melodies_truncated'])
        # Create a histogram measuring melody lengths (in bars not steps). Capture melodies that are very small, in the
        # range of the filter lower bound `min_bars`, and large. The bucket intervals grow approximately
        # exponentially.
        s['melody_lengths_in_bars'] = statistics.Histogram(
            'melody_lengths_in_bars',
            [0, 1, 10, 20, 30, 40, 50, 100, 200, 500, min_bars // 2, min_bars, min_bars + 1, min_bars - 1]
        )
        return s

    utilities.assert_is_relative_quantized_sequence(quantized_sequence)

    melodies: List[NoteSequence] = []
    stats = _init_stats()
    instruments = set(n.instrument for n in quantized_sequence.notes)
    steps_per_bar = int(utilities.steps_per_bar_in_quantized_sequence(quantized_sequence))
    for instrument in instruments:
        instrument_search_start_step = search_start_step
        while True:
            try:
                melody = processors.extractor.extract_melody_from_note_sequence(
                    quantized_sequence,
                    instrument=instrument,
                    search_start_step=instrument_search_start_step,
                    gap_bars=gap_bars,
                    min_pitch=min_pitch,
                    max_pitch=max_pitch,
                    ignore_polyphonic_notes=ignore_polyphonic_notes,
                    filter_drums=filter_drums,
                    valid_programs=valid_programs)
            except exceptions.PolyphonicMelodyError:
                stats['polyphonic_tracks_discarded'].increment()
                break  # Look for monophonic melodies in other tracks.
            except exceptions.NonIntegerStepsPerBarError:
                stats['non_integer_steps_per_bar_tracks_discarded'].increment()
                break

            if not melody:
                break

            # Truncate melodies that are too long.
            max_steps_truncate = steps_per_bar * max_bars_truncate if max_bars_truncate else None
            if max_steps_truncate is not None and melody.total_quantized_steps > max_steps_truncate:
                melody = processors.truncator.truncate_quantized_sequence_at_step(melody, max_steps_truncate)
                stats['melodies_truncated'].increment()

            # Start search for next melody on next bar boundary (inclusive).
            instrument_search_start_step += melody.total_quantized_steps
            instrument_search_start_step = steps_per_bar * ((instrument_search_start_step // steps_per_bar) + 1)

            # Require a certain melody length.
            if melody.total_quantized_steps < steps_per_bar * min_bars:
                stats['melodies_discarded_too_short'].increment()
                continue

            # Discard melodies that are too long.
            max_step_discard = steps_per_bar * max_bars_discard if max_bars_discard else None
            if max_step_discard is not None and melody.total_quantized_steps > max_step_discard:
                stats['melodies_discarded_too_long'].increment()
                continue

            # Require a certain number of unique pitches.
            note_histogram = utilities.get_note_pitches_histogram_for_note_sequence(melody)
            unique_pitches = np.count_nonzero(note_histogram)
            if unique_pitches < min_unique_pitches:
                stats['melodies_discarded_too_few_pitches'].increment()
                continue

            # TODO - Melody Extraction: add filter for rhythmic diversity.

            stats['melody_lengths_in_bars'].increment(melody.total_quantized_steps // steps_per_bar)

            melodies.append(melody)

    return melodies, stats


def extract_melody_from_note_sequence(quantized_sequence: NoteSequence,
                                      search_start_step: int = 0,
                                      min_pitch: int = constants.PIANO_MIN_MIDI_PITCH,
                                      max_pitch: int = constants.PIANO_MAX_MIDI_PITCH,
                                      instrument: int = 0,
                                      gap_bars: int = 1,
                                      ignore_polyphonic_notes: bool = False,
                                      filter_drums: bool = True,
                                      valid_programs: List[int] = constants.MEL_PROGRAMS) -> NoteSequence:
    """ Extract a melody from the given quantized NoteSequence.

    A monophonic melody is extracted from the given instrument starting at search_start_step. instrument and
    search_start_step can be used to drive extraction of multiple melodies from the same quantized sequence.

    The melody extraction is ended when there are no held notes for a time stretch of  gap_bars in bars of music.
    The number of time steps per bar is computed from the time signature in quantized_sequence.

    ignore_polyphonic_notes determines what happens when polyphonic (multiple notes start at the same time) data is
    encountered. If ignore_polyphonic_notes is True, the highest pitch is used in the melody when multiple notes start
    at the same time. If False, an exception is raised.

    Args:
        quantized_sequence (NoteSequence): A quantized NoteSequence proto.
        search_start_step (int): Start searching for a melody at this time step. Assumed to be the first step of a bar.
        min_pitch (int): Consider only notes whose pitch is above this number. Default to 21 (the minimum possible
            pitch in a piano)
        max_pitch (int): Consider only notes whose pitch is below this number. Default to 108 (the maximum possible
            pitch in a piano)
        instrument (int): Search for a melody in this instrument number.
        gap_bars (int): If this many bars or more follow a NOTE_OFF event, the melody is ended.
        ignore_polyphonic_notes (bool): If True, the highest pitch is used in the melody when multiple notes start at
            the same time. If False, PolyphonicMelodyError will be raised if multiple notes start at the same time.
        filter_drums (bool): If True, notes for which `is_drum` is True will be ignored.
        valid_programs (List[int]): Notes whose program is not in this list will be ignored.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
        PolyphonicMelodyError: If any of the notes start on the same step and `ignore_polyphonic_notes` is False.
    """

    def _copy_note_to_melody(target_melody, old_note, start_s, end_s, start_t, end_t):
        new_note = copy.deepcopy(old_note)
        new_note.start_time = start_t
        new_note.end_time = end_t
        new_note.quantized_start_step = start_s
        new_note.quantized_end_step = end_s
        target_melody.notes.append(new_note)

    utilities.assert_is_relative_quantized_sequence(quantized_sequence)

    steps_per_bar_float = utilities.steps_per_bar_in_quantized_sequence(quantized_sequence)
    time_signature = quantized_sequence.time_signatures[0]
    if steps_per_bar_float % 1 != 0:
        raise exceptions.NonIntegerStepsPerBarError('There are %f timesteps per bar. Time signature: %d/%d' %
                                                    (steps_per_bar_float,
                                                     time_signature.numerator,
                                                     time_signature.denominator))
    steps_per_bar = int(steps_per_bar_float)
    steps_per_second = utilities.steps_per_second_in_quantized_sequence(quantized_sequence)

    # Filter notes by search start step and instruments
    notes = [n for n in quantized_sequence.notes if n.instrument == instrument and n.program in valid_programs and
             n.quantized_start_step >= search_start_step and min_pitch <= n.pitch <= max_pitch]
    # Sort track by note start times, and secondarily by pitch descending.
    notes = sorted(notes, key=lambda n: (n.quantized_start_step, -n.pitch))

    if not notes:
        return None

    melody = copy.deepcopy(quantized_sequence)
    del melody.text_annotations[:]
    del melody.pitch_bends[:]
    del melody.control_changes[:]
    del melody.instrument_infos[:]
    del melody.notes[:]

    melody_start_step = notes[0].quantized_start_step - (
            notes[0].quantized_start_step - search_start_step) % steps_per_bar
    melody_start_time = melody_start_step / steps_per_second
    for note in notes:
        # Filter drums and Ignore 0 velocity notes.
        if (filter_drums and note.is_drum) or not note.velocity:
            continue

        # Compute note step and time relative to the melody
        note_start_step = note.quantized_start_step - melody_start_step
        note_start_time = note_start_step / steps_per_second
        note_end_step = note.quantized_end_step - melody_start_step
        note_end_time = note_end_step / steps_per_second

        if not melody.notes:
            # If there are no events, we don't need to check for polyphony.
            _copy_note_to_melody(melody, note, note_start_step, note_end_step, note_start_time, note_end_time)
            continue

        # If `start_index` comes before or lands on an already added note's start step, we cannot add it. In that case
        # either discard the melody or keep the highest pitch.
        last_note: NoteSequence.Note = melody.notes[-1]
        on_distance = note_start_step - last_note.quantized_start_step
        off_distance = note_end_step - last_note.quantized_end_step
        if on_distance == 0:
            # TODO - Melody extraction: convert `ignore_polyphonic_notes` into a float which controls the degree of
            #  polyphony that is acceptable.
            if ignore_polyphonic_notes:
                # TODO - Melody extraction: not sure that this approach is a good definition of a melody
                # Keep the highest note.
                # Notes are sorted by pitch descending, so if a note is already at this position it's the highest pitch.
                continue
            else:
                raise exceptions.PolyphonicMelodyError()
        elif on_distance < 0:
            raise exceptions.PolyphonicMelodyError('Unexpected note. Not in ascending order.')

        # If a gap of `gap` or more steps is found, end the melody.
        if len(melody.notes) and off_distance >= gap_bars * steps_per_bar:
            break

        # End any sustained notes.
        if last_note.quantized_end_step > note_start_step:
            last_note.quantized_end_step = note_start_step
            last_note.end_time = note_start_time

        # Add the note-on and off events to the melody.
        _copy_note_to_melody(melody, note, note_start_step, note_end_step, note_start_time, note_end_time)

    if not melody.notes:
        # If no notes were added, don't set `_start_step` and `_end_step`.
        return None
    else:
        # Populate melody info and annotations from original sequence
        melody.total_quantized_steps = melody.notes[-1].quantized_end_step
        melody.total_time = melody.notes[-1].end_time

    # Populate Control Change events
    for cc in quantized_sequence.control_changes:
        if (utilities.float_less_or_equal(melody_start_time, cc.time) and
                utilities.float_less(cc.time, melody.total_time) and cc.instrument == instrument
                and cc.program in valid_programs):
            new_cc = copy.deepcopy(cc)
            melody.control_changes.append(new_cc)

    # Populate Pitch Bend events
    for pb in quantized_sequence.pitch_bends:
        if (utilities.float_less_or_equal(melody_start_time, pb.time) and
                utilities.float_less(pb.time, melody.total_time) and pb.instrument == instrument
                and pb.program in valid_programs):
            new_pb = copy.deepcopy(pb)
            melody.pitch_bends.append(new_pb)

    # Populate Instrument Infos
    for ii in quantized_sequence.instrument_infos:
        if ii.instrument == instrument:
            new_ii = copy.deepcopy(ii)
            melody.instrument_infos.append(new_ii)

    # Populate Text Annotation
    for ta in quantized_sequence.text_annotations:
        if (utilities.float_less_or_equal(melody_start_time, ta.time) and
                utilities.float_less(ta.time, melody.total_time)):
            new_ta = copy.deepcopy(ta)
            melody.pitch_bends.append(new_ta)

    return melody


def extract_ngrams_from_note_sequence(note_sequence: NoteSequence, n: int = 2) -> List[NoteSequence]:
    """ Extracts n-grams from a given NoteSequence.
    Currently, the function extracts n-grams with a fixed stride window of 1.

    Args:
        note_sequence (NoteSequence): The input NoteSequence from which n-grams are to be extracted.
        n (int, optional): The size of the n-grams to extract. Defaults to 2.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the extracted n-grams.
    """
    if not note_sequence.notes:
        return []

    # TODO - Ngrams extraction: parametrize the stride window for extracting the ngrams (now it is fixed to 1)
    subsequences_intervals: List[Tuple[float, float]] = []
    for i in range(len(note_sequence.notes) - n + 1):
        subsequence_start_time = note_sequence.notes[i].start_time
        subsequence_end_time = note_sequence.notes[i + n - 1].end_time
        subsequences_intervals.append((subsequence_start_time, subsequence_end_time))

    return extract_subsequences(note_sequence, subsequences_intervals) if subsequences_intervals else []


def extract_repetitive_subsequences(sequence: NoteSequence, min_repetitions: int = 2) -> List[NoteSequence]:
    """ Extracts repetitive subsequences from a given NoteSequence.
    Repetitive subsequences are defined as consecutive subsequences of notes that are identical in pitch (see function
    equal_notes in the utilities module). The function identifies repetitive subsequences by comparing consecutive notes
    in the input sequence and a subsequence is considered repetitive if it repeats at least min_repetitions times
    consecutively. Subsequences that do not meet the minimum repetitions requirement are discarded.

    Args:
        sequence (NoteSequence): The input NoteSequence from which repetitive subsequences are to be extracted.
        min_repetitions (int, optional): The minimum number of repetitions required for a subsequence to be considered
            repetitive. Defaults to 2.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the extracted repetitive subsequences.
     """
    if not sequence.notes:
        return []

    subsequences_intervals: List[Tuple[float, float]] = []
    notes_by_start_time: List[NoteSequence.Note] = sorted(sequence.notes, key=lambda n: n.start_time)
    previous_note: NoteSequence.Note = notes_by_start_time[0]
    del notes_by_start_time[0]
    repetitions: int = 1
    subsequence_start_time: float = previous_note.start_time
    subsequence_end_time: float = previous_note.end_time
    for note in notes_by_start_time:
        if utilities.equal_notes(note, previous_note):
            repetitions += 1
            subsequence_end_time = note.end_time
        else:
            if repetitions >= min_repetitions:
                subsequences_intervals.append((subsequence_start_time, subsequence_end_time))
            else:
                logging.debug(f"Discarding repetitive subsequence of length {repetitions}. "
                              f"Minimum is {min_repetitions}.")
            repetitions = 1
            subsequence_start_time = note.start_time
            subsequence_end_time = note.end_time
        previous_note = note

    return extract_subsequences(sequence, subsequences_intervals) if subsequences_intervals else []


def extract_subsequences(sequence: NoteSequence, subsequences_intervals: List[Tuple[float, float]],
                         preserve_control_numbers: List[int] = None) -> List[NoteSequence]:
    """ Extracts subsequences from a given NoteSequence based on specified intervals.
    This function preserves the state of time signatures, key signatures, tempos, and chord changes
    across the subsequences.

    Args:
        sequence (NoteSequence): The input NoteSequence from which subsequences are to be extracted.
        subsequences_intervals (List[Tuple[float, float]]): A list of tuples representing start and end times
            in seconds defining the intervals from which subsequences will be extracted.
        preserve_control_numbers (List[int], optional): A list of control numbers to be preserved when extracting
            control changes (e.g., pedal events). Defaults to None.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the extracted subsequences.

    Raises:
        ValueError: If subsequences_intervals is empty or if any interval extends past the end of the sequence.
    """

    def _check_time_in_interval(time: float, interval: Tuple[float, float]):
        return utilities.float_less_or_equal(interval[0], time) and utilities.float_less(time, interval[1])

    if not subsequences_intervals:
        raise ValueError('Must provide at least a start and end time.')
    if any(utilities.float_great(time, sequence.total_time) for time in [e for t in subsequences_intervals for e in t]):
        raise ValueError('Cannot extract subsequence past end of sequence.')

    if preserve_control_numbers is None:
        preserve_control_numbers = constants.DEFAULT_SUBSEQUENCE_PRESERVE_CONTROL_NUMBERS

    # Init subsequences
    subsequence = NoteSequence()
    subsequence.CopyFrom(sequence)
    subsequence.total_time = 0.0
    del subsequence.notes[:]
    del subsequence.time_signatures[:]
    del subsequence.key_signatures[:]
    del subsequence.tempos[:]
    del subsequence.text_annotations[:]
    del subsequence.control_changes[:]
    del subsequence.pitch_bends[:]
    subsequences = [copy.deepcopy(subsequence) for _ in range(len(subsequences_intervals))]

    # Sort subsequences intervals by start time
    subsequences_intervals = sorted(subsequences_intervals, key=lambda x: x[0])
    first_subsequence_start_time = subsequences_intervals[0][0]

    # Extract notes into subsequences.
    for note in sorted(sequence.notes, key=lambda e: e.start_time):
        # Skip note if it starts before the first subsequence start time
        if utilities.float_less(note.start_time, first_subsequence_start_time):
            continue
        for idx, subsequences_interval in enumerate(subsequences_intervals):
            current_subsequence = subsequences[idx]
            subsequence_start_time = subsequences_interval[0]
            subsequence_end_time = subsequences_interval[1]
            # Add note to sequence only if it is in its interval
            if _check_time_in_interval(note.start_time, subsequences_interval):
                current_subsequence.notes.append(note)
                new_note = current_subsequence.notes[-1]
                new_note.start_time -= subsequence_start_time
                # Truncate end time if the note continue after subsequence end time
                new_note.end_time = min(new_note.end_time, subsequence_end_time) - subsequence_start_time
                if utilities.float_great(new_note.end_time, current_subsequence.total_time):
                    current_subsequence.total_time = new_note.end_time

    # Extract time signatures, key signatures, tempos, and chord changes (beats are handled below, other text
    # annotations and pitch bends are deleted). Additional state events will be added to the beginning of each
    # subsequence.
    events_by_type = [
        sequence.time_signatures, sequence.key_signatures, sequence.tempos,
        [
            annotation for annotation in sequence.text_annotations
            if annotation.annotation_type == NoteSequence.TextAnnotation.CHORD_SYMBOL
        ]
    ]
    new_event_containers = [[s.time_signatures for s in subsequences],
                            [s.key_signatures for s in subsequences],
                            [s.tempos for s in subsequences],
                            [s.text_annotations for s in subsequences]]
    for events, containers in zip(events_by_type, new_event_containers):
        previous_events: List = [None] * len(subsequences)
        for event in sorted(events, key=lambda e: e.time):
            for idx, subsequences_interval in enumerate(subsequences_intervals):
                subsequence_start_time = subsequences_interval[0]
                if utilities.float_less(event.time, subsequence_start_time):
                    # Save event to previous state. Since events are sorted by time at the end only the most recent
                    # event will be considered
                    previous_events[idx] = event
                elif _check_time_in_interval(event.time, subsequences_interval):
                    # Only add the event if it's actually inside the subsequence (and not
                    # on the boundary with the next one).
                    containers[idx].append(event)
                    containers[idx][-1].time -= subsequence_start_time
        # Add state events to the beginning of the subsequences only if the container is empty (e.g. previous state is
        # still valid)
        for idx, event in enumerate(previous_events):
            if event and not containers[idx]:
                containers[idx].append(event)
                containers[idx][-1].time = 0.0

    # Copy stateless events to subsequences. Unlike the stateful events above, stateless events do not have an effect
    # outside the subsequence in which they occur.
    stateless_events_by_type = [[
        annotation for annotation in sequence.text_annotations
        if annotation.annotation_type in NoteSequence.TextAnnotation.BEAT
    ]]
    new_stateless_event_containers = [[s.text_annotations for s in subsequences]]
    for events, containers in zip(stateless_events_by_type, new_stateless_event_containers):
        for event in sorted(events, key=lambda e: e.time):
            if utilities.float_less(event.time, first_subsequence_start_time):
                continue
            for idx, subsequences_interval in enumerate(subsequences_intervals):
                subsequence_start_time = subsequences_interval[0]
                if _check_time_in_interval(event.time, subsequences_interval):
                    containers[idx].append(event)
                    containers[idx][-1].time -= subsequence_start_time

    # Extract piano pedal events (other control changes are deleted). Pedal state is maintained per-instrument and
    # added to the beginning of each subsequence.
    pedal_events = [cc for cc in sequence.control_changes if cc.control_number in preserve_control_numbers]
    previous_pedal_events: List[dict] = [{}] * len(subsequences)
    for pedal_event in sorted(pedal_events, key=lambda e: e.time):
        for idx, subsequences_interval in enumerate(subsequences_intervals):
            subsequence_start_time = subsequences_interval[0]
            if utilities.float_less(pedal_event.time, subsequence_start_time):
                previous_pedal_events[idx][(pedal_event.instrument, pedal_event.control_number)] = pedal_event
            elif _check_time_in_interval(pedal_event.time, subsequences_interval):
                subsequences[idx].control_changes.append(pedal_event)
                subsequences[idx].control_changes[-1].time -= subsequence_start_time

    # Quantize subsequences if necessary
    if utilities.is_absolute_quantized_sequence(sequence):
        steps_per_second = sequence.quantization_info.steps_per_second
        for idx, subsequence in enumerate(subsequences):
            subsequences[idx] = processors.quantizer.quantize_note_sequence_absolute(subsequence, steps_per_second)
    elif utilities.is_relative_quantized_sequence(sequence):
        steps_per_quarter = sequence.quantization_info.steps_per_quarter
        for idx, subsequence in enumerate(subsequences):
            subsequences[idx] = processors.quantizer.quantize_note_sequence(subsequence, steps_per_quarter)

    # Set subsequence info for all subsequences.
    for subsequence, start_time in [(x, y) for x, (y, _) in zip(subsequences, subsequences_intervals)]:
        subsequence.subsequence_info.start_time_offset = start_time
        subsequence.subsequence_info.end_time_offset = (sequence.total_time - start_time - subsequence.total_time)

    # Filter empty subsequences
    subsequences = [subsequence for subsequence in subsequences if subsequence.notes]

    return subsequences
