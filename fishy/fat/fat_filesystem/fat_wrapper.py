"""
This file contains a wrapper for FAT filesystems, which
detects the FAT filesystem an uses the right class

>>> f = open('testfs.dd', 'rb')
>>> fs = create_fat(f)
"""
import typing as typ
from .fat_detector import get_filesystem_type
from .fat import FAT
from .fat_12 import FAT12
from .fat_16 import FAT16
from .fat_32 import FAT32


def create_fat(stream: typ.BinaryIO) -> FAT:
    """
    Detect FAT filesystem type and return an instance of it
    :param stream: filedescriptor of a FAT filesystem
    :return: FAT filesystem object
    :raises: UnsupportedFilesystemError
    :rtype: FAT12, FAT16 or FAT32
    """
    # get fs_type
    fat_type = get_filesystem_type(stream)
    # check if it is a FAT12
    if fat_type == 'FAT12':
        return FAT12(stream)
    # check if it is a FAT16
    elif fat_type == 'FAT16':
        return FAT16(stream)
    # check if its FAT32
    elif fat_type == 'FAT32':
        return FAT32(stream)
