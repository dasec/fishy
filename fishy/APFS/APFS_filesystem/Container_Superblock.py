from fishy.APFS.APFS_filesystem.APFS_Parser import Parser

BLOCK_SIZE = 4096
# Assumed starting block size

class Superblock:

    structure = {
        "magic": {"offset": 0x0, "size": 4, "format": "raw"},
        "block_size": {"offset": 0x4, "size": 4},
        "block_count": {"offset": 0x8, "size": 8},
        "features": {"offset": 0x10, "size": 8},
        "rom_features": {"offset": 0x18, "size": 8},
        "incompatible_features": {"offset": 0x20, "size": 8},
        "uuid": {"offset": 0x28, "size": 16, "format": "raw"},
        "next_oid": {"offset": 0x38, "size": 8},
        "next_xid": {"offset": 0x40, "size": 8},
        "xp_desc_blocks": {"offset": 0x48, "size": 4},
        "xp_data_blocks": {"offset": 0x4C, "size": 4},
        "xp_desc_base": {"offset": 0x50, "size": 8},
        "xp_data_base": {"offset": 0x58, "size": 8},
        "xp_desc_len": {"offset": 0x60, "size": 4},
        "xp_data_len": {"offset": 0x64, "size": 4},
        "xp_desc_index": {"offset": 0x68, "size": 4},
        "xp_desc_index_len": {"offset": 0x6C, "size": 4},
        "xp_data_index": {"offset": 0x70, "size": 4},
        "xp_data_index_len": {"offset": 0x74, "size": 4},
        "spaceman_oid": {"offset": 0x78, "size": 8},
        "omap_oid": {"offset": 0x80, "size": 8},
        "reaper_oid": {"offset": 0x88, "size": 8},
        "test_type": {"offset": 0x90, "size": 4},
        "max_file_systems": {"offset": 0x94, "size": 4},
    }

    def __init__(self, fs_stream, offset):
        self.data = self.parse_superblock(fs_stream, offset)
        self.block_size = self.data["block_size"]
        self.offset = offset

    def parse_superblock(self, fs_stream, offset):
        c = Parser.parse(fs_stream, offset+32, BLOCK_SIZE-32, structure=self.structure)
        i = 0
        v = c["max_file_systems"]
        blocksize = c["block_size"]

        structureLower = {
            "fs_oid "+str(i+1): {"offset": 0x98+(i*8), "size": 8} for i in range(0, v)
        }

        structureLowerTwo = {
            "nx_counter": {"offset": 0x98+(v*8), "size": 32*8},   # TODO Hier size nicht richtig?
            # "Array" of counters in reality, here just allocated space
            "nx_blocked_range": {"offset": 0x98+(v*8)+(32*8), "size": 16},
            "nx_evict_mapping_tree": {"offset": 0x108+(v*8)+(32*8), "size": 8},
            "nx_flags": {"offset": 0x110+(v*8)+(32*8), "size": 8},
            "nx_efi_jumpstart": {"offset": 0x118+(v*8)+(32*8), "size": 8},
            "nx_fusion_uuid": {"offset": 0x120+(v*8)+(32*8), "size": 16},
            "nx_keylocker": {"offset": 0x130+(v*8)+(32*8), "size": 16},
            "nx_ephemeral_info": {"offset": 0x140+(v*8)+(32*8), "size": 32},
            # "Array" of Ephemeral info in reality, here just allocated space
            "test_oid": {"offset": 0x160+(v*8)+(32*8), "size": 8},
            "nx_fusion_mt_oid": {"offset": 0x168+(v*8)+(32*8), "size": 8},
            "nx_fusion_wbc_oid": {"offset": 0x170+(v*8)+(32*8), "size": 8},
            "nx_fusion_wbc": {"offset": 0x178+(v*8)+(32*8), "size": 16}




        }

        struct = {**structureLower, **structureLowerTwo}

        e = Parser.parse(fs_stream, offset+32, blocksize-32, structure=struct)

        d = {**c, **e}

        fs_stream.seek(0)

        return d

    def getBlockSize(self):
        return self.block_size

    def getVolumes(self):
        i = 0
        v = self.data["max_file_systems"]
        volumes = []
        for i in range(0, v):
            volumes.append(self.data["fs_oid "+str(i+1)])

        return volumes

    def getObjectMapAdr(self):
        offset_blocks = self.data["omap_oid"]
        # offset in blocks
        offset = offset_blocks * self.block_size
        # offset in bytes
        return offset
