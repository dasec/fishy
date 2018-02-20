"""
FileSlack os a wrapper for filesystem specific file slack implementations
"""
import logging
import typing as typ
from os import path
from .fat.fat_filesystem.dir_entry import DirEntry
from .fat.file_slack import FileSlack as FATFileSlack
from .fat.file_slack import FileSlackMetadata as FATFileSlackMetadata
from .filesystem_detector import get_filesystem_type
from .metadata import Metadata
from .ntfs.ntfs_file_slack import NtfsSlack as NTFSFileSlack
from .ntfs.ntfs_file_slack import FileSlackMetadata as NTFSFileSlackMetadata

LOGGER = logging.getLogger("FileSlack")

class FileSlack:
    """
    This class wrapps the filesystem specific file slack implementations

    usage examples:

    >>> f = open('/dev/sdb1', 'rb+')
    >>> fs = FileSlack(f)
    >>> m = Metadata("FileSlack")
    >>> filenames = [ 'path/to/file/on/fs' ]

    to write something from stdin into slack:
    >>> fs.write(sys.stdin.buffer, m, filenames)

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
            self.metadata.set_module("fat-file-slack")
            self.fs = FATFileSlack(fs_stream)  # pylint: disable=invalid-name
        elif self.fs_type == 'NTFS':
            self.fs = NTFSFileSlack(dev, fs_stream)
            self.metadata.set_module("ntfs-slack")
        else:
            raise NotImplementedError()

    def write(self, instream: typ.BinaryIO, filepaths: typ.List[str],
              filename: str = None) -> None:
        """
        writes data from instream into slackspace of filepaths. Metadata of
        those files will be stored in Metadata object

        :param instream: stream to read data from
        :param filepaths: list of strings, paths to files, which slackspace
                          will be used to store data
        :param filename: name that will be used, when file gets written into a
                         directory (while reading fileslack). if none, a random
                         name will be generated
        :raises: IOError
        """
        LOGGER.info("Write")
        if filename is not None:
            filename = path.basename(filename)
        if self.fs_type == 'FAT':
            slack_metadata = self.fs.write(instream, filepaths)
            self.metadata.add_file(filename, slack_metadata)
        elif self.fs_type == 'NTFS':
            LOGGER.info("Write into ntfs")
            slack_metadata = self.fs.write(instream, filepaths)
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
        if self.fs_type == 'FAT':
            slack_metadata = FATFileSlackMetadata(file_metadata)
            self.fs.read(outstream, slack_metadata)
        elif self.fs_type == 'NTFS':
            slack_metadata = NTFSFileSlackMetadata(file_metadata)
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
        if self.fs_type == 'FAT' or self.fs_type == 'NTFS':
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
                file_metadata = FATFileSlackMetadata(file_metadata)
                self.fs.clear(file_metadata)
        elif self.fs_type == 'NTFS':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = NTFSFileSlackMetadata(file_metadata)
                self.fs.clear(file_metadata)
        else:
            raise NotImplementedError()

    def _print_file_info(self, dir_entry: DirEntry) -> None:
        """
        prints info about available file slack of a given file
        :param dir_entry: directory entry of a file, for which the info will
                          be printed
        """
        occp, rams, files = self.fs.calculate_slack_space(dir_entry)
        print("File:", dir_entry.get_name())
        print("  Occupied in last cluster:", occp)
        print("  Ram Slack:", rams)
        print("  File Slack:", files)


    def info(self, filepaths: typ.List[str]) -> None:
        """
        prints info about available file slack of files
        """
        if self.fs_type == 'FAT':
            for filepath in filepaths:
                dir_entry = self.fs.fatfs.find_file(filepath)
                if dir_entry.is_dir():
                    for entry in self.fs._file_walk(dir_entry):
                        self._print_file_info(entry)
                else:
                    self._print_file_info(dir_entry)
        elif self.fs_type == 'NTFS':
            self.fs.print_info(filepaths)
        else:
            raise NotImplementedError()
