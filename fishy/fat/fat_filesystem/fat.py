"""
Abstract base class for FAT12, FAT16 and FAT32 reader
"""

import logging
import typing as typ
from abc import ABCMeta, abstractmethod
from io import BytesIO, BufferedReader
from construct import Struct, Array, Bytes
from .dir_entry import DirEntry, LFNEntries


LOGGER = logging.getLogger("FATFilesystem")


class NoFreeClusterAvailableError(Exception):
    """
    This exception can be thrown by the get_free_cluster method of a FAT
    instance.
    """
    pass


class FAT:  # pylint: disable=too-many-instance-attributes
    """
    Abstract base class of all FAT filesystem types.
    """
    __metaclass__ = ABCMeta
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
        self.fat_type = None

    @abstractmethod
    def get_cluster_value(self, cluster_id: int) -> int:
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
            # check if last_allocated_data_cluster is a valid cluster number
            # otherwise use default value
            if start_id > self._fat_entry.encoding['bad_cluster'] \
                    or start_id < 2:
                start_id = 3
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
        raise NoFreeClusterAvailableError()

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
                          length: int = None) -> None:
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
            if not read:
                LOGGER.warning("failed to read %s bytes at %s",
                               length, self.stream.tell())
                raise EOFError()
            length -= len(read)
            stream.write(read)

    @abstractmethod
    def _root_to_stream(self, stream: typ.BinaryIO) -> None:
        """
        write root directory into a given stream

        only aplicable to FAT12 and FAT16
        :param stream: stream, where the root directory will be written into
        """
        raise NotImplementedError

    def get_root_dir_entries(self) \
            -> typ.Generator[DirEntry, None, None]:
        """
        iterator for reading the root directory
        """
        yield from self._get_dir_entries(0)

    def get_dir_entries(self, cluster_id: int) \
            -> typ.Generator[DirEntry, None, None]:
        """
        iterator for reading a cluster as directory and parse its content

        :param cluster_id: int, cluster to parse
        :return: generator for DirEntry
        :raises: IOError
        """
        try:
            yield from self._get_dir_entries(cluster_id)
        except IOError:
            LOGGER.warning("failed to read directory entries at %s",
                           cluster_id)

    def _get_dir_entries(self, cluster_id: int) \
            -> DirEntry:
        """
        generator for reading a cluster as directory and parse its content

        :param cluster_id: int, cluster to parse,
                           if cluster_id == 0, parse rootdir
        :return: DirEntry
        """
        lfn_entries = LFNEntries()
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
                    # stop if we read less than 32 byte
                    if len(raw) < 32:
                        raise StopIteration()
                    # parse as DirEntry
                    dir_entry = DirEntry(raw, self.fat_type)
                    # If dir entry is completely empty, skip it
                    if dir_entry.is_empty():
                        continue
                    # If it is a lfn entry, store it for later assignment to
                    # its physical entry
                    if dir_entry.is_lfn():
                        lfn_entries.append(dir_entry)
                    else:
                        dir_entry.lfn_name = lfn_entries.get_name()
                        lfn_entries.clear()
                        yield dir_entry

    def find_file(self, filepath: str) -> DirEntry:
        """
        returns the directory entry for a given filepath

        :param filepath: string, filepath to the file
        :return: DirEntry of the requested file
        """
        # build up filepath as directory and
        # reverse it so, that we can simple
        # pop all filepath parts from it
        path = filepath.split('/')
        path = list(reversed(path))
        # read root directory and append all file entries
        current_directory = []
        for entry in self.get_root_dir_entries():
            current_directory.append(entry)  # pylint: disable=bad-whitespace

        while path:
            fpart = path.pop()

            # scan current directory for filename
            filename_found = False
            for entry in current_directory:
                LOGGER.info("find_file: comparing '%s' with '%s'",
                            entry.get_name(), fpart)
                if entry.get_name() == fpart:
                    filename_found = True
                    break
            if not filename_found:
                raise Exception("File or directory '%s' not found" % fpart)

            # if it is a subdirectory and not the last name, enter it
            if entry.is_dir() and path:
                current_directory.clear()
                for entry in self.get_dir_entries(entry.get_start_cluster()):
                    current_directory.append(entry)  # pylint: disable=bad-whitespace
        return entry
