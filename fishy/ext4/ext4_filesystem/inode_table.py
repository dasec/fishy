from .inode import Inode

class InodeTable:
    """
    This class represents a single inode table.
    """

    inodes = []

    def __init__(self, fs_stream, superblock, offset, blocksize):
        self.blocksize = blocksize
        self.table_start = offset
        self.inode_size = superblock.data["inode_size"]
        self.table_size = superblock.data['inodes_per_group'] * self.inode_size

        for addr in range(self.table_start, self.table_start+self.table_size, self.inode_size):
            inode = Inode(fs_stream, addr, self.inode_size, self.blocksize)
            self.inodes.append(inode)
