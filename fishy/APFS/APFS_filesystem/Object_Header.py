# Object header Structure

from fishy.APFS.APFS_filesystem.APFS_Parser import Parser


HEADER_SIZE = 32
BYTEORDER = 'little'


class ObjectHeader:

    structure = {
        "o_chksum": {"offset": 0x0, "size": 8, "format": "hex"},
        # Fletchers Checksum, Input is entire block without first 8 bytes
        "oid": {"offset": 0x8, "size": 8},
        # Object ID
        "xid": {"offset": 0x10, "size": 8},
        # Version ID
        "type": {"offset": 0x18, "size": 2},
        "flags": {"offset": 0x1A, "size": 2, "format": "hex"},
        "subtype": {"offset": 0x1C, "size": 4}
        # Alternative size subtype 2 and 2 padding

    }

    def __init__(self, fs_stream, offset):
        self.data = self.parse_object_header(fs_stream, offset)
        self.offset = offset

    def parse_superblock_object_header(self, fs_stream):
        d = Parser.parse(fs_stream, 0, HEADER_SIZE, structure=self.structure)
        fs_stream.seek(0)
        return d

    def parse_object_header(self, fs_stream, offset):
        d = Parser.parse(fs_stream, offset, HEADER_SIZE, structure=self.structure)
        fs_stream.seek(0)

        return d

    def getSize(self):
        return HEADER_SIZE








