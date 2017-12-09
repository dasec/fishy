from fishy.ext4.superblock import Superblock
from fishy.ext4.ext4_gdt import GDT

class EXT4:

    def __init__(self, image):
        self.superblock = Superblock(image)
        self.gdt = GDT(image, self.superblock)