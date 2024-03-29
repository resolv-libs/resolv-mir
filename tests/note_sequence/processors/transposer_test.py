import unittest
from pathlib import Path

from resolv_mir.note_sequence.io import midi_io
from resolv_mir.note_sequence.processors import transposer


class TransposerTest(unittest.TestCase):

    @property
    def input_dir(self) -> Path:
        return Path("./data")

    @property
    def assert_dir(self) -> Path:
        return Path("./data/processors/transposer")

    @property
    def output_dir(self) -> Path:
        return Path("./output/processors/transposer")

    def setUp(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def test_positive_amount_transpose(self):
        test_file_name = "4bar_monophonic_melody.mid"
        test_file_path = self.input_dir / test_file_name
        assert_file_path = self.assert_dir / f"positive_{test_file_name}"
        assert_note_sequence = midi_io.midi_file_to_note_sequence(assert_file_path)
        note_sequence = midi_io.midi_file_to_note_sequence(test_file_path)
        transposed_ns, del_notes = transposer.transpose_note_sequence(note_sequence, amount=2, in_place=True)
        self.assertEqual(del_notes, 0)
        self.assertEqual(transposed_ns, assert_note_sequence)

    def test_negative_amount_transpose(self):
        test_file_name = "4bar_monophonic_melody.mid"
        test_file_path = self.input_dir / test_file_name
        assert_file_path = self.assert_dir / f"negative_{test_file_name}"
        assert_note_sequence = midi_io.midi_file_to_note_sequence(assert_file_path)
        note_sequence = midi_io.midi_file_to_note_sequence(test_file_path)
        transposed_ns, del_notes = transposer.transpose_note_sequence(note_sequence, amount=-2, in_place=True)
        self.assertEqual(del_notes, 0)
        self.assertEqual(transposed_ns, assert_note_sequence)

    def test_out_of_bound_transpose_delete_notes(self):
        test_file_name = "4bar_monophonic_melody.mid"
        test_file_path = self.input_dir / test_file_name
        assert_file_path = self.assert_dir / f"oob_delete_{test_file_name}"
        assert_note_sequence = midi_io.midi_file_to_note_sequence(assert_file_path)
        note_sequence = midi_io.midi_file_to_note_sequence(test_file_path)
        transposed_ns, del_notes = transposer.transpose_note_sequence(note_sequence,
                                                                      amount=4,
                                                                      min_allowed_pitch=72,
                                                                      max_allowed_pitch=76,
                                                                      delete_notes=True,
                                                                      in_place=True)
        self.assertEqual(del_notes, 6)
        self.assertEqual(transposed_ns, assert_note_sequence)

    def test_out_of_bound_transpose_keep_notes(self):
        test_file_name = "4bar_monophonic_melody.mid"
        test_file_path = self.input_dir / test_file_name
        assert_file_path = self.assert_dir / f"oob_keep_{test_file_name}"
        assert_note_sequence = midi_io.midi_file_to_note_sequence(assert_file_path)
        note_sequence = midi_io.midi_file_to_note_sequence(test_file_path)
        transposed_ns, del_notes = transposer.transpose_note_sequence(note_sequence,
                                                                      amount=4,
                                                                      min_allowed_pitch=72,
                                                                      max_allowed_pitch=76,
                                                                      delete_notes=False,
                                                                      in_place=True)
        self.assertEqual(del_notes, 4)
        self.assertEqual(transposed_ns, assert_note_sequence)


if __name__ == '__main__':
    unittest.main()
