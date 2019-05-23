"""
BadCluster wrapper for filesystem specific implementations
"""
import logging
import typing as typ
from os import path
from ..fat.bad_cluster import BadCluster as FATBadCluster
from ..fat.bad_cluster import BadClusterMetadata as FATBadClusterMetadata
from ..ntfs.bad_cluster import NtfsBadCluster as NTFSBadCluster
from ..ntfs.bad_cluster import BadClusterMetadata as NTFSBadClusterMetadata
from ..filesystem_detector import get_filesystem_type
from ..metadata import Metadata

LOGGER = logging.getLogger("ClusterAllocation")

class BadClusterWrapper:
    """
    This class wrapps the filesystem specific file cluster allocation
    implementations

    usage examples:

    >>> f = open('/dev/sdb1', 'rb+')
    >>> fs = BadClusterWrapper(f)
    >>> m = Metadata("BadCluster")

    to write something from stdin into slack:
    >>> fs.write(sys.stdin.buffer, m)

    to read something from slack to stdout:
    >>> fs.read(sys.stdout.buffer, m)

    to wipe slackspace via metadata file:
    >>> fs.clear_with_metadata(m)
    """
    def __init__(self, fs_stream: typ.BinaryIO, metadata: Metadata,
                 dev: str = None):
        """
        :param fs_stream: Stream of filesystem
        :param metadata: Metadata object
        """
        self.dev = dev
        self.metadata = metadata
        self.fs_type = get_filesystem_type(fs_stream)
        if self.fs_type == 'FAT':
            self.metadata.set_module("fat-bad-cluster")
            self.fs = FATBadCluster(fs_stream)  # pylint: disable=invalid-name
        elif self.fs_type == 'NTFS':
            self.metadata.set_module("ntfs-bad-cluster")
            #self.fs = NTFSBadCluster(dev)
            self.fs = NTFSBadCluster(dev, fs_stream)
        else:
            raise NotImplementedError()

    def write(self, instream: typ.BinaryIO, filename: str = None) -> None:
        """
        writes data from instream into bad cluster.
        Metadata of this file will be stored in Metadata object

        :param instream: stream to read data from
        :param filename: name that will be used, when file gets written into a
                         directory (while reading bad clusters). if none, a
                         random name will be generated
        :raises: IOError
        """
        if filename is not None:
            filename = path.basename(filename)
        if self.fs_type == 'FAT':
            bad_cluster_metadata = self.fs.write(instream)
            self.metadata.add_file(filename, bad_cluster_metadata)
        elif self.fs_type == 'NTFS':
            bad_cluster_metadata = self.fs.write(instream)
            self.metadata.add_file(filename, bad_cluster_metadata)
        else:
            raise NotImplementedError()

    def read(self, outstream: typ.BinaryIO):
        """
        writes hidden data from bad clusters into stream.

        :param outstream: stream to write hidden data into
        :raises: IOError
        """
        file_metadata = self.metadata.get_file("0")['metadata']
        if self.fs_type == 'FAT':
            bad_cluster_metadata = FATBadClusterMetadata(file_metadata)
            self.fs.read(outstream, bad_cluster_metadata)
        elif self.fs_type == 'NTFS':
            bad_cluster_metadata = NTFSBadClusterMetadata(file_metadata)
            self.fs.read(outstream, bad_cluster_metadata)
        else:
            raise NotImplementedError()

    def read_into_file(self, outfilepath: str):
        """
        reads hidden data from bad clusters into file
        :note: If provided filepath already exists, this file will be
               overwritten without a warning.
        :param outfilepath: filepath to file, where hidden data will be
                            restored into
        """
        if self.fs_type == 'FAT':
            with open(outfilepath, 'wb+') as outfile:
                self.read(outfile)
        elif self.fs_type == 'NTFS':
            with open(outfilepath, 'wb+') as outfile:
                self.read(outfile)
        else:
            raise NotImplementedError()

    def clear(self):
        """
        clears the allocated bad clusters. Information of them is stored in
        metadata.
        :param metadata: Metadata, object where metadata is stored in
        :raises: IOError
        """
        if self.fs_type == 'FAT':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = FATBadClusterMetadata(file_metadata)
                self.fs.clear(file_metadata)
        elif self.fs_type == 'NTFS':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = NTFSBadClusterMetadata(file_metadata)
                self.fs.clear(file_metadata)
        else:
            raise NotImplementedError()
