import logging
import math
import typing as typ

from fishy.ext4.ext4_filesystem.EXT4 import EXT4

LOGGER = logging.getLogger("ext4-obso_faddr")


class EXT4FADDRMetadata:
    """
    holds inode numbers which hold the hidden data in.
    """
    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of a EXT4FADDRMetadata
                  object
        """
        if d is None:
            # self.inode_table = None
            self.inode_numbers = []
        else:
            # self.inode_table = d["inode_table"]
            self.inode_numbers = d["inode_numbers"]

    def add_inode_number(self, inode_number: int) -> None:
        """
        adds a block to the list of blocks
        :param block_id: int, id of the block
        """
        self.inode_numbers.append(inode_number)

    def get_inode_numbers(self) \
            -> []:
        """
        returns list of inode_numbers
        :returns: list of inode_numbers
        """
        return self.inode_numbers

class EXT4FADDR:
    """
        Hides data in obso_faddr field of inodes in the first inode_table.
    """
    def __init__(self, stream: typ.BinaryIO, dev: str):
        """
        :param dev: path to an ext4 filesystem
        :param stream: filedescriptor of an ext4 filesystem
        """
        self.dev = dev
        self.stream = stream
        self.ext4fs = EXT4(stream, dev)
        self.inode_table = self.ext4fs.inode_tables[0]

    def write(self, instream: typ.BinaryIO) -> EXT4FADDRMetadata:
        """
        writes from instream into the last two bytes of inodes obso_faddr field.
        This method currently supports only data sizes less than 4000 bytes.
        :param instream: stream to read from
        :return: EXT4FADDRMetadata
        """
        metadata = EXT4FADDRMetadata()
        instream = instream.read()

        if not self._check_if_supported(instream):
            raise IOError("The hiding data size is currently not supported")


        instream_chunks = [instream[i:i+4] for i in range(0, len(instream), 4)]
        # print(instream_chunks)
        inode_number = 1
        hidden_chunks = 0

        while hidden_chunks < len(instream_chunks):
            chunk = instream_chunks[hidden_chunks]

            if self._write_to_obso_faddr(chunk, inode_number):
                metadata.add_inode_number(inode_number)
                hidden_chunks += 1

            inode_number += 1

        return metadata

    def read(self, outstream: typ.BinaryIO, metadata: EXT4FADDRMetadata) \
            -> None:
        """
        writes data hidden in obso_faddr blocks into outstream
        :param outstream: stream to write into
        :param metadata: EXT4FADDRMetadata object
        """
        inode_numbers = metadata.get_inode_numbers()
        # print(inode_numbers)
        for nr in inode_numbers:
            outstream.write(self._read_from_obso_faddr(nr))

    def clear(self, metadata: EXT4FADDRMetadata) -> None:
        """
        clears the obso_faddr field in which data has been hidden
        :param metadata: EXT4FADDRMetadata object
        """
        inode_numbers = metadata.get_inode_numbers()
        for nr in inode_numbers:
            self._clear_obso_faddr(nr)

    def info(self, metadata: EXT4FADDRMetadata = None) -> None:
        """
        shows info about inode obso_faddr fields and data hiding space
        :param metadata: EXT4FADDRMetadata object
        """
        print("Inodes: " + str(self.ext4fs.superblock.data["inode_count"]))
        print("Total hiding space in obso_faddr fields: " + str((self.ext4fs.superblock.data["inode_count"]) * 4) + " Bytes")
        if metadata != None:
            filled_inode_numbers = metadata.get_inode_numbers()
            print('Used: ' + str(len(filled_inode_numbers) * 4) + ' Bytes')

    def _write_to_obso_faddr(self, instream_chunk, inode_nr) -> bool:
        # print(instream_chunk)
        self.stream.seek(0)
        total_obso_faddr_offset = self._get_total_obso_faddr_offset(inode_nr)
        # print(total_obso_faddr_offset)
        self.stream.seek(total_obso_faddr_offset)
        if self.stream.read(4) == b'\x00\x00\x00\x00':      #\x00\x00
            self.stream.seek(total_obso_faddr_offset)
            # print(self.stream.read(12))
            self.stream.write(instream_chunk)
            return True
        else:
            return False

    def _clear_obso_faddr(self, inode_nr: int):
        total_obso_faddr_offset = self._get_total_obso_faddr_offset(inode_nr)
        self.stream.seek(total_obso_faddr_offset)
        self.stream.write(b"\x00\x00\x00\x00")   #\x00\x00

    def _read_from_obso_faddr(self, inode_nr: int):
        self.stream.seek(0)
        total_obso_faddr_offset = self._get_total_obso_faddr_offset(inode_nr)
        self.stream.seek(total_obso_faddr_offset)
        data = self.stream.read(4)
        # print(data)
        return data

    def _get_total_obso_faddr_offset(self, inode_nr: int) -> int:
        inode_size = self.ext4fs.superblock.data["inode_size"]
        # print("table start", self.inode_table.table_start)

        return self.inode_table.inodes[inode_nr].offset + 0x70

    def _check_if_supported(self, instream) -> bool:
        if len(instream) >= ((self.ext4fs.superblock.data["inode_count"]) * 4):
            return False
        else:
            return True
