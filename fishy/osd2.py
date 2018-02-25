"""
Wrapper for filesystem specific implementations of hiding data inside reserved GDT blocks
"""
import logging
import typing as typ
from os import path
from fishy.filesystem_detector import get_filesystem_type
from fishy.metadata import Metadata
from fishy.ext4.osd2 import EXT4OSD2
from fishy.ext4.osd2 import EXT4OSD2Metadata

LOGGER = logging.getLogger("ReservedGDTBlocks")

class OSD2:
    """
    This class wraps the filesystem specific implementation of the osd2 hiding technique
    """
    def __init__(self, fs_stream: typ.BinaryIO, metadata: Metadata,
                 dev: str = None):
        """
        :param dev: Path to filesystem
        :param fs_stream: Stream of filesystem
        :param metadata: Metadata object
        """
        self.dev = dev
        self.metadata = metadata
        self.fs_type = get_filesystem_type(fs_stream)
        if self.fs_type == 'EXT4':
            self.metadata.set_module("ext4-osd2")
            self.fs = EXT4OSD2(fs_stream, dev)  # pylint: disable=invalid-name
        else:
            raise NotImplementedError()

    def write(self, instream: typ.BinaryIO,
              filename: str = None) -> None:
        """
        writes data from instream into inodes' osd2 field. Metadata of
        those files will be stored in Metadata object

        :param instream: stream to read data from
        :param filename: name that will be used, when file gets written into inodes' osd2 field.
                         If none, a random name will be generated.
        :raises: IOError
        """
        LOGGER.info("Write")
        if filename is not None:
            filename = path.basename(filename)
        if self.fs_type == 'EXT4':
            LOGGER.info("Write into ext4")
            osd2_metadata = self.fs.write(instream)
            self.metadata.add_file(filename, osd2_metadata)
        else:
            raise NotImplementedError()

    def read(self, outstream: typ.BinaryIO):
        """
        writes hidden data from inodes' osd2 field into stream.

        :param outstream: stream to write hidden data into osd2 fields
        :raises: IOError
        """
        file_metadata = self.metadata.get_file("0")['metadata']
        if self.fs_type == 'EXT4':
            osd2_metadata = EXT4OSD2Metadata(file_metadata)
            self.fs.read(outstream, osd2_metadata)
        else:
            raise NotImplementedError()

    def read_into_file(self, outfilepath: str):
        """
        reads hidden data from inodes' osd2 field into files
        :note: If provided filepath already exists, this file will be
               overwritten without a warning.
        :param outfilepath: filepath to file, where hidden data will be
                            restored into
        """
        if self.fs_type == 'EXT4':
            with open(outfilepath, 'wb+') as outfile:
                self.read(outfile)
        else:
            raise NotImplementedError()

    def clear(self):
        """
        clears inodes' osd2 field in which data has been hidden
        :param metadata: Metadata, object where metadata is stored in
        :raises: IOError
        """
        if self.fs_type == 'EXT4':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = EXT4OSD2Metadata(file_metadata)
                self.fs.clear(file_metadata)
        else:
            raise NotImplementedError()

    def info(self):
        """
        shows info about inode osd2 fields and data hiding space
        :param metadata: Metadata, object where metadata is stored in
        :raises: IOError
        """
        if self.fs_type == 'EXT4':
            if len(self.metadata.get_files()) >= 0:
                for file_entry in self.metadata.get_files():
                    file_metadata = file_entry['metadata']
                    file_metadata = EXT4OSD2Metadata(file_metadata)
                    self.fs.info(file_metadata)
            else:
                self.fs.info()
        else:
            raise NotImplementedError()
