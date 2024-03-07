""" This processor module contains functions used to quantized a NoteSequence proto. """
import copy
import itertools

from .. import constants, exceptions, utilities
from ...protobuf import NoteSequence


def quantize_note_sequence(note_sequence: NoteSequence, steps_per_quarter: int) -> NoteSequence:
    """ Quantize a NoteSequence proto relative to tempo.

    The input NoteSequence is copied and quantization-related fields are populated. Sets the steps_per_quarter field
    in the quantization_info message in the NoteSequence.

    Note start and end times, and chord times are snapped to a nearby quantized step, and the resulting times are
    stored in a separate field (e.g. quantized_start_step). See the comments above QUANTIZE_CUTOFF in constants module
    for details on how the quantizing algorithm works.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.
        steps_per_quarter (int): Each quarter note of music will be divided into this many quantized time steps.

    Returns:
        qns (NoteSequence): A copy of the original NoteSequence, with quantized times added.

    Raises:
        MultipleTimeSignatureError: If there is a change in time signature in note_sequence.
        MultipleTempoError: If there is a change in tempo in note_sequence.
        BadTimeSignatureError: If the time signature found in note_sequence has a 0 numerator or a denominator which is
            not a power of 2.
        NegativeTimeError: If a note or chord occurs at a negative time.
    """

    def _is_power_of_2(x):
        return x and not x & (x - 1)

    qns = copy.deepcopy(note_sequence)

    qns.quantization_info.steps_per_quarter = steps_per_quarter

    if qns.time_signatures:
        time_signatures = sorted(qns.time_signatures, key=lambda ts: ts.time)
        # There is an implicit 4/4 time signature at 0 time. So if the first time signature is something other than
        # 4/4, and it's at a time other than 0, that's an implicit time signature change.
        if time_signatures[0].time != 0 and not (time_signatures[0].numerator == 4 and
                                                 time_signatures[0].denominator == 4):
            raise exceptions.MultipleTimeSignatureError(
                'NoteSequence has an implicit change from initial 4/4 time signature to '
                '%d/%d at %.2f seconds.' % (time_signatures[0].numerator,
                                            time_signatures[0].denominator,
                                            time_signatures[0].time))

        for time_signature in time_signatures[1:]:
            if (time_signature.numerator != qns.time_signatures[0].numerator or time_signature.denominator !=
                    qns.time_signatures[0].denominator):
                raise exceptions.MultipleTimeSignatureError(
                    'NoteSequence has at least one time signature change from %d/%d to '
                    '%d/%d at %.2f seconds.' % (time_signatures[0].numerator,
                                                time_signatures[0].denominator,
                                                time_signature.numerator,
                                                time_signature.denominator,
                                                time_signature.time))

        # Make it clear that there is only 1 time signature, and it starts at the beginning.
        qns.time_signatures[0].time = 0
        del qns.time_signatures[1:]
    else:
        time_signature = qns.time_signatures.add()
        time_signature.numerator = 4
        time_signature.denominator = 4
        time_signature.time = 0

    if not _is_power_of_2(qns.time_signatures[0].denominator):
        raise exceptions.BadTimeSignatureError('Denominator is not a power of 2. Time signature: %d/%d' %
                                               (qns.time_signatures[0].numerator, qns.time_signatures[0].denominator))

    if qns.time_signatures[0].numerator == 0:
        raise exceptions.BadTimeSignatureError('Numerator is 0. Time signature: %d/%d' %
                                               (qns.time_signatures[0].numerator, qns.time_signatures[0].denominator))

    if qns.tempos:
        tempos = sorted(qns.tempos, key=lambda t: t.time)
        # There is an implicit 120.0 qpm tempo at 0 time. So if the first tempo is
        # something other that 120.0, and it's at a time other than 0, that's an
        # implicit tempo change.
        if tempos[0].time != 0 and (tempos[0].qpm != constants.DEFAULT_QUARTERS_PER_MINUTE):
            raise exceptions.MultipleTempoError(
                'NoteSequence has an implicit tempo change from initial %.1f qpm to %.1f qpm at'
                ' %.2f seconds.' % (constants.DEFAULT_QUARTERS_PER_MINUTE, tempos[0].qpm,
                                    tempos[0].time))

        for tempo in tempos[1:]:
            if tempo.qpm != qns.tempos[0].qpm:
                raise exceptions.MultipleTempoError(
                    'NoteSequence has at least one tempo change from %.1f qpm to %.1f qpm at %.2f '
                    'seconds.' % (tempos[0].qpm, tempo.qpm, tempo.time))

        # Make it clear that there is only 1 tempo, and it starts at the beginning.
        qns.tempos[0].time = 0
        del qns.tempos[1:]
    else:
        tempo = qns.tempos.add()
        tempo.qpm = constants.DEFAULT_QUARTERS_PER_MINUTE
        tempo.time = 0

    # Compute quantization steps per second.
    steps_per_second = utilities.steps_per_quarter_to_steps_per_second(steps_per_quarter, qns.tempos[0].qpm)
    qns.total_quantized_steps = quantize_to_step(qns.total_time, steps_per_second)
    _quantize_notes(qns, steps_per_second)

    return qns


