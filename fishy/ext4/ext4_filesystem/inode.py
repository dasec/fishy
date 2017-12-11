import pprint

from fishy.ext4.ext4_filesystem.parser import Parser

pp = pprint.PrettyPrinter(indent=4)

BYTEORDER = 'little'


class Inode:
    """
    This class represents a single inode.
    """

    # Structure of Superblock:
    # name: {offset: hex, size: in bytes, [format: python builtin function (e.g. hex, bin, etc...] }
    structure = {
        "mode":         {"offset": 0x0, "size": 2, "format": "hex"},
        "uid":          {"offset": 0x2, "size": 2},
        "size":         {"offset": 0x4, "size": 4},
        "atime":        {"offset": 0x8, "size": 4, "format": "time"},
        "ctime":        {"offset": 0xC, "size": 4, "format": "time"},
        "mtime":        {"offset": 0x10, "size": 4, "format": "time"},
        "dtime":        {"offset": 0x14, "size": 4, "format": "time"},
        "gid":          {"offset": 0x18, "size": 2},
        "links_count":  {"offset": 0x1A, "size": 2},
        "blocks":       {"offset": 0x1C, "size": 4},
        "flags":        {"offset": 0x20, "size": 4, "format": "hex"},
        "osd1":         {"offset": 0x24, "size": 4, "format": "raw"},
        "extent_tree":  {"offset": 0x28, "size": 60, "format": "raw"},
        "generation":   {"offset": 0x64, "size": 4},
        "file_acl":     {"offset": 0x68, "size": 4},
        "dir_acl":      {"offset": 0x6C, "size": 4},
        "obso_faddr":   {"offset": 0x70, "size": 4},
        "osd2":         {"offset": 0x74, "size": 12, "format": "raw"},
        "extra_isize":  {"offset": 0x80, "size": 2},
        "checksum_hi":  {"offset": 0x82, "size": 2},
        "ctime_extra":  {"offset": 0x84, "size": 4},
        "mtime_extra":  {"offset": 0x88, "size": 4},
        "atime_extra":  {"offset": 0x8C, "size": 4},
        "crtime":       {"offset": 0x90, "size": 4},
        "crtime_extra": {"offset": 0x94, "size": 4},
        "version_hi":   {"offset": 0x98, "size": 4},
        "projid":       {"offset": 0x9C, "size": 4},
    }

    extent_tree_header = {
        "magic": {"offset": 0x0, "size": 2},
        "entries": {"offset": 0x2, "size": 2},
        "max": {"offset": 0x4, "size": 2},
        "depth": {"offset": 0x6, "size": 2},
        "generation": {"offset": 0x8, "size": 4},
    }

    extent_internal_nodes = {
        "block": {"offset": 0x0, "size": 4},
        "leaf_lo": {"offset": 0x4, "size": 4},
        "leaf_hi": {"offset": 0x8, "size": 2},
        "unused": {"offset": 0xA, "size": 2},
    }

    extent_leaf_nodes = {
        "block": {"offset": 0x0, "size": 4},
        "len": {"offset": 0x4, "size": 2},
        "start_hi": {"offset": 0x6, "size": 2},
        "start_lo": {"offset": 0x8, "size": 4},
    }

    def __init__(self, fs_stream, offset, lenght, blocksize):
        self.blocksize = blocksize
        self.offset = offset
        self.length = lenght
        self.data = self.parse_inode(fs_stream)

        self.extents = self.parse_extents(self.data['extent_tree'])

    def parse_inode(self, filename):
        d = Parser.parse(filename, offset=self.offset, length=self.length, structure=self.structure)
        return d

    def parse_extents(self, tree):
        extent_data = {}

        header_part = tree[:12]

        header = {}
        for key, value in self.extent_tree_header.items():
            field_offset = value["offset"]
            field_size = value["size"]
            bytes = header_part[field_offset:field_offset+field_size]
            header[key] = int.from_bytes(bytes, byteorder='little')


        extent_data["header"] = header

        if header["depth"] == 0:
            leaf_part = tree[12:24]
            data = {}
            for key, value in self.extent_leaf_nodes.items():
                field_offset = value["offset"]
                field_size = value["size"]
                bytes = leaf_part[field_offset:field_offset+field_size]
                data[key] = int.from_bytes(bytes, byteorder='little')

            extent_data["data"] = data

        return extent_data
