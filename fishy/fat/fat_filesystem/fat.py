"""
FAT12, FAT16 and FAT32 reader

examples:
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
>>>     for i,v in fs.get_root_dir_entries():
>>>         if v != "":
>>>             print(v, i.start_cluster)

"""

import logging
import typing as typ
from io import BytesIO, BufferedReader
from construct import Struct, Array, Padding, Embedded, Bytes, this
from .bootsector import FAT12_16_BOOTSECTOR, FAT32_BOOTSECTOR
from .dir_entry import DIR_ENTRY, LFN_ENTRY
from .fat_entry import FAT12Entry, FAT16Entry, FAT32Entry


logger = logging.getLogger("FATFilesystem")


class NoFreeClusterAvailable(Exception):
    """
    This exception can be thrown by the get_free_cluster method of a FAT
    instance.
    """
    pass


FAT12_PRE_DATA_REGION = Struct(
    "bootsector" / Embedded(FAT12_16_BOOTSECTOR),
    Padding((this.reserved_sector_count - 1) * this.sector_size),
    # FATs.
    "fats" / Array(this.fat_count, Bytes(this.sectors_per_fat * this.sector_size)),
    # RootDir Table
    "rootdir" / Bytes(this.rootdir_entry_count * DIR_ENTRY.sizeof())
    )

FAT16_PRE_DATA_REGION = Struct(
    "bootsector" / Embedded(FAT12_16_BOOTSECTOR),
    Padding((this.reserved_sector_count - 1) * this.sector_size),
    # FATs
    "fats" / Array(this.fat_count, Bytes(this.sectors_per_fat * this.sector_size)),
    # RootDir Table
    "rootdir" / Bytes(this.rootdir_entry_count * DIR_ENTRY.sizeof())
    )

FAT32_PRE_DATA_REGION = Struct(
    "bootsector" / Embedded(FAT32_BOOTSECTOR),
    Padding((this.reserved_sector_count - 2) * this.sector_size),
    # FATs
    "fats" / Array(this.fat_count, Bytes(this.sectors_per_fat * this.sector_size)),
    )


