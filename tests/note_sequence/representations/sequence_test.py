import unittest

from resolv_mir.note_sequence import processors, representations
from resolv_mir.note_sequence.io import midi_io


class PitchSequenceTest(unittest.TestCase):

    @property
    def test_file_path(self):
        return "../../data/4bar_monophonic_melody.mid"

    def test_to_pitch_sequence(self):
        pitch_seq_repr = [80, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 78, 76, 128, 129,
                          129, 68, 128, 128, 128, 69, 128, 71, 128, 128, 128, 79, 128, 80, 128, 128, 128, 128, 128, 128,
                          128, 128, 128, 128, 128, 128, 128, 128, 129, 129, 129, 129, 129, 68, 128, 128, 128, 69, 128,
                          71, 128, 128, 128, 79, 128]
        note_sequence = midi_io.midi_file_to_note_sequence(self.test_file_path)
        note_sequence = processors.quantizer.quantize_note_sequence(note_sequence, steps_per_quarter=4)
        test_pitch_seq_repr = representations.pitch_sequence_representation(note_sequence)
        self.assertEqual(pitch_seq_repr, test_pitch_seq_repr)

    def test_from_pitch_sequence(self):
        # TODO - test implementation
        pass


if __name__ == '__main__':
    unittest.main()
