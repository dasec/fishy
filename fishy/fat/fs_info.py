from construct import Struct, Padding, Bytes, Int32ul

# Filesystem information sector for FAT32
FS_information_sector = Struct(
        "fsinfo_sector_signature" / Bytes(4),
        Padding(480),  # reserved
        "fsinfo_sector_signature" / Bytes(4),
        "free_data_cluster_count" / Int32ul,
        "last_allocated_data_cluster" / Int32ul,
        Padding(12),  # reserved
        "fsinfo_sector_signature" / Bytes(4),
        )
