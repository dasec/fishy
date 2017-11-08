import typing as typ
from construct import Struct, Array, Padding, Embedded, Bytes, this
from .bootsector import FAT12_16_BOOTSECTOR
from .dir_entry import DIR_ENTRY
from .fat import FAT
from .fat_entry import FAT16Entry


FAT16_PRE_DATA_REGION = Struct(
    "bootsector" / Embedded(FAT12_16_BOOTSECTOR),
    Padding((this.reserved_sector_count - 1) * this.sector_size),
    # FATs
    "fats" / Array(this.fat_count, Bytes(this.sectors_per_fat * this.sector_size)),
    # RootDir Table
    "rootdir" / Bytes(this.rootdir_entry_count * DIR_ENTRY.sizeof())
    )


class FAT16(FAT):
    """
    FAT16 filesystem implementation.
    """
    def __init__(self, stream: typ.BinaryIO):
        """
        :param stream: filedescriptor of a FAT16 filesystem
        """
        super().__init__(stream, FAT16_PRE_DATA_REGION)
        self.entries_per_fat = int(self.pre.sectors_per_fat
                                   * self.pre.sector_size
                                   / 2)
        self._fat_entry = FAT16Entry

    def get_cluster_value(self, cluster_id: int) -> typ.Union[int, str]:
        """
        finds the value that is written into fat
        for given cluster_id
        :param cluster_id: int, cluster that will be looked up
        :return: int or string
        """
        byte = cluster_id*2
        byte_slice = self.pre.fats[0][byte:byte+2]
        value = int.from_bytes(byte_slice, byteorder='little')
        return self._fat_entry.parse(value.to_bytes(2, 'little'))

    def _root_to_stream(self, stream: typ.BinaryIO) -> None:
        """
        write root directory into a given stream
        :param stream: stream, where the root directory will be written into
        """
        stream.write(self.pre.rootdir)
