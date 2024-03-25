""" This module provides utility functions for working with NoteSequence I/O. """
import collections
import hashlib
from typing import Dict, Any

from resolv_mir.protobuf import NoteSequence, SequenceMetadata


def generate_note_sequence_id(filename, collection_name, source_type):
    """Generates a unique ID for a sequence.

    The format is:'/id/<type>/<collection name>/<hash>'.

    Args:
      filename: The string path to the source file relative to the root of the
          collection.
      collection_name: The collection from which the file comes.
      source_type: The source type as a string (e.g. "midi" or "abc").

    Returns:
      The generated sequence ID as a string.
    """
    filename_fingerprint = hashlib.sha1(filename.encode('utf-8'))
    return f'/id/{source_type.lower()}/{collection_name}/{filename_fingerprint.hexdigest()}'


def populate_sequence_metadata(sequence: NoteSequence, source_type: str, metadata: Dict[str, Any]):
    if metadata:
        dict_metadata = collections.defaultdict(lambda: "")
        dict_metadata.update(metadata)
        sequence.id = generate_note_sequence_id(dict_metadata['id'], dict_metadata['collection_name'], source_type)
        sequence.filepath = dict_metadata['filepath']
        sequence.collection_name = dict_metadata['collection_name']
        sequence.reference_number = dict_metadata['reference_number'] if dict_metadata['reference_number'] else 0
        sequence_metadata = SequenceMetadata(
            title=dict_metadata['title'],
            artist=dict_metadata['artist'],
            genre=dict_metadata['genre']
        )
        sequence_metadata.composers.append(dict_metadata['composer'])
        sequence.sequence_metadata.CopyFrom(sequence_metadata)
    return sequence