class FAT:
    """
    Abstract base class of a FAT filesystem.
    """
    def __init__(self, stream: typ.BinaryIO, predataregion: Struct):
        """
        :param stream: filedescriptor of a FAT filesystem
        :param predataregion: Struct that represents the PreDataRegion
                              of the concrete FAT filesystem
        """
        self.stream = stream
        self.offset = stream.tell()
        self.predataregion_definition = predataregion
        self.pre = predataregion.parse_stream(stream)
        self.start_dataregion = stream.tell()
        self._fat_entry = None
        self.entries_per_fat = None

    def get_cluster_value(self, cluster_id: int) -> None:
        """
        finds the value that is written into fat
        for given cluster_id
        :param cluster_id: int, cluster that will be looked up
        :return: int or string
        """
        raise NotImplementedError()

    def write_fat_entry(self, cluster_id: int,
                        value: typ.Union[int, str]) -> None:
        """
        write a given value into FAT tables
        requires that FAT object holds self._fat_entry attribute with
        a valid construct.Mapping
        :param cluster_id: int, cluster_id to write the value into
        :param value: int or string, value that gets written into FAT
                      use integer for valid following cluster_ids
                      use string 'free_cluster', 'bad_cluster' or
                      'last_cluster' without need to distinguish between
                      different FAT versions.
        :raises: AttributeError, AssertionError, FieldError
        """
        # make sure cluster_id is valid
        if cluster_id < 0 or cluster_id >= self.entries_per_fat:
            raise AttributeError("cluster_id out of bounds")
        # make sure user does not input invalid values as next cluster
        if isinstance(value, int):
            assert value < self._fat_entry.encoding['bad_cluster'], \
                            "next_cluster value must be < " \
                            + str(self._fat_entry.encoding['bad_cluster']) \
                            + ". For last cluster use 'last_cluster'. For " \
                            + "bad_cluster use 'bad_cluster'"
            assert value >= 2, "next_cluster value must be >= 2. For " \
                               + "free_cluster use 'free_cluster'"
        # get start position of FAT0
        fat0_start = self.offset + 512 + (self.pre.sector_size - 512) + \
            (self.pre.reserved_sector_count - 1) * self.pre.sector_size
        fat1_start = fat0_start + self.pre.sectors_per_fat \
            * self.pre.sector_size
        # update first fat on disk
        self.stream.seek(fat0_start + cluster_id
                         * self._fat_entry.sizeof())
        self.stream.write(self._fat_entry.build(value))
        # update second fat on disk if it exists
        if self.pre.fat_count > 1:
            self.stream.seek(fat1_start + cluster_id
                             * self._fat_entry.sizeof())
            self.stream.write(self._fat_entry.build(value))
        # flush changes to disk
        self.stream.flush()
        # re-read fats into memory
        fat_definition = Array(self.pre.fat_count,
                               Bytes(self.pre.sectors_per_fat *
                                     self.pre.sector_size))
        self.stream.seek(fat0_start)
        self.pre.fats = fat_definition.parse_stream(self.stream)

    def get_free_cluster(self) -> int:
        """
        searches for the next free (unallocated cluster) in fat
        :return: int, the cluster_id of an unallocated cluster
        """
        # FAT32 FS_Info sector stores the last allocated cluster
        # so lets use it as an entry point, otherwise use cluster_id 3
        # (as 0 and 1 are reserved cluster and it seems uncommon to assign
        # cluster 2)
        if hasattr(self.pre, "last_allocated_data_cluster"):
            start_id = self.pre.last_allocated_data_cluster
        else:
            start_id = 3

        current_id = start_id
        while current_id != start_id - 1:
            if current_id < 2:
                # skip cluster 0 and 1
                current_id += 1
                continue
            # check if current_id is free. Return if it is
            if self.get_cluster_value(current_id) == 'free_cluster':
                return current_id
            # If current_id is not allocated, increment it and wrap
            # around the maximum count of entries as with FAT32 we
            # might start in the middle of FAT and want to examine
            # previous entries first until we throw an error
            current_id = (current_id + 1) % (self.entries_per_fat - 1)
        raise NoFreeClusterAvailable()

    def follow_cluster(self, start_cluster: int) -> typ.List[int]:
        """
        collect all cluster, that belong to a file
        :param start_cluster: cluster to start with
        :return: list of cluster numbers (int)
        """
        clusters = [start_cluster]
        while True:
            next_cluster_id = clusters[-1]
            next_cluster = self.get_cluster_value(next_cluster_id)
            if next_cluster == 'last_cluster':
                return clusters
            elif next_cluster == 'free_cluster':
                raise Exception("Cluster %d is a free cluster"
                                % next_cluster_id)
            elif next_cluster == 'bad_cluster':
                raise Exception("Cluster %d is a bad cluster"
                                % next_cluster_id)
            else:
                clusters.append(next_cluster)

    def get_cluster_start(self, cluster_id: int) -> int:
        """
        calculates the start byte of a given cluster_id
        :param cluster_id: id of the cluster
        :return: int, start byte of the given cluster_id
        """
        # offset of requested cluster to the start of dataregion in bytes
        cluster_offset = (cluster_id - 2) \
            * self.pre.sectors_per_cluster \
            * self.pre.sector_size
        # offset of requested cluster to the start of the stream
        cluster_start = self.start_dataregion + cluster_offset
        return cluster_start

    def file_to_stream(self, start_cluster_id: int,
                       stream: typ.BinaryIO) -> None:
        """
        writes all clusters of a file into a given stream
        :param start_cluster_id: int, cluster_id of the start cluster
        :param stream: stream, the file will written into
        """
        for cluster_id in self.follow_cluster(start_cluster_id):
            self.cluster_to_stream(cluster_id, stream)

    def cluster_to_stream(self, cluster_id: int, stream: typ.BinaryIO,
                          length: int =None) -> None:
        """
        writes a cluster to a given stream
        :param cluster_id: int, cluster_id of the cluster
                           that will be written to stream
        :param stream: stream, the cluster will written into
        :param length: int, length of the written cluster.
                       Default: cluster size
        """
        if length is None:
            length = self.pre.sectors_per_cluster * self.pre.sector_size
        start = self.get_cluster_start(cluster_id)

        self.stream.seek(start)
        while length > 0:
            read = self.stream.read(length)
            if len(read) == 0:
                logger.warning("failed to read %s bytes at %s",
                               length, self.stream.tell())
                raise EOFError()
            length -= len(read)
            stream.write(read)

    def _root_to_stream(self, stream: typ.BinaryIO) -> None:
        """
        write root directory into a given stream
        only aplicable to FAT12 and FAT16
        :param stream: stream, where the root directory will be written into
        """
        raise NotImplementedError

    def get_root_dir_entries(self) \
            -> typ.Generator[typ.Tuple[Struct, str], None, None]:
        """
        iterator for reading the root directory
        """
        for dir_entry, lfn in self._get_dir_entries(0):
            yield (dir_entry, lfn)

    def get_dir_entries(self, cluster_id: int) \
            -> typ.Generator[typ.Tuple[Struct, str], None, None]:
        """
        iterator for reading a cluster as directory and parse its content
        :param cluster_id: int, cluster to parse
        :return: tuple of (DIR_ENTRY, lfn)
        :raises: IOError
        """
        try:
            for dir_entry, lfn in self._get_dir_entries(cluster_id):
                yield (dir_entry, lfn)
        except IOError:
            logger.warning("failed to read directory entries at %s", cluster_id)

    def _get_dir_entries(self, cluster_id: int) \
            -> typ.Generator[typ.Tuple[Struct, str], None, None]:
        """
        iterator for reading a cluster as directory and parse its content
        :param cluster_id: int, cluster to parse,
                           if cluster_id == 0, parse rootdir
        :return: tuple of (DIR_ENTRY, lfn)
        """
        lfn = ''
        with BytesIO() as mem:
            # create an IO stream, to write the directory in it
            if cluster_id == 0:
                # write root dir into stream if cluster_id is 0
                self._root_to_stream(mem)
            else:
                # if cluster_id is != 0, write cluster into stream
                self.file_to_stream(cluster_id, mem)
            mem.seek(0)
            with BufferedReader(mem) as reader:
                while reader.peek(1):
                    # read 32 bit into variable
                    raw = reader.read(32)
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
                        # add start_cluster attribute for convenience
                        dir_entry.start_cluster = int.from_bytes(dir_entry.firstCluster,
                                                                 byteorder='little')
                        yield (dir_entry, retlfn)


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
