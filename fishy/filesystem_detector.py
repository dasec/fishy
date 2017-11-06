"""
Basic filesystem detector for FAT and NTFS
"""

from .fat.fat_filesystem import fat_detector
from .ntfs import ntfs_detector

# TODO: This is a duplicate of fat_detector
#       we should somehow figure out how to
#       deduplicate this
class UnsupportedFilesystemError(Exception):
    """
    This exception indicates, that the filesystem type could not be determined
    """
    pass


def get_filesystem_type(stream) -> str:
    """
    extracts the filesystem type from a given stream
    :stream: stream of filesystem
    :return: string, 'FAT'
    :raises: UnsupportedFilesystemError
    """
    # TODO: Implement ext4 detector
    if fat_detector.is_fat(stream):
        return "FAT"
    elif ntfs_detector.is_ntfs(stream):
        return "NTFS"
    else:
        raise UnsupportedFilesystemError()
