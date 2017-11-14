"""
Implementation of a FAT12 filesystem reader

example usage:
>>> with open('testfs.dd', 'rb') as filesystem:
>>>     fs = FAT12(filesystem)

example to print all entries in root directory:
>>>     for i, v in fs.get_root_dir_entries():
>>>         if v != "":
>>>             print(v)

example to print all fat entries
>>>     for i in range(fs.entries_per_fat):
>>>         print(i,fs.get_cluster_value(i))

example to print all root directory entries
>>>     for entry in fs.get_root_dir_entries():
>>>         print(v, entry.get_start_cluster())

"""
import typing as typ
from construct import Struct, Array, Padding, Embedded, Bytes, this
from .bootsector import FAT12_16_BOOTSECTOR
from .dir_entry import DIR_ENTRY_DEFINITION as DIR_ENTRY
from .fat import FAT
from .fat_entry import FAT12Entry


FAT12_PRE_DATA_REGION = Struct(
    "bootsector" / Embedded(FAT12_16_BOOTSECTOR),
    Padding((this.reserved_sector_count - 1) * this.sector_size),
    # FATs.
    "fats" / Array(this.fat_count, Bytes(this.sectors_per_fat * this.sector_size)),
    # RootDir Table
    "rootdir" / Bytes(this.rootdir_entry_count * DIR_ENTRY.sizeof())
    )


class FAT12(FAT):
    """
    FAT12 filesystem implementation.
    """
    def __init__(self, stream):
        """
        :param stream: filedescriptor of a FAT12 filesystem
        """
        super().__init__(stream, FAT12_PRE_DATA_REGION)
        self.entries_per_fat = int(self.pre.sectors_per_fat
                                   * self.pre.sector_size
                                   * 8 / 12)
        self._fat_entry = FAT12Entry
        self.fat_type = 'FAT12'

    def get_cluster_value(self, cluster_id: int) -> typ.Union[int, str]:
        """
        finds the value that is written into fat
        for given cluster_id
        :param cluster_id: int, cluster that will be looked up
        :return: int or string
        """
        # as python read does not allow to read simply 12 bit,
        # we need to do some fancy stuff to extract those from
        # 16 bit long reads
        # this strange layout results from the little endianess
        # which causes that:
        # * clusternumbers beginning at the start of a byte use this
        #   byte + the second nibble of the following byte.
        # * clusternumbers beginning in the middle of a byte use
        #   the first nibble of this byte + the second byte
        # because of little endianess these nibbles need to be
        # reordered as by default int() interpretes hexstrings as
        # big endian
        #
        byte = cluster_id + int(cluster_id/2)
        byte_slice = self.pre.fats[0][byte:byte+2]
        if cluster_id % 2 == 0:
            # if cluster_number is even, we need to wipe the third nibble
            hexvalue = byte_slice.hex()
            value = int(hexvalue[3] + hexvalue[0:2], 16)
        else:
            # if cluster_number is odd, we need to wipe the second nibble
            hexvalue = byte_slice.hex()
            value = int(hexvalue[2:4] + hexvalue[0], 16)
        return self._fat_entry.parse(value.to_bytes(2, 'little'))

    def write_fat_entry(self, cluster_id: int,
                        value: typ.Union[int, str]) -> None:
        # make sure cluster_id is valid
        if cluster_id < 0 or cluster_id >= self.entries_per_fat:
            raise AttributeError("cluster_id out of bounds")
        # make sure user does not input invalid values as next cluster
        if isinstance(value, int):
            assert value <= 4086, "next_cluster value must be <= 4086. For " \
                                  + "last cluster use 'last_cluster'. For " \
                                  + "bad_cluster use 'bad_cluster'"
            assert value >= 2, "next_cluster value must be >= 2. For " \
                               + "free_cluster use 'free_cluster'"
        # get start position of FAT0
        fat0_start = self.offset + 512 + (self.pre.sector_size - 512) + \
            (self.pre.reserved_sector_count - 1) * self.pre.sector_size
        fat1_start = fat0_start + self.pre.sectors_per_fat \
            * self.pre.sector_size
        # read current entry
        byte = cluster_id + int(cluster_id/2)
        self.stream.seek(fat0_start + byte)
        current_entry = self.stream.read(2).hex()
        new_entry_hex = self._fat_entry.build(value).hex()
        # calculate new entry as next entry overlaps with current bytes
        if cluster_id % 2 == 0:
            # if cluster_number is even, we need to keep the third nibble
            new_entry = new_entry_hex[0:2] + current_entry[2] \
                + new_entry_hex[3]
        else:
            # if cluster_number is odd, we need to keep the second nibble
            new_entry = new_entry_hex[1] + current_entry[1] + \
                    new_entry_hex[3] + new_entry_hex[0]
        # convert hex to bytes
        new_entry = bytes.fromhex(new_entry)
        # write new value to first fat on disk
        self.stream.seek(fat0_start + byte)
        self.stream.write(new_entry)
        # write new value to second fat on disk if it exists
        if self.pre.fat_count > 1:
            self.stream.seek(fat1_start + byte)
            self.stream.write(new_entry)
        # flush changes to disk
        self.stream.flush()
        # re-read fats into memory
        fat_definition = Array(self.pre.fat_count,
                               Bytes(self.pre.sectors_per_fat *
                                     self.pre.sector_size))
        self.stream.seek(fat0_start)
        self.pre.fats = fat_definition.parse_stream(self.stream)

    def _root_to_stream(self, stream: typ.BinaryIO) -> None:
        """
        write root directory into a given stream
        :param stream: stream, where the root directory will be written into
        """
        stream.write(self.pre.rootdir)
