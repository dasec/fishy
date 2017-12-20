"""
Declaration of a record reference
"""

from construct import Struct, Int16ul, Int32ul

RECORD_REFERENCE = Struct(
    "segment_number_low_part" / Int32ul,
    "segment_number_high_part" / Int16ul,
    "sequence_number" / Int16ul
)
