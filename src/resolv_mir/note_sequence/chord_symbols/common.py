from .exceptions import ChordSymbolError


# Function to add a scale degree.
def add_scale_degree(degrees, degree, alter):
    if degree in degrees:
        raise ChordSymbolError('Scale degree already in chord: %d' % degree)
    if degree == 7:
        alter -= 1
    degrees[degree] = alter


# Function to remove a scale degree.
def subtract_scale_degree(degrees, degree, unused_alter):
    if degree not in degrees:
        raise ChordSymbolError('Scale degree not in chord: %d' % degree)
    del degrees[degree]


# Function to alter (or add) a scale degree.
def alter_scale_degree(degrees, degree, alter):
    if degree in degrees:
        degrees[degree] += alter
    else:
        degrees[degree] = alter


def pitch_class_to_string(step, alter):
    """Convert a pitch class scale step and alteration to string."""
    return step + abs(alter) * ('#' if alter >= 0 else 'b')
