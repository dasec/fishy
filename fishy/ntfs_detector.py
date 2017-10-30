# TODO: This file should be moved into ntfs module when it exists
# TODO: This is a duplicate of fat.fat_filesystem.fat_detector
#       we should deduplicate this
class UnsupportedFilesystemError(Exception):
    pass


def is_ntfs(stream):
    """
    checks if a given stream is of type ntfs or not
    :param stream: stream of filesystem
    :return: bool, True if it is a NTFS filesystem
                   False if it is not a NTFS filesystem
    """
    # get start position to reset after check
    offset = stream.tell()
    stream.seek(offset + 3)
    fs_type = stream.read(8)
    stream.seek(offset)
    if fs_type == b'NTFS    ':
        return True
    return False
