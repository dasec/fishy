import typing as typ
from pytsk3 import FS_Info, Img_Info

from fishy.ext4.ext_filesystem.gdt import GDT
from fishy.ext4.ext_filesystem.inode_table import InodeTable
from fishy.ext4.ext_filesystem.superblock import Superblock


class EXT4:

    def __init__(self, stream: typ.BinaryIO, dev: str):
        self.blocksize = self._get_blocksize(dev)
        self.superblock = Superblock(stream)
        self.gdt = GDT(stream, self.superblock, self.blocksize)

        # get inode table for each gdt entry
        self.inode_tables = []
        for gdt_entry in self.gdt.data:
            table_start = gdt_entry['inode_table_lo'] * self.blocksize
            self.inode_tables.append(InodeTable(stream, self.superblock, table_start, self.blocksize))

    def _get_blocksize(self, dev):
        img_info = Img_Info(dev)
        fs_info = FS_Info(img_info, offset=0)
        return fs_info.info.block_size