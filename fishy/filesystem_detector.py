from .fat.fat_filesystem import fat_detector
from .ntfs import ntfs_detector

# TODO: This is a duplicate of fat_detector
#       we should somehow figure out how to
#       deduplicate this
class UnsupportedFilesystemError(Exception):
    pass


def get_filesystem_type(stream):
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

if __name__ == "__main__":
    # Just a simple test if filesystem detection works.
    s = open('utils/testfs-fat12.dd', 'rb')
    print(get_filesystem_type(s))
    s = open('utils/testfs-fat16.dd', 'rb')
    print(get_filesystem_type(s))
    s = open('utils/testfs-fat32.dd', 'rb')
    print(get_filesystem_type(s))
    s = open('utils/testfs-ntfs.dd', 'rb')
    print(get_filesystem_type(s))
    s = open('utils/testfs-ext4.dd', 'rb')
    print(get_filesystem_type(s))
