import logging
import typing as typ
from os import path
from fishy.filesystem_detector import get_filesystem_type
from fishy.metadata import Metadata
from fishy.APFS.Inode_Padding import APFSInodePadding
from fishy.APFS.Inode_Padding import APFSInodePaddingMetadata

LOGGER = logging.getLogger("write_gen")

class inodePadding:

    def __init__(self, fs_stream: typ.BinaryIO, metadata: Metadata, dev: str = None):
        self.dev = dev
        self.metadata = metadata
        self.fs_type = get_filesystem_type(fs_stream)
        if self.fs_type == 'APFS':
            self.metadata.set_module("APFS-Inode-Padding")
            self.fs = APFSInodePadding(fs_stream)  # pylint: disable=invalid-name
        else:
            raise NotImplementedError()

    def write(self, instream: typ.BinaryIO,
              filename: str = None) -> None:
        LOGGER.info("Write")
        if filename is not None:
            filename = path.basename(filename)
        if self.fs_type == 'APFS':
            LOGGER.info("Write into APFS")
            inode_padding_metadata = self.fs.write(instream)
            self.metadata.add_file(filename, inode_padding_metadata)
        else:
            raise NotImplementedError()

    def read(self, outstream: typ.BinaryIO):
        file_metadata = self.metadata.get_file("0")['metadata']
        if self.fs_type == 'APFS':
            inode_padding_metadata = APFSInodePaddingMetadata(file_metadata)
            self.fs.read(outstream, inode_padding_metadata)
        else:
            raise NotImplementedError()

    def read_into_file(self, outfilepath: str):
        if self.fs_type == 'APFS':
            with open(outfilepath, 'wb+') as outfile:
                self.read(outfile)
        else:
            raise NotImplementedError()

    def clear(self):
        if self.fs_type == 'APFS':
            for file_entry in self.metadata.get_files():
                file_metadata = file_entry['metadata']
                file_metadata = APFSInodePaddingMetadata(file_metadata)
                self.fs.clear(file_metadata)
        else:
            raise NotImplementedError()