def quantize_note_sequence_absolute(note_sequence: NoteSequence, steps_per_second: float):
    """ Quantize a NoteSequence proto using absolute event times.

    The input NoteSequence is copied and quantization-related fields are populated. Sets the steps_per_second field in
    the quantization_info message in the NoteSequence.

    Note start and end times, and chord times are snapped to a nearby quantized step, and the resulting times are
    stored in a separate field (e.g. quantized_start_step). See the comments above QUANTIZE_CUTOFF in constants module
    for details on how the quantizing algorithm works.

    Args:
        note_sequence (NoteSequence): A NoteSequence proto.
        steps_per_second (float): Each second will be divided into this many quantized time steps.

    Returns:
        qns (NoteSequence): A copy of the original NoteSequence, with quantized times added.

    Raises:
        NegativeTimeError: If a note or chord occurs at a negative time.
    """
    qns = copy.deepcopy(note_sequence)
    qns.quantization_info.steps_per_second = steps_per_second

    qns.total_quantized_steps = quantize_to_step(qns.total_time, steps_per_second)
    _quantize_notes(qns, steps_per_second)

    return qns


def quantize_to_step(un_quantized_seconds: float, steps_per_second: int, quantize_cutoff=constants.QUANTIZE_CUTOFF) \
        -> int:
    """ Quantizes seconds to the nearest step, given steps_per_second.
    See the comments above QUANTIZE_CUTOFF in constants module for details on how the quantizing algorithm works.

    Args:
        un_quantized_seconds (float): Seconds to quantize.
        steps_per_second (int): Quantizing resolution.
        quantize_cutoff (float): Value to use for quantizing cutoff.

    Returns:
        (int): The input value quantized to the nearest step.
    """
    un_quantized_steps = un_quantized_seconds * steps_per_second
    return int(un_quantized_steps + (1 - quantize_cutoff))


def _quantize_notes(note_sequence: NoteSequence, steps_per_second: int):
    """ Quantize the notes and chords of a NoteSequence proto in place.

    Note start and end times, and chord times are snapped to a nearby quantized step, and the resulting times are
    stored in a separate field (e.g. quantized_start_step). See the comments above QUANTIZE_CUTOFF in constants module
    for details on how the quantizing algorithm works.

    Args:
        note_sequence (NoteSequence): A music_pb2.NoteSequence protocol buffer. Will be modified in place.
        steps_per_second (float): Each second will be divided into this many quantized time steps.

    Raises:
        NegativeTimeError: If a note or chord occurs at a negative time.
    """
    for note in note_sequence.notes:
        # Quantize the start and end times of the note.
        note.quantized_start_step = quantize_to_step(note.start_time, steps_per_second)
        note.quantized_end_step = quantize_to_step(note.end_time, steps_per_second)
        if note.quantized_end_step == note.quantized_start_step:
            note.quantized_end_step += 1

        # Do not allow notes to start or end in negative time.
        if note.quantized_start_step < 0 or note.quantized_end_step < 0:
            raise exceptions.NegativeTimeError('Got negative note time: start_step = %s, end_step = %s' %
                                               (note.quantized_start_step, note.quantized_end_step))

        note.start_time = note.quantized_start_step / steps_per_second
        note.end_time = note.quantized_end_step / steps_per_second

        # Extend quantized sequence if necessary.
        if note.quantized_end_step > note_sequence.total_quantized_steps:
            note_sequence.total_quantized_steps = note.quantized_end_step

    # Also quantize control changes and text annotations.
    for event in itertools.chain(note_sequence.control_changes, note_sequence.text_annotations):
        # Quantize the event time, disallowing negative time.
        event.quantized_step = quantize_to_step(event.time, steps_per_second)
        event.time = event.quantized_step / steps_per_second
        if event.quantized_step < 0:
            raise exceptions.NegativeTimeError('Got negative event time: step = %s' % event.quantized_step)
