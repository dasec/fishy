from construct import Struct, Byte, Bytes, Int16ul, Int32ul, Padding, this, \
                      Embedded, BitStruct, Nibble, Flag
from fs_info import FS_information_sector

# Core Bootsector, which is the same for all FAT types
FATCoreBootsector = Struct(
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
FAT12_16_ExtendedBootsector = Struct(
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
FAT32_ExtendedBootsector = Struct(
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
FAT12_16Bootsector = Struct(
        Embedded(FATCoreBootsector),
        Embedded(FAT12_16_ExtendedBootsector),
        Padding(this.sector_size - FATCoreBootsector.sizeof() -
                FAT12_16_ExtendedBootsector.sizeof()),
        )

# ready to use bootsector definition for FAT32
FAT32Bootsector = Struct(
        Embedded(FATCoreBootsector),
        Embedded(FAT32_ExtendedBootsector),
        # Embedded(FS_information_sector),
        Padding(this.sector_size - FATCoreBootsector.sizeof() -
                FAT32_ExtendedBootsector.sizeof()
                # - FS_information_sector.sizeof()
                ),
        )
