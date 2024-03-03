from . import common, parser, splitter, constants


def transpose_chord_symbol(figure, transpose_amount):
    """Transposes a chord symbol figure string by the given amount.

    Args:
      figure: The chord symbol figure string to transpose.
      transpose_amount: The integer number of half steps to transpose.

    Returns:
      The transposed chord symbol figure string.

    Raises:
      ChordSymbolError: If the given chord symbol cannot be interpreted.
    """
    # Split chord symbol into root, kind, modifications, and bass.
    root_str, kind_str, modifications_str, bass_str = splitter.split_chord_symbol(figure)

    # Parse and transpose the root.
    root_step, root_alter = parser.parse_root(root_str)
    transposed_root_step, transposed_root_alter = transpose_pitch_class(root_step, root_alter, transpose_amount)
    transposed_root_str = common.pitch_class_to_string(transposed_root_step, transposed_root_alter)

    # Parse bass.
    bass = parser.parse_bass(bass_str)

    if bass:
        # Bass exists, transpose it.
        bass_step, bass_alter = bass  # pylint: disable=unpacking-non-sequence
        transposed_bass_step, transposed_bass_alter = transpose_pitch_class(bass_step, bass_alter, transpose_amount)
        transposed_bass_str = '/' + common.pitch_class_to_string(transposed_bass_step, transposed_bass_alter)
    else:
        # No bass.
        transposed_bass_str = bass_str

    return '%s%s%s%s' % (transposed_root_str, kind_str, modifications_str, transposed_bass_str)


def transpose_pitch_class(step, alter, transpose_amount):
    """Transposes a chord symbol figure string by the given amount."""
    transpose_amount %= 12

    # Transpose up as many steps as we can.
    while transpose_amount >= constants.STEPS_ABOVE[step]:
        transpose_amount -= constants.STEPS_ABOVE[step]
        step = chr(ord('A') + (ord(step) - ord('A') + 1) % 7)

    if transpose_amount > 0:
        if alter >= 0:
            # Transpose up one more step and remove sharps (or add flats).
            alter -= constants.STEPS_ABOVE[step] - transpose_amount
            step = chr(ord('A') + (ord(step) - ord('A') + 1) % 7)
        else:
            # Remove flats.
            alter += transpose_amount

    return step, alter
