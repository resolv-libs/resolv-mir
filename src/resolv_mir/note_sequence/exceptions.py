""" This module defines custom exception classes related to music processing and MIDI/MusicXML input/output operations.

Exceptions are organized into two main categories:

1. Processors Exceptions:
    - These exceptions relate to errors that may occur during music processing, such as invalid notes or time
    signatures.

2. MIDI IO Exceptions:
    - These exceptions relate to errors that may occur during the conversion of MIDI files to NoteSequence proto.

3. MusicXML IO Exceptions:
    - These exceptions relate to errors that may occur during the conversion of MusicXML files to NoteSequence proto,
    as well as parsing MusicXML content.

Module Contents:
-----------------
Processors Exceptions:
    - BadNoteError
    - BadTimeSignatureError
    - MultipleTempoError
    - MultipleTimeSignatureError
    - NegativeTimeError
    - NonIntegerStepsPerBarError
    - PolyphonicMelodyError
    - QuantizationStatusError

MIDI IO Exceptions:
    - MIDIConversionError

MusicXML IO Exceptions:
    - MusicXMLConversionError
    - MusicXMLParseError
    - PitchStepParseError
    - ChordSymbolParseError
    - AlternatingTimeSignatureError
    - TimeSignatureParseError
    - UnpitchedNoteError
    - KeyParseError
    - InvalidNoteDurationTypeError

Each exception provides specific error messages and context for different exceptional situations that may occur during
music processing or input/output operations.
"""


# --------------------- Processors Exceptions ---------------------

class BadNoteError(Exception):
    """Exception thrown when a NoteSequence.Note is invalid."""
    pass


class BadTimeSignatureError(Exception):
    """Exception thrown when a NoteSequence.TimeSignature is invalid."""
    pass


class MultipleTempoError(Exception):
    """Exception thrown when multiple NoteSequence.Tempo in a quantized NoteSequence are found."""
    pass


class MultipleTimeSignatureError(Exception):
    """Exception thrown when multiple NoteSequence.TimeSignature in a quantized NoteSequence are found."""
    pass


class NegativeTimeError(Exception):
    """Exception thrown when a negative time value is found."""
    pass


class NonIntegerStepsPerBarError(Exception):
    """Exception thrown if the bar length in a quantized NoteSequence is not an integer number of time steps."""
    pass


class PolyphonicMelodyError(Exception):
    """Exception thrown when a polyphonic event occurs during the extraction of a melody."""
    pass


class QuantizationStatusError(Exception):
    """Exception thrown when a sequence was unexpectedly quantized or un-quantized."""
    pass


# --------------------- MIDI IO Exceptions ---------------------

class MIDIConversionError(Exception):
    """Exception thrown when an error occurs during the conversion of a MIDI file to a NoteSequence proto."""
    pass


# --------------------- MusicXML IO Exceptions ---------------------

class MusicXMLConversionError(Exception):
    """Exception thrown when an error occurs during the conversion of a MusicXML file to a NoteSequence proto."""
    pass


class MusicXMLParseError(Exception):
    """Exception thrown when a MusicXML file content cannot be parsed."""
    pass


class PitchStepParseError(MusicXMLParseError):
    """Exception thrown when a pitch step cannot be parsed.
    Will happen if pitch step is not one of A, B, C, D, E, F, or G
    """
    pass


class ChordSymbolParseError(MusicXMLParseError):
    """Exception thrown when a chord symbol cannot be parsed."""
    pass


class AlternatingTimeSignatureError(MusicXMLParseError):
    """Exception thrown when an alternating time signature is encountered."""
    pass


class TimeSignatureParseError(MusicXMLParseError):
    """Exception thrown when the time signature could not be parsed."""
    pass


class UnpitchedNoteError(MusicXMLParseError):
    """Exception thrown when an unpitched note is encountered.
    We do not currently support parsing files with unpitched notes (e.g. percussion scores).
    https://www.musicxml.com/tutorial/percussion/unpitched-notes/
    """
    pass


class KeyParseError(MusicXMLParseError):
    """Exception thrown when a key signature cannot be parsed."""
    pass


class InvalidNoteDurationTypeError(MusicXMLParseError):
    """Exception thrown when a note's duration type is invalid."""
    pass
