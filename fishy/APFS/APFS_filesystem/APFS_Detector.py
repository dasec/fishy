# Calls function returning magic bytes from Container

# basic syntax: if [magic bytes] == [predetermined magic bytes] return true

def is_apfs(fs_stream):
    fs_stream.seek(0)
    offset = fs_stream.tell()
    fs_stream.seek(offset + 32)
    fs_type = fs_stream.read(4)
    fs_stream.seek(offset)
    if fs_type == b'NXSB':
        return True

    elif object_type != b'NXSB':
        return False


