"""
Author: Matteo Pettenò.
Package Name: I/O.
Description: Package providing I/O operations for the note_sequence lib.
    Supported input files are MIDI and MusicXML. This package provides the necessary modules containing the functions
    useful to convert the input files to the NoteSequence canonical format and vice versa.
Copyright (c) 2024, Matteo Pettenò
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
from . import midi_io
from . import musicxml_io
