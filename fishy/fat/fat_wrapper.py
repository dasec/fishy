"""
This file contains a wrapper for FAT filesystems, who
detects the FAT filesystem an uses the right class
"""
from fat import FAT12, FAT16, FAT32


class UnsupportedFilesystemError(Exception):
    pass

def FAT(stream):
    """
    :param stream: filedescriptor of a FAT12 filesystem
    :return: FAT filesystem object
    """
    # save stream offset
    offset = stream.tell()

    # check if it is a FAT12
    stream.seek(offset + 54)
    fat_type = stream.read(8)
    fat_type = fat_type.decode('ascii').strip()
    if fat_type == 'FAT12':
        # reapply original stream position
        stream.seek(offset)
        return FAT12(stream)

    # check if it is a FAT16
    elif fat_type == 'FAT16':
        # reapply original stream position
        stream.seek(offset)
        return FAT16(stream)

    # check if its FAT32
    stream.seek(offset + 82)
    fat_type = stream.read(8)
    fat_type = fat_type.decode('ascii').strip()
    if fat_type == 'FAT32':
        # check if its real FAT32 or fatplus
        stream.seek(offset + 42)
        fat_version = int.from_bytes(stream.read(2), byteorder='little')
        if fat_version == 0:
            # yes its fat32
            stream.seek(offset)
            return FAT32(stream)
        elif fat_version == 1:
            # No its fat+
            stream.seek(offset)
            raise UnsupportedFilesystemError("FAT+ is currently not supported")
    else:
        stream.seek(offset)
        raise UnsupportedFilesystemError("Could not detect filesystem")

    # reapply original position
    stream.seek(offset)