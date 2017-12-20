class UnsupportedFilesystemError(Exception):
    pass


def is_ext4(stream):
    """
    checks if a given stream is of type ext4 or not
    :param stream: stream of filesystem
    :return: bool, True if it is a ext4 filesystem
                   False if it is not a ext4 filesystem
    """
    # get start position to reset after check
    offset = stream.tell()
    stream.seek(offset + 1024 + 56)
    fs_type = stream.read(2)
    stream.seek(offset)
    if fs_type.hex() == '53ef':
        return True
    else:
        return False