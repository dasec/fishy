"""
This module implements additional cluster allocation to hide data in FAT
filesystems.
"""

import logging
import typing as typ
from io import BytesIO, BufferedReader
from .fat_filesystem.fat import NoFreeClusterAvailable
from .fat_filesystem.fat_32 import FAT32
from .fat_filesystem.fat_detector import get_filesystem_type
from .fat_filesystem.fat_wrapper import create_fat


LOGGER = logging.getLogger("FATClusterAllocator")


class AllocatorMetadata:
    """
    Metadata class for additional cluster allocator
    """
    def __init__(self, d: typ.Dict = None):
        if d:
            self.start_cluster = d['start_cluster']
            self.length = d['length']
            self.original_last_cluster = d['original_last_cluster']
        else:
            self.start_cluster = None
            self.length = None
            self.original_last_cluster = None

    def set_start_cluster(self, start_cluster: int) -> None:
        """
        set the start cluster id
        :param start_cluster: int, start cluster of the hidden data
        """
        self.start_cluster = start_cluster

    def get_start_cluster(self) -> int:
        """
        get start cluster id
        :rtype: int
        """
        return self.start_cluster

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

    def get_original_last_cluster(self) -> int:
        """
        get the original last cluster of the file, for which addinional
        clusters were allocated
        :return: int, cluster_id of the last cluster
        """
        return self.original_last_cluster

    def set_original_last_cluster(self, cluster_id: int) -> None:
        """
        set the original last cluster of the file, for which addinional
        clusters were allocated
        :param cluster_id: int, id of the original last cluster
        """
        self.original_last_cluster = cluster_id


class ClusterAllocator:
    """
    Provides methods to hide and restore data from additional clusters
    allocated for a file
    """
    def __init__(self, stream: typ.BinaryIO):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.fat_type = get_filesystem_type(stream)
        self.fatfs = create_fat(stream)
        self.stream = stream

    def write(self, instream: typ.BinaryIO, filepath: str) \
            -> AllocatorMetadata:
        """
        writes from instream into slackspace of filename
        :param instream: stream to read from
        :param filepath: string, path to file, for which additional clusters
                          will be allocated
        :return: AllocatorMetadata
        """
        metadata = AllocatorMetadata()
        # get last cluster of the file we want to use
        file_entry = self.fatfs.find_file(filepath)
        assert not file_entry.attributes.subDirectory, \
            "Can't allocate additional clusters for a directory"
        assert not file_entry.start_cluster < 2, \
            "File has no clusters allocated"
        last_cluster = self.fatfs.follow_cluster(file_entry.start_cluster).pop()
        metadata.set_original_last_cluster(last_cluster)
        LOGGER.info("last cluster of file '%s' is cluster_id %d", filepath,
                    last_cluster)
        cluster_count = 0
        written_length = 0
        LOGGER.info("%d Bytes in buffer to write", len(instream.peek()))
        while instream.peek():
            try:
                # get next cluster to write into
                next_cluster = self.fatfs.get_free_cluster()
                LOGGER.info("Got cluster %d as next cluster to write into",
                            next_cluster)
            except NoFreeClusterAvailable:
                raise NoFreeClusterAvailable
            # allocate this cluster in FAT
            self.fatfs.write_fat_entry(last_cluster, next_cluster)
            cluster_count += 1
            # terminate cluster chain, to be able to get new clusters
            self.fatfs.write_fat_entry(next_cluster, 'last_cluster')
            # record this cluster as the start_cluster of hidden data
            if metadata.get_start_cluster() is None:
                metadata.set_start_cluster(next_cluster)
            # write to cluster
            written_bytes = self._write_to_cluster(instream, next_cluster)
            written_length += written_bytes
            LOGGER.info("%d bytes written into cluster %d",
                        written_bytes, next_cluster)
            last_cluster = next_cluster
        # write overall length into metadata
        metadata.set_length(written_length)
        # finish fat chain
        LOGGER.info("Finishing cluster chain on cluster %d", last_cluster)
        self.fatfs.write_fat_entry(last_cluster, 'last_cluster')
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
        # that fits into slack
        bufferv = instream.read(cluster_size)
        LOGGER.info("%d bytes read from instream", len(bufferv))
        # find position where we can start writing data
        cluster_start = self.fatfs.get_cluster_start(cluster_id)
        self.stream.seek(cluster_start)
        # write bytes into stream
        bytes_written = self.stream.write(bufferv)
        return bytes_written

    def read(self, outstream: typ.BinaryIO, metadata: AllocatorMetadata) \
            -> None:
        """
        writes slackspace of files into outstream
        :param outstream: stream to write into
        :param metadata: AllocatorMetadata object
        """
        # calculate size of a cluster
        cluster_size = self.fatfs.pre.sector_size \
                       * self.fatfs.pre.sectors_per_cluster
        # get metadata
        start_cluster = metadata.get_start_cluster()
        length = metadata.get_length()
        LOGGER.info("Content length to read: %d bytes, starting on cluster %d",
                    length, start_cluster)
        # put content of each cluster into stream
        LOGGER.info("Found %d cluster in chain to read from",
                    len(self.fatfs.follow_cluster(start_cluster)))
        for cluster_id in self.fatfs.follow_cluster(start_cluster):
            if length > cluster_size:
                length_to_read = cluster_size
                length -= cluster_size
            else:
                length_to_read = length
            LOGGER.info("reading %d bytes from cluster", length_to_read)
            self.fatfs.cluster_to_stream(cluster_id, outstream, length_to_read)

    def clear(self, metadata: AllocatorMetadata) -> None:
        """
        clears the additional allocated clusters from a file
        :param metadata: AllocatorMetadata object
        """
        # calculate size of a cluster
        cluster_size = self.fatfs.pre.sector_size \
                       * self.fatfs.pre.sectors_per_cluster
        # get metadata
        start_cluster = metadata.get_start_cluster()
        orig_last_cluster = metadata.get_original_last_cluster()
        clusters = self.fatfs.follow_cluster(start_cluster)
        # set original last cluster for file
        self.fatfs.write_fat_entry(orig_last_cluster, 'last_cluster')
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
