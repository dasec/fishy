"""
This module implements bad cluster allocation to hide data in FAT
filesystems. It offers methods to read, write and clear the bad clusters
allocated for a file.

:Example:

>>> f = open('/dev/sdb1', 'rb+')
>>> fs = BadCluster(f)

to write something from stdin to bad clusters:

>>> metadata = fs.write(sys.stdin.buffer)

to read something from bad clusters:

>>> fs.read(sys.stdout.buffer, metadata)

delete bad clusters for a file:

>>> fs.clear(metadata)
"""

import logging
import typing as typ
from io import BytesIO, BufferedReader
from .fat_filesystem.fat import NoFreeClusterAvailableError
from .fat_filesystem.fat_32 import FAT32
from .fat_filesystem.fat_detector import get_filesystem_type
from .fat_filesystem.fat_wrapper import create_fat


LOGGER = logging.getLogger("BadCluster")


class BadClusterMetadata:
    """
    Metadata class for bad cluster allocator
    """
    def __init__(self, d: typ.Dict = None):
        if d:
            self.clusters = d['clusters']
            self.length = d['length']
        else:
            self.clusters = []
            self.length = None

    def add_cluster(self, cluster_id) -> None:
        """
        adds a cluster to the list of clusters

        :param cluster_id: int, id of the cluster
        """
        self.clusters.append(cluster_id)

    def get_clusters(self) \
            -> typ.List[int]:
        """
        iterator for clusters

        :returns: iterator, that returns cluster_id
        """
        return self.clusters

    def set_length(self, length: int) -> None:
        """
        set the overall length of written data

        :param length: int, count of bytes written to filesystem
        """
        self.length = length

    def get_length(self) -> int:
        """
        get the length of hidden data

        :rtype: int
        """
        return self.length


class BadCluster:
    """
    Provides methods to hide and restore data from bad clusters
    """
    def __init__(self, stream: typ.BinaryIO):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.fat_type = get_filesystem_type(stream)
        self.fatfs = create_fat(stream)
        self.stream = stream

    def write(self, instream: typ.BinaryIO) \
            -> BadClusterMetadata:
        """
        writes from instream bad clusters

        :param instream: stream to read from

        :return: BadCluster
        """
        metadata = BadClusterMetadata()
        # get last cluster of the file we want to use
        cluster_count = 0
        written_length = 0
        LOGGER.info("%d Bytes in buffer to write", len(instream.peek()))
        while instream.peek():
            try:
                # get next cluster to write into
                next_cluster = self.fatfs.get_free_cluster()
                LOGGER.info("Got cluster %d as next cluster to write into",
                            next_cluster)
            except NoFreeClusterAvailableError:
                self.clear(metadata)
                raise NoFreeClusterAvailableError()
            # allocate this cluster in FAT
            self.fatfs.write_fat_entry(next_cluster, 'bad_cluster')
            cluster_count += 1
            # record this cluster to metadata
            metadata.add_cluster(next_cluster)
            # write to cluster
            written_bytes = self._write_to_cluster(instream, next_cluster)
            written_length += written_bytes
            LOGGER.info("%d bytes written into cluster %d",
                        written_bytes, next_cluster)
            # write overall length into metadata
            metadata.set_length(written_length)
            # save last cluster
            last_cluster = next_cluster
        # clean up fs_info sector, if we write to FAT32
        if isinstance(self.fatfs, FAT32):
            self.fatfs.write_last_allocated(last_cluster)
            old_free_clusters = self.fatfs.pre.free_data_cluster_count
            new_free_clusters = old_free_clusters - cluster_count
            self.fatfs.write_last_allocated(new_free_clusters)
        return metadata

    def _write_to_cluster(self, instream: typ.BinaryIO, cluster_id) \
            -> int:
        """
        writes from instream into cluster
        :param instream: stream to read from
        :param cluster_id: id of the cluster the data gets written into
        :return: tuple of (number of bytes written, cluster_id written to)
        """
        cluster_size = self.fatfs.pre.sector_size \
                       * self.fatfs.pre.sectors_per_cluster
        # read what to write. ensure that we only read the amount of data,
        # that fits into cluster
        bufferv = instream.read(cluster_size)
        LOGGER.info("%d bytes read from instream", len(bufferv))
        # find position where we can start writing data
        cluster_start = self.fatfs.get_cluster_start(cluster_id)
        self.stream.seek(cluster_start)
        # write bytes into stream
        bytes_written = self.stream.write(bufferv)
        return bytes_written

    def read(self, outstream: typ.BinaryIO, metadata: BadClusterMetadata) \
            -> None:
        """
        writes bad clusters into outstream

        :param outstream: stream to write into
        :param metadata: BadClusterMetadata object
        """
        # calculate size of a cluster
        cluster_size = self.fatfs.pre.sector_size \
                       * self.fatfs.pre.sectors_per_cluster
        # get metadata
        length = metadata.get_length()
        LOGGER.info("Content length to read: %d bytes" % length)
        # put content of each cluster into stream
        for cluster_id in metadata.get_clusters():
            if length > cluster_size:
                length_to_read = cluster_size
                length -= cluster_size
            else:
                length_to_read = length
            LOGGER.info("reading %d bytes from cluster", length_to_read)
            self.fatfs.cluster_to_stream(cluster_id, outstream, length_to_read)

    def clear(self, metadata: BadClusterMetadata) -> None:
        """
        clears allocated bad clusters

        :param metadata: BadClusterMetadata object
        """
        # calculate size of a cluster
        cluster_size = self.fatfs.pre.sector_size \
                       * self.fatfs.pre.sectors_per_cluster
        # get metadata
        clusters = metadata.get_clusters()
        # prepare stream with zero bytes to overwrite clusters
        mem = BytesIO()
        mem.write(cluster_size * b'\x00')
        reader = BufferedReader(mem)
        for cluster_id in clusters:
            # overwrite cluster
            mem.seek(0)
            self._write_to_cluster(reader, cluster_id)
            # unlink cluster
            self.fatfs.write_fat_entry(cluster_id, 'free_cluster')
        if isinstance(self.fatfs, FAT32):
            old_free_clusters = self.fatfs.pre.free_data_cluster_count
            new_free_clusters = old_free_clusters + len(clusters)
            self.fatfs.write_free_clusters(new_free_clusters)
