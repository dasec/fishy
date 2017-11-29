from .superblock import Superblock

class EXT4:

    def __init__(self, image):
        self.superblock = Superblock(image)