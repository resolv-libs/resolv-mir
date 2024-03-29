import unittest
from pathlib import Path

from resolv_mir.note_sequence.io import midi_io
from resolv_mir.note_sequence.processors import slicer, quantizer


class SlicerTest(unittest.TestCase):

    @property
    def input_dir(self) -> Path:
        return Path("./data/processors/slicer")

    @property
    def assert_dir(self) -> Path:
        return Path("./data/processors/slicer")

    @property
    def output_dir(self) -> Path:
        return Path("./output/processors/slicer")

    def setUp(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


if __name__ == '__main__':
    unittest.main()
