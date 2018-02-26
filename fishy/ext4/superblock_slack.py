import logging
import math
import typing as typ

from fishy.ext4.ext4_filesystem.EXT4 import EXT4

LOGGER = logging.getLogger("ext4-superblock_slack")

class EXT4SuperblockSlackMetadata:
    """
    Metadata Class for Superblock Slack
    """
    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of a EXT4SuperblockSlackMetadata
                  object
        """
        if d is None:
            self.blocks = []
            self.length = []
        else:
            self.blocks = d["blocks"]
            self.length = d["length"]

    def add_block(self, block_id: int) -> None:
        """
        adds a block to the list of blocks
        :param block_id: int, id of the block
        """
        self.blocks.append(block_id)

    def add_length(self, length: int) -> None:
        """
        adds the length of the hidden data
        :param length: int, length of the data, which was written to superblock slack
        """
        self.length.append(length)

    def get_blocks(self) \
            -> []:
        """
        returns list of block ids
        :returns: list of block_ids
        """
        return self.blocks

    def get_length(self) \
            -> int:
        """
        returns length of the hidden data
        :returns: length of the hidden data
        """
        return self.length[0]

class EXT4SuperblockSlack:
    def __init__(self, stream: typ.BinaryIO, dev: str):
        """
        :param dev: path to an ext4 filesystem
        :param stream: filedescriptor of an ext4 filesystem
        """
        self.dev = dev
        self.stream = stream
        self.ext4fs = EXT4(stream, dev)

    def write(self, instream: typ.BinaryIO) \
            -> EXT4SuperblockSlackMetadata:
        """
        writes from instream into superblock slack
        :param instream: stream to read from
        :return: EXT4SuperblockSlackMetadata
        """
        metadata = EXT4SuperblockSlackMetadata()
        if self.ext4fs.blocksize<=1024:
           raise IOError("This hidding technique requires a blocksize of more than 1024")
        total_block_count = self.ext4fs.superblock.data['total_block_count']
        blocks_per_group = self.ext4fs.superblock.data['blocks_per_group']
        if self._check_if_sparse_super_is_set():
            block_ids = self._get_block_ids_for_sparse_super(total_block_count, blocks_per_group)
        else:
            block_ids = self._get_block_ids_for_non_sparse_super(total_block_count, blocks_per_group)
        file_size=0
        file_size+=self._write_to_superblock(instream)
        metadata.add_block(0)
        while instream.peek():
            if len(block_ids)==0:
                break
            else:
                block_id=block_ids.pop(0)
                file_size+=self._write_to_backup_superblock(instream,block_id,blocks_per_group)
                metadata.add_block(block_id)

        if instream.peek():
            raise IOError("No slackspace left to write data to, but there are"
                          + " still %d Bytes in stream" % len(instream.read()))
        metadata.add_length(file_size)

        return metadata

    def read(self, outstream: typ.BinaryIO, metadata: EXT4SuperblockSlackMetadata) \
            -> None:
        """
        writes data hidden in superblock slack into outstream
        :param outstream: stream to write into
        :param metadata: EXT4ReservedGDTBlocksMetadata object
        """
        length = metadata.get_length()
        block_size = self.ext4fs.blocksize
        for block_id in metadata.get_blocks():
            if block_id==0:
                offset=2048
                slackspace=block_size-2048
            else:
                offset=block_id * block_size+1024
                slackspace=block_size-1024
            self.stream.seek(offset)
            if length < slackspace:
                buf = self.stream.read(length)
            else:
                buf = self.stream.read(slackspace)
            outstream.write(buf)
            length = length - slackspace


    def clear(self, metadata: EXT4SuperblockSlackMetadata) -> None:
        """
        clears the superblock slack in which data has been hidden
        :param metadata: EXT4ReservedGDTBlocksMetadata object
        """
        block_size = self.ext4fs.blocksize
        for block_id in metadata.get_blocks():
            if block_id==0:
                offset=2048
                slackspace=block_size-2048
            else:
                offset=block_id * block_size+1024
                slackspace=block_size-1024
            self.stream.seek(offset)
            self.stream.write(slackspace * b'\x00')

    def info(self, metadata: EXT4SuperblockSlackMetadata = None) -> None:
        """
        shows info about the superblock slack and data hiding space
        :param metadata: EXT4SuperblockSlackMetadata object
        """
        total_block_count = self.ext4fs.superblock.data['total_block_count']
        blocks_per_group = self.ext4fs.superblock.data['blocks_per_group']
        if self._check_if_sparse_super_is_set():
            block_ids = self._get_block_ids_for_sparse_super(total_block_count, blocks_per_group)
        else:
            block_ids = self._get_block_ids_for_non_sparse_super(total_block_count, blocks_per_group)

        total_space = self._calculate_slack_space(len(block_ids))

        print("Block size: " + str(self.ext4fs.blocksize))
        print("Total hiding space in superblock slack space: " + str(total_space) + " Bytes")
        if metadata != None:
            print('Used: ' + str(metadata.get_length()) + ' Bytes')

    def _check_if_sparse_super_is_set(self) \
            -> bool:
        """
        checks if the sparse superblock flag is set
        :return:bool
        """
        if (int(self.ext4fs.superblock.data['feature_ro_compat'], 0) & 0x1) == 0x1:
            return True
        else:
            return False

    def _get_block_ids_for_sparse_super(self, total_block_count, blocks_per_group) \
            -> []:
        """
        calculates the blockid for the superblock copies
        assuming the sparse superblock flag is set
        :param total_block_count:
        :param blocks_per_group:
        :return: list containing the blockids
        """
        block_ids = []
        total_block_group_count = int(math.ceil(total_block_count / blocks_per_group))

        if total_block_group_count>1:
            block_ids.append(blocks_per_group)

        # 3^x
        block_group_id = 3
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id
            block_ids.append(block_id)
            block_group_id = 3 * block_group_id

        # 5^x
        block_group_id = 5
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id
            block_ids.append(block_id)
            block_group_id = 5 * block_group_id

        # 7^x
        block_group_id = 7
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id
            block_ids.append(block_id)
            block_group_id = 7 * block_group_id

        return block_ids

    def _get_block_ids_for_non_sparse_super(self, total_block_count, blocks_per_group) \
            -> []:
        """
        calculates the blockid for the superblock copies
        assuming the sparse superblock flag is not set
        :param total_block_count:
        :param blocks_per_group:
        :return: list containing the blockids
        """
        block_ids = []
        block_group_id = 1
        total_block_group_count = int(math.ceil(total_block_count / blocks_per_group))
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id
            block_ids.append(block_id)
            block_group_id += 1

        return block_ids

    def _calculate_slack_space(self, num_of_block_ids) \
            -> int:
        """
        calculates avaible slackspace
        :param num_of_block_ids: number of superblock copies
        :return: total slackspace
        """
        total_space = (self.ext4fs.blocksize-1024) * num_of_block_ids
        total_space = total_space + (self.ext4fs.blocksize-2048)
        return total_space

    def _write_to_superblock(self, instream)->int:
        """
        writes from instream into Slackspace of primary superblock
        :param instream: stream to read data from
        :return: number of bytes written
        """
        block_size = self.ext4fs.blocksize
        slackspace=block_size-2048
        buf=instream.read(slackspace)
        self.stream.seek(2048)
        self.stream.write(buf)
        return len(buf)

    def _write_to_backup_superblock(self, instream, block_id,blocks_per_group)->int:
        """
        writes from instream into slackspace of superblock copy
        :param instream: instream: stream to read data from
        :param block_id: blockid of superblockcopy to write to
        :param blocks_per_group:
        :return: number of bytes written
        """
        block_size=self.ext4fs.blocksize
        slackspace=block_size-1024
        buf=instream.read(slackspace)
        offset=block_id*block_size+1024
        self.stream.seek(offset)
        self.stream.write(buf)
        return len(buf)
