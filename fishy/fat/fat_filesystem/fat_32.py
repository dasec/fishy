import typing as typ
from construct import Struct, Array, Padding, Embedded, Bytes, this
from .bootsector import FAT32_BOOTSECTOR
from .dir_entry import DIR_ENTRY, LFN_ENTRY
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

    def _get_dir_entries(self, cluster_id: int) \
            -> typ.Generator[typ.Tuple[Struct, str], None, None]:
        """
        iterator for reading a cluster as directory and parse its content
        :param cluster_id: int, cluster to parse,
                           if cluster_id == 0, parse rootdir
        :return: tuple of (DIR_ENTRY, lfn)
        """
        # TODO: The english wikipedia entry hints that using 0x00 as
        #       an end-marker is deprecated. How FAT32 does then determine
        #       that the end of a directory was reached?
        lfn = ''
        start_cluster_id = self.get_cluster_start(cluster_id)
        self.stream.seek(start_cluster_id)
        end_marker = 0xff
        while end_marker != 0x00:
            # read 32 bit into variable
            raw = self.stream.read(32)
            # parse as DIR_ENTRY
            dir_entry = DIR_ENTRY.parse(raw)
            attr = dir_entry.attributes
            # If LFN attributes are set, parse it as LFN_ENTRY instead
            if attr.volumeLabel and attr.system and attr.hidden and attr.readonly:
                # if lfn attributes set, convert it to lfnEntry
                # and save it for later use
                dir_entry = LFN_ENTRY.parse(raw)
                lfnpart = dir_entry.name1 + dir_entry.name2 + dir_entry.name3

                # remove non-chars after padding
                retlfn = b''
                for i in range(int(len(lfnpart) / 2)):
                    i *= 2
                    next_bytes = lfnpart[i:i+2]
                    if next_bytes != b'\x00\x00':
                        retlfn += next_bytes
                    else:
                        break
                # append our lfn part to the global lfn, that will
                # later used as the filename
                lfn = retlfn.decode('utf-16') + lfn
            else:
                retlfn = lfn
                lfn = ''
                end_marker = dir_entry.name[0]
                # add start_cluster attribute for convenience
                start_cluster = int.from_bytes(dir_entry.firstCluster +
                                               dir_entry.accessRightsBitmap,
                                               byteorder='little')
                dir_entry.start_cluster = start_cluster
                yield (dir_entry, retlfn)
