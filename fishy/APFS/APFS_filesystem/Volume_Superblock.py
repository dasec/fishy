# structure of volume superblock; at first only for potential links in container

from fishy.APFS.APFS_filesystem.APFS_Parser import Parser

class vSuperblock:

    structure = {
        "magic": {"offset": 0x0, "size": 4, "format": "raw"},
        "fs_index": {"offset": 0x4, "size": 4},
        "features": {"offset": 0x8, "size": 8},
        "readonly_features": {"offset": 0x10, "size": 8},
        "incompatible_features": {"offset": 0x18, "size": 8},
        "unmount_time": {"offset": 0x20, "size": 8, "format": "hex"},
        "reserve_block_count": {"offset": 0x28, "size": 8},
        "quota_block_count": {"offset": 0x30, "size": 8},
        "alloc_block_count": {"offset": 0x38, "size": 8},
        "crypto_meta": {"offset": 0x40, "size": 32, "format": "raw"},
        # single values unimportant; easily implementable via official ref
      #  "root_tree_type": {"offset": 0x60, "size": 4}, in doc but not in image
       # "extentref_tree_type": {"offset": 0x64, "size": 4}, in doc but not in image
       # "snapmeta_tree_type": {"offset": 0x68, "size": 4}, in doc but not in image
        "omap_oid": {"offset": 0x60, "size": 8},
        "root_tree_oid": {"offset":  0x68, "size": 8},
        "extentref_tree_oid": {"offset": 0x70, "size": 8},
        "snapmeta_tree_oid": {"offset": 0x78, "size": 8},
        "revert_to_xid": {"offset": 0x80, "size": 8},
        "revert_to_sblock_oid": {"offset": 0x88, "size": 8},
        "next_obj_id": {"offset": 0x90, "size": 8},
        "num_files": {"offset": 0x98, "size": 8},
        "num_dir": {"offset": 0xA0, "size": 8},
        "num_symlinks": {"offset": 0xA8, "size": 8},
        "num_other_fs_obj": {"offset": 0xB0, "size": 8},
        "num_snapshots": {"offset": 0xB8, "size": 8},
        "total_blocks_alloc": {"offset": 0xC0, "size": 8},
        "total_block_freed": {"offset": 0xC8, "size": 8},
        "vol_uuid": {"offset": 0xD0, "size": 16},
        "last_mod_time": {"offset": 0xE0, "size": 8, "format": "hex"},
        "fs_flags": {"offset": 0xE8, "size": 8, "format": "hex"},
        "apfs_formatted_by_id": {"offset": 0xF0, "size": 32, "format": "utf"},
        "apfs_formatted_by_timestamp": {"offset": 0xF0+32, "size": 8, "format": "hex"},
        "apfs_formatted_by_xid": {"offset": 0xF0+40, "size": 8}
    }


    def __init__(self, fs_stream, offset, blocksize):
        self.fs_stream = fs_stream
        self.blocksize = blocksize
        self.data = self.parseVolumeSuperblock(fs_stream, offset)
        self.offset = offset

    def parseVolumeSuperblock(self, fs_stream, offset):
        blocksize = self.blocksize
        d = Parser.parse(fs_stream, offset+32, blocksize-32, structure=self.structure)



        structLowerId = {
            "apfs_modified_by_id " + str(i): {"offset": 0xF0+48+(i*48), "size": 32, "format": "utf"} for i in range(0,8)
        }

        structLowerTs = {
            "apfs_modified_by_timestamp " + str(i): {"offset": 0xF0+80+(i*48), "size": 8, "format": "hex"} for i in range(0,8)
        }

        s1 = {**structLowerId, **structLowerTs}

        structLowerXid = {
            "apfs_modified_by_xid " + str(i): {"offset": 0xF0+88+(i*48), "size": 8} for i in range(0,8)
        }

        s2 = {**s1, **structLowerXid}


        structLowerToo = {
            "volname": {"offset": 0xF0 + (48 * 9), "size": 256, "format": "utf"},
            "next_doc_id": {"offset": 0xF0 + (48 * 9) + 256, "size": 4},
            "role": {"offset": 0xF4 + (48 * 9) + 256, "size": 2},
            "reserved1": {"offset": 0xF6 + (48 * 9) + 256, "size": 2},
            "root_to_xid": {"offset": 0xF8 + (48 * 9) + 256, "size": 8},
            "er_state_oid": {"offset": 0x100 + (48 * 9) + 256, "size": 8},
            "reserved2": {"offset": 0x100 + (48 * 9) + 256, "size": 60}

            # Timestamps are not implemented completely due to their unique structure
        }

        s3 = {**s2, **structLowerToo}

        e = Parser.parse(fs_stream, offset+32, blocksize-32, structure=s3)

        f = {**e, **d}

        return f

    def getOmapRootNode(self):
        blocksize = self.blocksize

        return self.data["omap_oid"]*blocksize

    def getExtentRefTree(self):
        blocksize = self.blocksize

        return self.data["extentref_tree_oid"]*blocksize

    def getrootTreeOid(self):

        return self.data["root_tree_oid"]



