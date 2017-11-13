"""
Directory and Long Filename entries that appear in root and
subdirectories.
"""

import typing as typ
from construct import Struct, Byte, Bytes, BitStruct, Flag, Padding, \
                      Int16ul, Int32ul, Int8ul


# Directory Entry in either the root directory
# or any subdirectory
DIR_ENTRY_DEFINITION = Struct(
    "name" / Bytes(8),
    "extension" / Bytes(3),
    "attributes" / BitStruct(
        "unused" / Flag,
        "device" / Flag,
        "archive" / Flag,
        "subDirectory" / Flag,
        "volumeLabel" / Flag,
        "system" / Flag,
        "hidden" / Flag,
        "readonly" / Flag,
    ),
    Padding(1),
    "deleted_char" / Byte,
    Padding(6),
    "accessRightsBitmap" / Bytes(2),
    "timeRecorded" / Int16ul,
    "dateRecorded" / Int16ul,
    "firstCluster" / Bytes(2),
    "fileSize" / Int32ul,
)

# Directory entry that represents a vFAT entry
# for Long Filenames (LFN)
LFN_ENTRY_DEFINITION = Struct(
    "sequence_number" / Int8ul,
    "name1" / Bytes(10),
    "attributes" / BitStruct(
        "unused" / Flag,
        "device" / Flag,
        "archive" / Flag,
        "subDirectory" / Flag,
        "volumeLabel" / Flag,
        "system" / Flag,
        "hidden" / Flag,
        "readonly" / Flag,
    ),
    "type" / Byte,
    "checksum" / Byte,
    "name2" / Bytes(12),
    "first_cluster" / Bytes(2),
    "name3" / Bytes(4),
    )


class LFNEntries(list):
    """
    List to collect lfn entries
    """
    def get_name(self) -> typ.Union[str, None]:
        """
        get full lfn name
        :return: str, concatinated name of lfn entries
                 None if the list is empty
        """
        # if not len(self):
        #     return None
        sorted_entries = sorted(self, key=lambda x: x.get_sequence_number())
        name = ""
        for entry in sorted_entries:
            name += entry.get_name()
        return name


class DirEntry(object):
    """
    class that represents a FAT directory entry and provides convenient
    access methods for common actions
    """
    def __init__(self, byte_representation: bytearray, fat_type: str):
        """
        :param byte_representation: 32 byte long bytearray of the
                                    directory entry
        :param fat_type: str, opions 'FAT12', 'FAT16', FAT32
        """
        self.is_fat32 = fat_type == 'FAT32'
        self.byte_representation = byte_representation
        self.parsed = DIR_ENTRY_DEFINITION.parse(byte_representation)
        if self.is_lfn():
            self.parsed = LFN_ENTRY_DEFINITION.parse(byte_representation)
        self.lfn_name = None

    def get_sequence_number(self) -> int:
        """
        returns sequence number for lfn entries
        """
        return self.parsed.sequence_number

    def is_empty(self) -> bool:
        """
        checks if this is a valid directory entry
        """
        return self.byte_representation == b'\x00' * 32

    def is_lfn(self) -> bool:
        """
        checks if this entry is a long filename entry
        :rtype: bool
        """
        return self.parsed.attributes.volumeLabel \
                and self.parsed.attributes.system \
                and self.parsed.attributes.hidden \
                and self.parsed.attributes.readonly

    def is_dir(self) -> bool:
        """
        checks if this entry is a directory entry
        :rtype: bool
        """
        return self.parsed.attributes.subDirectory

    def is_file(self) -> bool:
        """
        checks if this entry is a regular file
        :rtype: bool
        """
        return not self.is_dot_entry() \
            and not self.is_dir() \
            and not self.is_lfn()

    def is_dot_entry(self) -> bool:
        """
        checks if this entry is a dot entry
        :rtype: bool
        """
        return self.get_name() == "." or self.get_name() == ".."

    def _reconstruct_name(self) -> bytes:
        """
        reconstructs name field of deleted directory entries
        :return: bytes, representing the original name field
        """
        if not self.is_lfn():
            if self.parsed.name[0] == 0xe5:
                # if this is a deleted entry, replace delete_mark with
                # the original character, saved in deleted_char field
                return self.parsed.deleted_char + self.parsed.name[1:]
            return self.parsed.name
        else:
            raise AttributeError("LFN entry has no name attribute")

    def get_name(self) -> str:
        """
        get the name of this directory entry.
        :return: if this entry is a lfn: return all string information
                 if this entry is a file/directory: return name
        """
        # if this is a lfn entry
        if self.is_lfn():
            lfnpart = self.parsed.name1 + self.parsed.name2 + self.parsed.name3
            # end of string is indicated by \x00\x00
            # following procedure looks for this sequence and removes
            # non-chars after padding
            retlfn = b''
            for i in range(int(len(lfnpart) / 2)):
                i *= 2
                next_bytes = lfnpart[i:i+2]
                if next_bytes != b'\x00\x00':
                    retlfn += next_bytes
                else:
                    break
            return retlfn.decode('utf-16')
        else:
            # if this is a regular directory entry
            if self.lfn_name:
                # if this dir entry has its lfn_name set, return it
                return self.lfn_name
            # if this dir entry has no lfn use its name field
            name = self._reconstruct_name().decode('ascii').rstrip(' ')
            extension = self.parsed.extension.decode('ascii').rstrip(' ')
            if extension != "":
                return name + "." + extension
            return name

    def get_start_cluster(self) -> int:
        """
        get start cluster for this directory entry
        :return: int, start cluster_id of this directory entry
        """
        if not self.is_fat32:
            return int.from_bytes(self.parsed.firstCluster, byteorder='little')
        start_cluster_bytes = self.parsed.firstCluster \
                                + self.parsed.accessRightsBitmap
        return int.from_bytes(start_cluster_bytes, byteorder='little')

    def get_filesize(self) -> int:
        """
        get directory entries filesize attribute
        :return: int, filesize of dir_entry
        """
        return self.parsed.fileSize
