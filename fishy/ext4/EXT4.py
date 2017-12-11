from fishy.ext4.superblock import Superblock
from fishy.ext4.ext4_gdt import GDT
import typing as typ
from pytsk3 import FS_Info, Img_Info

class EXT4:

    def __init__(self, stream: typ.BinaryIO, dev: str):
        self.blocksize = self._get_blocksize(dev)
        self.superblock = Superblock(stream)
        self.gdt = GDT(stream, self.superblock, self.blocksize)

    def _get_blocksize(self, dev):
        img_info = Img_Info(dev)
        fs_info = FS_Info(img_info, offset=0)
        return fs_info.info.block_size