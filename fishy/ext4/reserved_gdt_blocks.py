import logging
import math
import typing as typ

from fishy.ext4.ext4_filesystem.EXT4 import EXT4

LOGGER = logging.getLogger("ext4-reserved-gdt-blocks")


class EXT4ReservedGDTBlocksMetadata:
    """
    holds information about reserved GDT blocks, which are generated during write.
    """
    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of a EXT4ReservedGDTBlocksMetadata
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
        :param length: int, length of the data, which was written to reserved GDT blocks
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

class EXT4ReservedGDTBlocks:
    """
    contains and submethods to write, read and clean data using the reserved gdt blocks of an ext4 filesystem. 
    """
    def __init__(self, stream: typ.BinaryIO, dev: str):
        """
        :param dev: path to an ext4 filesystem
        :param stream: filedescriptor of an ext4 filesystem
        """
        self.dev = dev
        self.stream = stream
        self.ext4fs = EXT4(stream, dev)

    def write(self, instream: typ.BinaryIO) \
            -> EXT4ReservedGDTBlocksMetadata:
        """
        writes from instream into reserved GDT blocks
        :param instream: stream to read from
        :return: EXT4ReservedGDTBlocksMetadata
        """
        metadata = EXT4ReservedGDTBlocksMetadata()
        if not self._check_if_supported():
            raise IOError("This partition does not support reserved GDT blocks")

        total_block_count = self.ext4fs.superblock.data['total_block_count']
        blocks_per_group = self.ext4fs.superblock.data['blocks_per_group']
		#todo maybe add block group 0 here or with separate function due to different structure; 1024 byte boot sector
        if self._check_if_sparse_super_is_set():
            block_ids = self._get_block_ids_for_sparse_super(total_block_count, blocks_per_group)
        else:
            block_ids = self._get_block_ids_for_non_sparse_super(total_block_count, blocks_per_group)

        # file_size = self._calculate_file_size(instream)
        total_space = self._calculate_reserved_space(len(block_ids))
        # if file_size > total_space:
        #     raise IOError("This partition can only hide up to %d bytes of data", total_space)

        file_size = 0
        while instream.peek():
            if len(block_ids) == 0:
                break
            else:
                file_size += len(instream.peek())
                block_id = block_ids.pop(0)
                self._write_to_reserved_gdt_block(instream, block_id)
                metadata.add_block(block_id)

        if instream.peek():
            raise IOError("No reserved GDT blocks left to write data to, but there are"
                          + " still %d Bytes in stream" % len(instream.read()))

        metadata.add_length(file_size)

        return metadata

    def read(self, outstream: typ.BinaryIO, metadata: EXT4ReservedGDTBlocksMetadata) \
            -> None:
        """
        writes data hidden in reserved GDT blocks into outstream
        :param outstream: stream to write into
        :param metadata: EXT4ReservedGDTBlocksMetadata object
        """
        length = metadata.get_length()
        block_size = self.ext4fs.blocksize
        for block_id in metadata.get_blocks():
            offset = block_id * block_size
            self.stream.seek(offset)
            if length < block_size:
                buf = self.stream.read(length)
            else:
                buf = self.stream.read(block_size)
            outstream.write(buf)
            length = length - block_size

    def clear(self, metadata: EXT4ReservedGDTBlocksMetadata) -> None:
        """
        clears the reserved GDT blocks in which data has been hidden
        :param metadata: EXT4ReservedGDTBlocksMetadata object
        """
        block_size = self.ext4fs.blocksize
        for block_id in metadata.get_blocks():
            offset = block_id * block_size
            self.stream.seek(offset)
            self.stream.write(block_size * b'\x00')

    def info(self, metadata: EXT4ReservedGDTBlocksMetadata = None) -> None:
        """
        shows info about the reserved GDT blocks and data hiding space
        :param metadata: EXT4ReservedGDTBlocksMetadata object
        """
        total_block_count = self.ext4fs.superblock.data['total_block_count']
        blocks_per_group = self.ext4fs.superblock.data['blocks_per_group']
        if self._check_if_sparse_super_is_set():
            block_ids = self._get_block_ids_for_sparse_super(total_block_count, blocks_per_group)
        else:
            block_ids = self._get_block_ids_for_non_sparse_super(total_block_count, blocks_per_group)

        total_space = self._calculate_reserved_space(len(block_ids))

        print("Block size: " + str(self.ext4fs.blocksize))
        print("Total hiding space in reserved GDT blocks: " + str(total_space) + " Bytes")
        if metadata != None:
            filled_gdt_blocks = metadata.get_blocks()
            print('Used: ' + str(self._calculate_reserved_space(len(filled_gdt_blocks))) + ' Bytes')

    def _write_to_reserved_gdt_block(self, instream, block_id):
        block_size = self.ext4fs.blocksize
        offset = (block_size * block_id)
        buf = instream.read(block_size)
        self.stream.seek(offset)
        self.stream.write(buf)


    def _check_if_supported(self) \
            -> bool:
        if (int(self.ext4fs.superblock.data['feature_compat'], 0) & 0x10) == 0x10:
            return True
        else:
            return False

    def _check_if_sparse_super_is_set(self) \
            -> bool:
        if (int(self.ext4fs.superblock.data['feature_ro_compat'], 0) & 0x1) == 0x1:
            return True
        else:
            return False

    def _calculate_reserved_space(self, num_of_block_ids) \
            -> int:
        total_space = self.ext4fs.blocksize * num_of_block_ids
        return total_space

    def _calculate_file_size(self, instream) \
            -> bool:
        #pos = instream.tell()
        size = len(instream.read())
        instream.seek(0)
        return size

    def _get_block_ids_for_sparse_super(self, total_block_count, blocks_per_group) \
            -> []:
        block_ids = []
        total_block_group_count = int(math.ceil(total_block_count / blocks_per_group))
        if self.ext4fs.gdt.is_64bit:
            architecture = 64
        else:
            architecture = 32
        gdt_size = int(math.ceil((architecture * total_block_group_count) / self.ext4fs.blocksize))
		
        # block group 0
        # todo; 1024 buffer at beginning, 

        # 3^x
        block_group_id = 3
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id + 2 + gdt_size
            number_of_reserved_gdt_blocks = self.ext4fs.superblock.data['res_gdt_blocks']
            for i in range(block_id, (block_id + number_of_reserved_gdt_blocks)):
                block_ids.append(i)
            block_group_id = 3 * block_group_id

        # 5^x
        block_group_id = 5
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id + 2 + gdt_size
            number_of_reserved_gdt_blocks = self.ext4fs.superblock.data['res_gdt_blocks']
            for i in range(block_id, (block_id + number_of_reserved_gdt_blocks)):
                block_ids.append(i)
            block_group_id = 5 * block_group_id

        # 7^x
        block_group_id = 7
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id + 2 + gdt_size
            number_of_reserved_gdt_blocks = self.ext4fs.superblock.data['res_gdt_blocks']
            for i in range(block_id, (block_id + number_of_reserved_gdt_blocks)):
                block_ids.append(i)
            block_group_id = 7 * block_group_id
			
        #todo sort block ids list?
        block_ids.sort()
        return block_ids

    def _get_block_ids_for_non_sparse_super(self, total_block_count, blocks_per_group) \
            -> []:
        block_ids = []
		#todo block id group 0, 1024 byte buffer at beginning
        block_group_id = 1
        total_block_group_count = int(math.ceil(total_block_count / blocks_per_group))
        if self.ext4fs.gdt.is_64bit:
            architecture = 64
        else:
            architecture = 32
        gdt_size = int(math.ceil((architecture * total_block_group_count) / self.ext4fs.blocksize))
        while block_group_id < total_block_group_count:
            block_id = (block_group_id * blocks_per_group)
            block_id = block_id + 2 + gdt_size
            number_of_reserved_gdt_blocks = self.ext4fs.superblock.data['res_gdt_blocks']
            for i in range(block_id, (block_id + number_of_reserved_gdt_blocks)):
                block_ids.append(i)
            block_group_id += 1

        block_ids.sort()
        return block_ids