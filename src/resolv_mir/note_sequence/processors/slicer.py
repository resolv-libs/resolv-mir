""" This processor module contains functions used to slice a NoteSequence proto in subsequences. """
from typing import List

from .. import processors, utilities
from ...protobuf import NoteSequence


def slice_note_sequence(note_sequence: NoteSequence, slice_size_seconds: float, hop_size_seconds: float,
                        start_time: float = 0, skip_splits_inside_notes: bool = False,
                        allow_cropped_slices: bool = False) -> List[NoteSequence]:
    """ Slice a NoteSequence into smaller subsequences of a fixed duration.

    This function divides a given NoteSequence into smaller subsequences, each of which has a fixed duration specified
    by slice_size_seconds. The slicing process starts at start_time and moves forward by hop_size_seconds until
    the end of the sequence is reached. Each slice is represented as a NoteSequence proto.
    The processors.extractor.extract_subsequences function is used internally to extract the subsequences
    based on the computed slice intervals.

    Args:
        note_sequence (NoteSequence): The input NoteSequence proto to be sliced.
        slice_size_seconds (float): The duration of each slice in seconds.
        hop_size_seconds (float): The time interval between the start times of consecutive slices in seconds.
        start_time (float, optional): The time in seconds ath which the slicing of the NoteSequence will start.
            Defaults to 0 (start of the sequence).
        skip_splits_inside_notes (bool, optional): If True, skips creating slices that fall within a note.
            Defaults to False.
        allow_cropped_slices (bool, optional): If True, allows slices to be cropped at the end of the NoteSequence
            if their duration exceeds the remaining sequence duration. If False, such slices are discarded.
            Defaults to False.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the sliced subsequences.
    """
    # Compute slices intervals
    total_time = note_sequence.total_time
    current_time = start_time
    slices_times = []
    notes_by_start_time = sorted(list(note_sequence.notes), key=lambda note: note.start_time)
    note_idx = 0
    notes_crossing_split = []
    while utilities.float_less_or_equal(current_time, total_time):
        slice_start = current_time
        slice_end = current_time + slice_size_seconds

        # If the slice goes beyond the end of the sequence, check whether to crop it to the end or discard it
        if utilities.float_great(slice_end, total_time):
            if allow_cropped_slices:
                slice_end = total_time
            else:
                break

        while (note_idx < len(notes_by_start_time) and
               utilities.float_less(notes_by_start_time[note_idx].start_time, slice_start)):
            notes_crossing_split.append(notes_by_start_time[note_idx])
            note_idx += 1

        if not (skip_splits_inside_notes and notes_crossing_split):
            slices_times.append((slice_start, slice_end))

        current_time += hop_size_seconds

    return processors.extractor.extract_subsequences(note_sequence, slices_times)


def slice_note_sequence_in_bars(note_sequence: NoteSequence, slice_size_bars: int, hop_size_bars: int,
                                start_time: float = 0, skip_splits_inside_notes: bool = False,
                                allow_cropped_slices: bool = False) -> List[NoteSequence]:
    """ Slices a NoteSequence into subsequences of specified length in bars with a specified hop size.

    This function slices a given NoteSequence into subsequences of a fixed duration specified in bars, with a specified
    hop size also in bars. The resulting slices are returned as a list of NoteSequence objects.

    Args:
        note_sequence (NoteSequence): The input NoteSequence to be sliced.
        slice_size_bars (int): The length of each slice in bars.
        hop_size_bars (int): The hop size between consecutive slices in bars.
        start_time (float, optional): The time in seconds ath which the slicing of the NoteSequence will start.
            Defaults to 0 (start of the sequence).
        skip_splits_inside_notes (bool, optional): If True, skips splitting notes that cross the boundaries of slices.
            Defaults to False.
        allow_cropped_slices (bool, optional): If True, allows slices that exceed the total time of the sequence to
            be cropped to fit within the sequence duration. If False, such slices are discarded. Defaults to False.

    Returns:
        List[NoteSequence]: A list of NoteSequence objects representing the sliced subsequences.

    Raises:
        QuantizationStatusError: If note_sequence is not quantized relative to tempo.
    """
    utilities.assert_is_relative_quantized_sequence(note_sequence)
    slice_size_seconds = utilities.bars_length_in_quantized_sequence(note_sequence, slice_size_bars)
    hop_size_seconds = utilities.bars_length_in_quantized_sequence(note_sequence, hop_size_bars)
    return slice_note_sequence(note_sequence, slice_size_seconds, hop_size_seconds, start_time,
                               skip_splits_inside_notes, allow_cropped_slices)
