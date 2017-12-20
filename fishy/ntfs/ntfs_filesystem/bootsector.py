"""
Bootsector definition for NTFS
"""

from construct import Struct, Byte, Bytes,\
    Int8ul, Int8sl, Int16ul, Int32ul, Int64ul

NTFS_BOOTSECTOR = Struct(
    "jump_instruction" / Bytes(3),
    "oem_name" / Bytes(8),
    "sector_size" / Int16ul,
    "cluster_size" / Int8ul,
    "reserved_sectors" / Bytes(2),
    "reserved_1" / Bytes(3),
    "unused_1" / Bytes(2),
    "media_descriptor" / Byte,
    "unused_2" / Bytes(2),
    "sectors_per_track" / Int16ul,
    "num_heads" / Int16ul,
    "hidden_sectors" / Int32ul,
    "unused_3" / Bytes(4),
    "unused_5" / Bytes(4),
    "total_sectors" / Int64ul,
    "mft_cluster" / Int64ul,
    "mft_mirr_cluster" / Int64ul,
    "clusters_per_file_record" / Int8sl,
    "unused_6" / Bytes(3),
    "clusters_per_index_buffer" / Int8sl,
    "unused_7" / Bytes(3),
    "volume_serial" / Bytes(8),
    "checksum" / Bytes(4),
    "bootstrap" / Bytes(426),
    "eos_marker" / Bytes(2)
)

