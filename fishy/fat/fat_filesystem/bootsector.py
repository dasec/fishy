"""
Bootsector definition for FAT12, FAT16 and FAT32
This structure is part of the reserved sectors section.
"""

from construct import Struct, Byte, Bytes, Int16ul, Int32ul, Padding, this, \
                      Embedded, BitStruct, Nibble, Flag
from .fs_info import FS_INFORMATION_SECTOR


# Core Bootsector, which is the same for all FAT types
FAT_CORE_BOOTSECTOR = Struct(
    "jump_instruction" / Bytes(3),
    "oem_name" / Bytes(8),
    "sector_size" / Int16ul,
    "sectors_per_cluster" / Byte,
    "reserved_sector_count" / Int16ul,
    "fat_count" / Byte,
    "rootdir_entry_count" / Int16ul,
    "sectorCount_small" / Int16ul,
    "media_descriptor_byte" / Byte,
    "sectors_per_fat" / Int16ul,
    "sectors_per_track" / Int16ul,
    "side_count" / Int16ul,
    "hidden_sectors_count" / Int32ul,
    "sectorCount_large" / Int32ul,
    )

# FAT12 and FAT16 bootsector extension
FAT12_16_EXTENDED_BOOTSECTOR = Struct(
    "physical_drive_number" / Byte,
    Padding(1),  # reserved
    "extended_boot_signature" / Byte,
    "volume_id" / Bytes(4),
    "volume_label" / Bytes(11),
    "fs_type" / Bytes(8),
    "boot_code" / Bytes(448),
    "boot_sector_signature" / Bytes(2),
    )

# FAT32 bootsector extension
FAT32_EXTENDED_BOOTSECTOR = Struct(
    "sectors_per_fat" / Int32ul,
    "flags" / BitStruct(
        "active_fat" / Nibble,  # only interesting if fat is not mirrored
        "mirrored" / Flag,
        Padding(3),
        Padding(8)
        ),
    "version" / Int16ul,
    "rootdir_cluster" / Int32ul,
    "fsinfo_sector" / Int16ul,
    "bootsector_copy_sector" / Int16ul,
    Padding(12),  # reserved
    "physical_drive_number" / Byte,
    Padding(1),  # reserved
    "extended_bootsignature" / Byte,
    "volume_id" / Int32ul,
    "volume_label" / Bytes(11),
    "fs_type" / Bytes(8),
    "boot_code" / Bytes(420),
    "boot_sector_signature" / Bytes(2),
    )

# ready to use bootsector definition for FAT12 and FAT16
FAT12_16_BOOTSECTOR = Struct(
    Embedded(FAT_CORE_BOOTSECTOR),
    Embedded(FAT12_16_EXTENDED_BOOTSECTOR),
    Padding(this.sector_size - FAT_CORE_BOOTSECTOR.sizeof() -
            FAT12_16_EXTENDED_BOOTSECTOR.sizeof()),
    )

# ready to use bootsector definition for FAT32
FAT32_BOOTSECTOR = Struct(
    Embedded(FAT_CORE_BOOTSECTOR),
    Embedded(FAT32_EXTENDED_BOOTSECTOR),
    Padding(this.sector_size - FAT_CORE_BOOTSECTOR.sizeof()
            - FAT32_EXTENDED_BOOTSECTOR.sizeof()
           ),
    Embedded(FS_INFORMATION_SECTOR),
    Padding(this.sector_size
            - FS_INFORMATION_SECTOR.sizeof()
           ),
    )
