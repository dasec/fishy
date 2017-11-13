"""
Implementation of a FAT32 filesystem reader

example usage:
>>> with open('testfs.dd', 'rb') as filesystem:
>>>     fs = FAT32(filesystem)

example to print all entries in root directory:
>>>     for i, v in fs.get_root_dir_entries():
>>>         if v != "":
>>>             print(v)

example to print all fat entries
>>>     for i in range(fs.entries_per_fat):
>>>         print(i,fs.get_cluster_value(i))

example to print all root directory entries
>>>     for i,v in fs.get_root_dir_entries():
>>>         if v != "":
>>>             print(v, i.start_cluster)

"""
import typing as typ
from construct import Struct, Array, Padding, Embedded, Bytes, this
from .bootsector import FAT32_BOOTSECTOR, FAT_CORE_BOOTSECTOR, \
    FAT32_EXTENDED_BOOTSECTOR
from .fat import FAT
from .fat_entry import FAT32Entry


FAT32_PRE_DATA_REGION = Struct(
    "bootsector" / Embedded(FAT32_BOOTSECTOR),
    Padding((this.reserved_sector_count - 2) * this.sector_size),
    # FATs
    "fats" / Array(this.fat_count, Bytes(this.sectors_per_fat * this.sector_size)),
    )


class FAT32(FAT):
    """
    FAT32 filesystem implementation.
    """
    def __init__(self, stream: typ.BinaryIO):
        """
        :param stream: filedescriptor of a FAT32 filesystem
        """
        super().__init__(stream, FAT32_PRE_DATA_REGION)
        self.entries_per_fat = int(self.pre.sectors_per_fat
                                   * self.pre.sector_size
                                   / 4)
        self._fat_entry = FAT32Entry
        self.fat_type = 'FAT32'

    def get_cluster_value(self, cluster_id: int) -> typ.Union[int, str]:
        """
        finds the value that is written into fat
        for given cluster_id
        :param cluster_id: int, cluster that will be looked up
        :return: int or string
        """
        byte = cluster_id*4
        # TODO: Use active FAT
        byte_slice = self.pre.fats[0][byte:byte+4]
        value = int.from_bytes(byte_slice, byteorder='little')
        # TODO: Remove highest 4 Bits as FAT32 uses only 28Bit
        #       long addresses.
        return self._fat_entry.parse(value.to_bytes(4, 'little'))

    def _root_to_stream(self, stream: typ.BinaryIO) -> None:
        """
        write root directory into a given stream
        :param stream: stream, where the root directory will be written into
        """
        raise NotImplementedError

    def get_root_dir_entries(self) \
            -> typ.Generator[typ.Tuple[Struct, str], None, None]:
        return self.get_dir_entries(self.pre.rootdir_cluster)

    def write_free_clusters(self, new_value: int) -> None:
        """
        Write a new value to free_cluster_count field of FAT32 FS INFO sector
        :param new_value: int, new value for free_cluster_count
        """
        # calculate start address of FS_INFO sector
        bootsector_size = FAT_CORE_BOOTSECTOR.sizeof() \
                          + FAT32_EXTENDED_BOOTSECTOR.sizeof()
        bootsector_padd = self.pre.sector_size - bootsector_size
        fs_info_start = bootsector_size + bootsector_padd
        free_cluster_offset = 488
        # write new value to disk
        self.stream.seek(self.offset + fs_info_start + free_cluster_offset)
        self.stream.write(int(new_value).to_bytes(4, 'little'))
        # re-read pre_data_region
        self.stream.seek(self.offset)
        self.pre = FAT32_PRE_DATA_REGION.parse_stream(self.stream)

    def write_last_allocated(self, new_value: int) -> None:
        """
        Write a new value to 'last_allocated_data_cluster' field of FAT32
        FS INFO sector
        :param new_value: int, new value for free_cluster_count
        """
        # calculate start address of FS_INFO sector
        bootsector_size = FAT_CORE_BOOTSECTOR.sizeof() \
                          + FAT32_EXTENDED_BOOTSECTOR.sizeof()
        bootsector_padd = self.pre.sector_size - bootsector_size
        fs_info_start = bootsector_size + bootsector_padd
        free_cluster_offset = 492
        # write new value to disk
        self.stream.seek(self.offset + fs_info_start + free_cluster_offset)
        self.stream.write(int(new_value).to_bytes(4, 'little'))
        # re-read pre_data_region
        self.stream.seek(self.offset)
        self.pre = FAT32_PRE_DATA_REGION.parse_stream(self.stream)
