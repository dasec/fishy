"""
Declaration of the header of MFT Records
"""

from construct import Struct, Bytes, Int16ul, Int32ul
from .record_reference import RECORD_REFERENCE

RECORD_HEADER = Struct(
    "signature" / Bytes(4),
    "update_sequence_array_offset" / Int16ul,
    "update_sequence_array_size" / Int16ul,
    "reserved1" / Bytes(8),
    "sequence_number" / Int16ul,
    "reserved2" / Bytes(2),
    "first_attribute_offset" / Int16ul,
    "flags" / Bytes(2),
    "reserved3" / Bytes(8),
    "base_record_segment" / RECORD_REFERENCE,
    "reserved4" / Bytes(2)
)
