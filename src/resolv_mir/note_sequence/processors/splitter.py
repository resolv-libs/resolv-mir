""" This processor module contains functions used to split a NoteSequence proto in subsequences. """
from typing import List, Union

from modules.libs.mir.note_sequence import constants, processors, utilities
from modules.libs.mir.protobuf.protos.symbolic_music_pb2 import NoteSequence


def split_note_sequence(note_sequence: NoteSequence, hop_size_seconds: Union[float, List[float]],
                        skip_splits_inside_notes: bool = False) -> List[NoteSequence]:
    """ Split one NoteSequence proto into many at specified time intervals.

    If hop_size_seconds is a scalar, this function splits a NoteSequence into multiple NoteSequences, all of fixed size
    (unless split_notes is False, in which case splits that would have truncated notes will be skipped; i.e. each split
    will either happen at a multiple of `hop_size_seconds` or not at all). Each of the resulting NoteSequences is
    shifted to start at time zero.

    If hop_size_seconds is a list, the NoteSequence will be split at each time in the list (unless split_notes is False
    as above).

    Args:
        note_sequence (NoteSequence): The NoteSequence to split.
        hop_size_seconds (Union[float, List[float]]): The hop size, in seconds, at which the NoteSequence will be split.
            Alternatively, this can be a list of times in seconds at which to split the NoteSequence.
        skip_splits_inside_notes (bool): If False, the NoteSequence will be split at all hop positions, regardless of
            whether any notes are sustained across the potential split time, thus sustained notes will be truncated. If
            True, the NoteSequence will not be split at positions that occur within sustained notes.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the split subsequences.
    """

    def _get_masked_array(array, mask):
        return [e for e, m in zip(array, mask) if m]

    # Create split intervals
    if not isinstance(hop_size_seconds, list):
        split_intervals = []
        current_time = 0
        while utilities.float_less(current_time, note_sequence.total_time):
            end_time = min(current_time + hop_size_seconds, note_sequence.total_time)
            split_intervals.append((current_time, end_time))
            current_time += hop_size_seconds
    else:
        split_intervals = []
        current_time = 0
        for split_point in sorted(hop_size_seconds):
            end_time = min(split_point, note_sequence.total_time)
            split_intervals.append((current_time, end_time))
            current_time = end_time
        split_intervals.append((current_time, note_sequence.total_time))

    # Compute valid intervals according to skip_splits_inside_notes flag
    valid_split_intervals = split_intervals
    if skip_splits_inside_notes:
        valid_split_intervals_mask: List[bool] = [True] * len(split_intervals)
        for note in sorted(list(note_sequence.notes), key=lambda n: n.start_time):
            for idx, split_interval in enumerate(split_intervals):
                interval_start = split_interval[0]
                interval_end = split_interval[1]
                if (utilities.float_great(note.start_time, interval_start) and
                        utilities.float_great(note.end_time, interval_end)):
                    valid_split_intervals_mask[idx] = False
        valid_split_intervals = _get_masked_array(split_intervals, valid_split_intervals_mask)

    if len(valid_split_intervals) > 1:
        return processors.extractor.extract_subsequences(note_sequence, valid_split_intervals)
    else:
        return [note_sequence]


