"""
Author: Matteo Pettenò.
Package Name: processors.
Description: Package providing various operations on NoteSequences.
    This module imports functions from submodules to perform operations such as extending, extracting, quantizing,
    slicing, splitting, stretching, sustaining, transposing, and truncating NoteSequences.
Copyright (c) 2024, Matteo Pettenò
License: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""
from . import extender
from . import extractor
from . import quantizer
from . import slicer
from . import splitter
from . import stretcher
from . import sustainer
from . import transposer
from . import truncator
