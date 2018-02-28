"""
MftSlack a wrapper to comply with README - How to implement a hiding technique
"""
import logging
import typing as typ
from os import path
from ..filesystem_detector import get_filesystem_type
from ..metadata import Metadata
from ..ntfs.ntfs_mft_slack import NtfsMftSlack as NTFSMftSlack
from ..ntfs.ntfs_mft_slack import MftSlackMetadata as NTFSMftSlackMetadata

LOGGER = logging.getLogger("MftSlack")

class MftSlack:
    """
    This class wrapps the mft slack implementations

    usage examples:

    >>> f = open('/dev/sdb1', 'rb+')
    >>> ms = MftSlack(f)
    >>> m = Metadata("MftSlack")

    to write something from stdin into slack:
    >>> fs.write(sys.stdin.buffer, m)

    to write something from stdin into slack with offset:
    >>> fs.write(sys.stdin.buffer, m, 36)

    to read something from slack to stdout:
    >>> fs.read(sys.stdout.buffer, m)

    to wipe slackspace via metadata file:
    >>> fs.clear_with_metadata(m)
    """
    def __init__(self, fs_stream: typ.BinaryIO, metadata: Metadata,
                 dev: str = None, domirr = False):
        """
        :param fs_stream: Stream of filesystem
        :param metadata: Metadata object
        :param dev: device to use
        :param domirr: write copy of data to $MFTMirr
        """
        self.dev = dev
        self.metadata = metadata
        self.fs_type = get_filesystem_type(fs_stream)
        if self.fs_type == 'NTFS':
            self.fs = NTFSMftSlack(dev, fs_stream)
            self.fs.domirr = domirr
            self.metadata.set_module("ntfs-mft-slack")
        else:
            raise NotImplementedError()

    def write(self, instream: typ.BinaryIO, filename: str=None, offset=0) -> None:
        """
        writes data from instream into slackspace of mft entires starting at the offset.
        Metadata of those files will be stored in Metadata object

        :param instream: stream to read data from
        :param filename: name that will be used, when file gets written into a
                         directory (while reading fileslack). if none, a random
                         name will be generated
        :param offset: first sector of mft entry to start with
        :raises: IOError
        """
        LOGGER.info("Write")
        if filename is not None:
            filename = path.basename(filename)
        if self.fs_type == 'NTFS':
            slack_metadata = self.fs.write(instream, offset)
            self.metadata.add_file(filename, slack_metadata)
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
        if self.fs_type == 'NTFS':
            slack_metadata = NTFSMftSlackMetadata(file_metadata)
            self.fs.read(outstream, slack_metadata)
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
        if self.fs_type == 'NTFS':
            with open(outfilepath, 'wb+') as outfile:
                self.read(outfile)
        else:
            raise NotImplementedError()

    def clear(self):
        """
        clears the slackspace of mft entires. Information of them is stored in
        metadata.
        :param metadata: Metadata, object where metadata is stored in
        :raises: IOError
        """
        if self.fs_type == 'NTFS':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = NTFSMftSlackMetadata(file_metadata)
                self.fs.clear(file_metadata)
        else:
            raise NotImplementedError()

    def info(self, offset=0, limit=-1) -> None:
        """
        prints info about available file slack of mft entries

        :param offset: First sector of mft entry to start with.
        :param limit: Amount of mft entries to display info for. Unlimited if -1.
        """
        if self.fs_type == 'NTFS':
            self.fs.print_info(offset, limit)
        else:
            raise NotImplementedError()