def split_note_sequence_in_bars(note_sequence: NoteSequence, n_bars: int, skip_splits_inside_notes: bool = False) -> \
        List[NoteSequence]:
    """ Splits a NoteSequence into subsequences of specified length in bars.

    This function splits a given NoteSequence into subsequences of a fixed duration specified in bars. The resulting
    slices are returned as a list of NoteSequence objects.

    Args:
        note_sequence (NoteSequence): The input NoteSequence to be split.
        n_bars (int): The length of each split in bars.
        skip_splits_inside_notes (bool, optional): If True, skips splitting notes that cross the boundaries of splits.
            Defaults to False.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the split subsequences.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    utilities.assert_is_relative_quantized_sequence(note_sequence)
    hop_size_seconds = utilities.bars_length_in_quantized_sequence(note_sequence, n_bars)
    return split_note_sequence(note_sequence, hop_size_seconds, skip_splits_inside_notes)


def split_note_sequence_on_time_changes(note_sequence: NoteSequence, skip_splits_inside_notes: bool = False) -> \
        List[NoteSequence]:
    """ Split one NoteSequence into many around time signature and tempo changes.

    This function splits a NoteSequence into multiple NoteSequences, each of which contains only a single time signature
    and tempo, unless split_notes is False in which case all time signature and tempo changes occur within sustained
    notes. Each of the resulting NoteSequences is shifted to start at time zero.

    Args:
        note_sequence (NoteSequence): The NoteSequence proto to split.
        skip_splits_inside_notes (bool): If False, the NoteSequence will be split at all time changes, regardless of
            whether any notes are sustained across the time change. If True, the NoteSequence will not be split at time
            changes that occur within sustained notes.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the split subsequences.
    """
    # Get time signature and tempo changes events
    time_signatures_and_tempos = sorted(list(note_sequence.time_signatures) + list(note_sequence.tempos),
                                        key=lambda t: t.time)
    time_signatures_and_tempos = [t for t in time_signatures_and_tempos if t.time < note_sequence.total_time]

    current_numerator = 4
    current_denominator = 4
    current_qpm = constants.DEFAULT_QUARTERS_PER_MINUTE
    notes_by_start_time = sorted(list(note_sequence.notes), key=lambda note: note.start_time)
    note_idx = 0
    notes_crossing_split = []
    valid_split_times = []
    previous_split_time = (0.0, 0.0)
    for event in time_signatures_and_tempos:
        if isinstance(event, NoteSequence.TimeSignature):
            if event.numerator == current_numerator and event.denominator == current_denominator:
                # Time signature didn't actually change.
                continue
        else:
            if event.qpm == current_qpm:
                # Tempo didn't actually change.
                continue

        # Update notes crossing potential split.
        while (note_idx < len(notes_by_start_time) and
               utilities.float_less(notes_by_start_time[note_idx].start_time, event.time)):
            notes_crossing_split.append(notes_by_start_time[note_idx])
            note_idx += 1
        notes_crossing_split = [note for note in notes_crossing_split if note.end_time > event.time]

        previous_end_time = previous_split_time[1]
        if utilities.float_great(event.time, previous_end_time):
            if not (skip_splits_inside_notes and notes_crossing_split):
                split_time = (previous_end_time, event.time)
                valid_split_times.append(split_time)
                previous_split_time = split_time

        # Even if we didn't split here, update the current time signature or tempo.
        if isinstance(event, NoteSequence.TimeSignature):
            current_numerator = event.numerator
            current_denominator = event.denominator
        else:
            current_qpm = event.qpm

    # Handle the final subsequence.
    last_event_end_time = previous_split_time[1]
    if utilities.float_great(note_sequence.total_time, last_event_end_time):
        valid_split_times.append((last_event_end_time, note_sequence.total_time))

    if len(valid_split_times) > 1:
        return processors.extractor.extract_subsequences(note_sequence, valid_split_times)
    else:
        return [note_sequence]


def split_note_sequence_on_silence(note_sequence: NoteSequence, gap_seconds: float = 3.0) -> List[NoteSequence]:
    """ Split one NoteSequence into many around gaps of silence.

    This function splits a NoteSequence into multiple NoteSequences, each of which contains no gaps of silence longer
    than gap_seconds. Each of the resulting NoteSequences is shifted such that the first note starts at time zero.

    Args:
      note_sequence (NoteSequence): The NoteSequence proto to split.
      gap_seconds (float): The maximum amount of contiguous silence to allow within a NoteSequence, in seconds.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the split subsequences.
    """
    split_times = []
    previous_split_time = (0.0, 0.0)
    last_active_time = 0.0

    for note in sorted(list(note_sequence.notes), key=lambda e: e.start_time):
        if utilities.float_great(note.start_time, last_active_time + gap_seconds):
            split_time = (previous_split_time[1], note.start_time)
            split_times.append(split_time)
            previous_split_time = split_time
        last_active_time = max(last_active_time, note.end_time)

    last_end_time = previous_split_time[1]
    if utilities.float_great(note_sequence.total_time, last_end_time):
        split_times.append((last_end_time, note_sequence.total_time))

    if len(split_times) > 1:
        processors.extractor.extract_subsequences(note_sequence, split_times)
    else:
        return [note_sequence]
