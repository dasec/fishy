# centerpiece of interface implementation, content tbd
# offset and headersize into parser -> get object type function: parse corresponding object structure with offset+header
# \2 (start after header) and blocksize-header (do not include header in parsing of object)

from typing import BinaryIO
from fishy.APFS.APFS_filesystem.Container_Superblock import Superblock
from fishy.APFS.APFS_filesystem.Object_Header import ObjectHeader

# TODO: implement in fishy
# TODO: test on linux
# TODO: Wrapper Functions, CLI implementation, FS Detector implementation
# TODO: macOS VM to test apfs fsck and potential other fs checks

class APFS:

    def __init__(self, stream: BinaryIO):
        self.stream = stream
        self.mainSuperblock = Superblock(stream, 0)
        self.blocksize = self.getBlockSize()

    def getObjectType(self, offset):
        # TODO: move to Object_Header.py
        objectType = " \n"
        ohead = ObjectHeader(self.stream, offset)
        d = ohead.parse_object_header(self.stream, offset)
        tempType = d["type"]
        if tempType == 0:
            objectType = "not found \n"
        elif tempType == 1:
            objectType = "Container Superblock detected"
        elif tempType == 2:
            objectType = "Root Node detected"
        elif tempType == 3:
            objectType = "Node detected"
        elif tempType == 5:
            objectType = "Space Manager detected"
        elif tempType == 7:
            objectType = "Space Manager Internal Pool detected"
        elif tempType == 11:
            objectType = "B-Tree detected"
        elif tempType == 12:
            objectType = "Checkpoint detected"
        elif tempType == 13:
            objectType = "Volume Superblock detected"
        elif tempType == 17:
            objectType = "Reaper detected"


        return objectType

    def getBlockSize(self):
        blocksize = self.mainSuperblock.getBlockSize()
        return blocksize

