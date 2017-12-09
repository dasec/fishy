from .parser import Parser

class GDT:

    structure32 = {
        "block_bitmap_lo":          {"offset": 0x0, "size": 4},
        "inode_bitmap_lo":          {"offset": 0x4, "size": 4},
        "inode_table_lo":           {"offset": 0x8, "size": 4},
        "free_blocks_count_lo":     {"offset": 0xC, "size": 2},
        "free_inodes_count_lo":     {"offset": 0xE, "size": 2},
        "used_dirs_count_lo":       {"offset": 0x10, "size": 2},
        "flags":                    {"offset": 0x12, "size": 2},
        "exclude_bitmap_lo":        {"offset": 0x14, "size": 4},
        "block_bitmap_csum_lo":     {"offset": 0x18, "size": 2},
        "inode_bitmap_csum_lo":     {"offset": 0x1A, "size": 2},
        "itable_unused_lo":         {"offset": 0x1C, "size": 2},
        "checksum":                 {"offset": 0x1E, "size": 2}
    }

    # Contains fields only used if the 64bit feature is enabled and s_desc_size > 32.
    structure64 = {
        "block_bitmap_lo":          {"offset": 0x0, "size": 4},
        "inode_bitmap_lo":          {"offset": 0x4, "size": 4},
        "inode_table_lo":           {"offset": 0x8, "size": 4},
        "free_blocks_count_lo":     {"offset": 0xC, "size": 2},
        "free_inodes_count_lo":     {"offset": 0xE, "size": 2},
        "used_dirs_count_lo":       {"offset": 0x10, "size": 2},
        "flags":                    {"offset": 0x12, "size": 2},
        "exclude_bitmap_lo":        {"offset": 0x14, "size": 4},
        "block_bitmap_csum_lo":     {"offset": 0x18, "size": 2},
        "inode_bitmap_csum_lo":     {"offset": 0x1A, "size": 2},
        "itable_unused_lo":         {"offset": 0x1C, "size": 2},
        "checksum":                 {"offset": 0x1E, "size": 2},
        # These fields only exist if the 64bit feature is enabled and s_desc_size > 32.
        "block_bitmap_hi":          {"offset": 0x20, "size": 4},
        "inode_bitmap_hi":          {"offset": 0x24, "size": 4},
        "inode_table_hi":           {"offset": 0x28, "size": 4},
        "free_blocks_count_hi":     {"offset": 0x2C, "size": 2},
        "free_inodes_count_hi":     {"offset": 0x2E, "size": 2},
        "used_dirs_count_hi":       {"offset": 0x30, "size": 2},
        "itable_unused_hi":         {"offset": 0x32, "size": 2},
        "exclude_bitmap_hi":        {"offset": 0x34, "size": 4},
        "block_bitmap_csum_hi":     {"offset": 0x38, "size": 2},
        "inode_bitmap_csum_hi":     {"offset": 0x3A, "size": 2},
        "reserved":                 {"offset": 0x3C, "size": 4}
    }

    def __init__(self, filename, superblock):
        if(int(self.superblock.data['feature_incompat'], 0) & 0x80) == 0x80:
            self.is_64bit = True
        else:
            self.is_64bit = False
        self.data = self.parse_gdt(filename)

    def parse_gdt(self, filename):
        if(self.is_64bit) :
            d = Parser.parse(filename, 1024, 64, structure=self.structure64)
        else:
            d = Parser.parse(filename, 1024, 32, structure = self.structure32)

        return d