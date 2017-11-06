"""
Directory and Long Filename entries that appear in root and
subdirectories.
"""

from construct import Struct, Byte, Bytes, BitStruct, Flag, Padding, \
                      Int16ul, Int32ul


# Directory Entry in either the root directory
# or any subdirectory
DIR_ENTRY = Struct(
    "name" / Bytes(8),
    "extension" / Bytes(3),
    "attributes" / BitStruct(
        "unused" / Flag,
        "device" / Flag,
        "archive" / Flag,
        "subDirectory" / Flag,
        "volumeLabel" / Flag,
        "system" / Flag,
        "hidden" / Flag,
        "readonly" / Flag,
    ),
    Padding(8),
    "accessRightsBitmap" / Bytes(2),
    "timeRecorded" / Int16ul,
    "dateRecorded" / Int16ul,
    "firstCluster" / Bytes(2),
    "fileSize" / Int32ul,
)

# Directory entry that represents a vFAT entry
# for Long Filenames (LFN)
LFN_ENTRY = Struct(
    "sequence_number" / Byte,
    "name1" / Bytes(10),
    "attributes" / Byte,
    "type" / Byte,
    "checksum" / Byte,
    "name2" / Bytes(12),
    "first_cluster" / Bytes(2),
    "name3" / Bytes(4),
    )
