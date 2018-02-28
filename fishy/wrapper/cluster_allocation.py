"""
ClusterAllocator wrapper for filesystem specific implementations
"""
import logging
import typing as typ
from os import path
from ..ntfs.cluster_allocator import ClusterAllocator as NTFSAllocator
from ..ntfs.cluster_allocator import AllocatorMetadata as NTFSAllocatorMeta
from ..fat.cluster_allocator import ClusterAllocator as FATAllocator
from ..fat.cluster_allocator import AllocatorMetadata as FATAllocatorMeta
from ..filesystem_detector import get_filesystem_type
from ..metadata import Metadata

LOGGER = logging.getLogger("ClusterAllocation")

class ClusterAllocation:
    """
    This class wrapps the filesystem specific file cluster allocation
    implementations

    usage examples:

    >>> f = open('/dev/sdb1', 'rb+')
    >>> fs = ClusterAllocation(f)
    >>> m = Metadata("FileSlack")
    >>> filename = 'path/to/file/on/fs'

    to write something from stdin into slack:
    >>> fs.write(sys.stdin.buffer, m, filename)

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
            self.metadata.set_module("fat-cluster-allocator")
            self.fs = FATAllocator(fs_stream)  # pylint: disable=invalid-name
        elif self.fs_type == 'NTFS':
            self.metadata.set_module("ntfs-cluster-allocator")
            self.fs = NTFSAllocator(fs_stream)  # pylint: disable=invalid-name
        else:
            raise NotImplementedError()

    def write(self, instream: typ.BinaryIO, filepath: str,
              filename: str = None) -> None:
        """
        writes data from instream into additional allocated clusters of given
        file. Metadata of this file will be stored in Metadata object

        :param instream: stream to read data from
        :param filepath: string, path to file, for which additional clusters
                          will be allocated to hide data in
        :param filename: name that will be used, when file gets written into a
                         directory (while reading fileslack). if none, a random
                         name will be generated
        :raises: IOError
        """
        if filename is not None:
            filename = path.basename(filename)
        if self.fs_type == 'FAT':
            allocator_metadata = self.fs.write(instream, filepath)
            self.metadata.add_file(filename, allocator_metadata)
        elif self.fs_type == 'NTFS':
            allocator_metadata = self.fs.write(instream, filepath)
            self.metadata.add_file(filename, allocator_metadata)
        else:
            raise NotImplementedError()

    def read(self, outstream: typ.BinaryIO):
        """
        writes hidden data from slackspace into stream. The examined slack
        space information is taken from metadata.

        :param outstream: stream to write hidden data into
        :raises: IOError
        """
        file_metadata = self.metadata.get_file("0")['metadata']
        if self.fs_type == 'FAT':
            allocator_metadata = FATAllocatorMeta(file_metadata)
            self.fs.read(outstream, allocator_metadata)
        elif self.fs_type == 'NTFS':
            allocator_metadata = NTFSAllocatorMeta(file_metadata)
            self.fs.read(outstream, allocator_metadata)
        else:
            raise NotImplementedError()

    def read_into_file(self, outfilepath: str):
        """
        reads hidden data from slack into files
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
        clears the slackspace of files. Information of them is stored in
        metadata.
        :param metadata: Metadata, object where metadata is stored in
        :raises: IOError
        """
        if self.fs_type == 'FAT':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = FATAllocatorMeta(file_metadata)
                self.fs.clear(file_metadata)
        elif self.fs_type == 'NTFS':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = NTFSAllocatorMeta(file_metadata)
                self.fs.clear(file_metadata)
        else:
            raise NotImplementedError()
