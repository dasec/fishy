"""
Declaration of the sctructure of attributes
"""

from construct import Struct, Byte, Bytes, Int8ul, Int16ul, Int32ul, Int64ul, this
from .record_reference import RECORD_REFERENCE

STANDARD_INFORMATION_ID = 16

ATTRIBUTE_LIST_ID = 32
ATTRIBUTE_LIST_ENTRY = Struct(
    "attribute_type" / Byte,
    "record_length" / Int16ul,
    "attribute_name_length" / Int8ul,
    "attribute_name_offset" / Int8ul,
    "lowest_vcn" / Int64ul,
    "record_reference" / RECORD_REFERENCE,
    "reserved" / Bytes(2),
    "attribute_name" / Bytes(2*this.attribute_name_length)
)

FILE_NAME_ID = 48
FILE_NAME_ATTRIBUTE = Struct(
    "parent_directory" / RECORD_REFERENCE,
    "creation_time" / Int64ul,
    "last_modified" / Int64ul,
    "last_modifed_for_file_record" / Int64ul,
    "last_access_time" / Int64ul,
    "allocated_size_of_file" / Int64ul,
    "real_file_size" / Int64ul,
    "file_flags" / Bytes(4),
    "reparse_options" / Bytes(4),
    "file_name_length" / Int8ul,
    "namespace" / Byte,
    "file_name" / Bytes(2*this.file_name_length)
)

DATA_ID = 128
INDEX_ROOT_ID = 144
INDEX_ALLOCATION_ID = 160
INDEX_ROOT = Struct(
    "type" / Bytes(4),
    "collation_rule" / Bytes(4),
    "index_entry_size" / Int32ul,
    "cluster_per_index_record" / Byte,
    "padding" / Bytes(3)
)

INDEX_HEADER = Struct(
    "first_entry_offset" / Int32ul,
    "total_size" / Int32ul,
    "allocated_size" / Int32ul,
    "flags" / Byte,
    "padding" / Bytes(3)
)

INDEX_RECORD_HEADER = Struct(
    "signature" / Bytes(4),
    "update_sequence_array_offset" / Int16ul,
    "update_sequence_array_size" / Int16ul,
    "log_file_sequence" / Int64ul,
    "lowest_vcn" / Int64ul,
    "index_entry_offset" / Int32ul,
    "size_of_entries" / Int32ul,
    "size_of_entry_alloc" / Int32ul,
    "flags" / Byte,
    "reserved" / Bytes(3),
    "update_sequence" / Bytes(2*this.update_sequence_array_size)
)

INDEX_RECORD_ENTRY = Struct(
    "record_reference" / RECORD_REFERENCE,
    "size_of_index_entry" / Int16ul,
    "file_name_offset" / Int16ul,
    "flags" / Bytes(2),
    "reserved" / Bytes(2),
    "record_reference_of_parent" / RECORD_REFERENCE,
    "creation_time" / Int64ul,
    "last_modified" / Int64ul,
    "last_modifed_for_file_record" / Int64ul,
    "last_access_time" / Int64ul,
    "allocated_size_of_file" / Int64ul,
    "real_file_size" / Int64ul,
    "file_flags" / Int64ul,
    "file_name_length" / Byte,
    "file_name_namespace" / Byte,
    "file_name" / Bytes(2*this.file_name_length)
)

BITMAP_ID = 176

