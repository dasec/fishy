class UnsupportedFilesystemError(Exception):
    pass


def is_fat(stream):
    """
    checks if a given stream is of type fat or not
    :param stream: stream of filesystem
    :return: bool, True if it is a FAT filesystem
                   False if it is not a FAT filesystem
    """
    try:
        fs_type = get_filesystem_type(stream)
        if fs_type == 'FAT12' \
                or fs_type == 'FAT16' \
                or fs_type == 'FAT32':
            return True
    except UnsupportedFilesystemError:
        pass
    return False


def get_filesystem_type(stream):
    """
    extracts the FAT filesystem type from a given stream
    :stream: stream of filesystem
    :return: string, 'FAT12', 'FAT16' or 'FAT32'
    :raises: UnsupportedFilesystemError
    """
    # save stream offset
    offset = stream.tell()

    # check if it is a FAT12
    stream.seek(offset + 54)
    fat_type = stream.read(8)
    if fat_type == b'FAT12   ':
        # reapply original stream position
        stream.seek(offset)
        return "FAT12"

    # check if it is a FAT16
    elif fat_type == b'FAT16   ':
        # reapply original stream position
        stream.seek(offset)
        return "FAT16"

    # check if its FAT32
    stream.seek(offset + 82)
    fat_type = stream.read(8)
    if fat_type == b'FAT32   ':
        # check if its real FAT32 or fatplus
        stream.seek(offset + 42)
        fat_version = int.from_bytes(stream.read(2), byteorder='little')
        if fat_version == 0:
            # yes its fat32
            stream.seek(offset)
            return "FAT32"
        elif fat_version == 1:
            # No its fat+
            stream.seek(offset)
            raise UnsupportedFilesystemError("FAT+ is currently not supported")
    else:
        stream.seek(offset)
        raise UnsupportedFilesystemError("Could not detect filesystem")

    # reapply original position
    stream.seek(offset)
