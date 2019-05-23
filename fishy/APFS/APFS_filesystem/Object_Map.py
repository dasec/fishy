from fishy.APFS.APFS_filesystem.APFS_Parser import Parser
from fishy.APFS.APFS_filesystem.Volume_Superblock import vSuperblock
from fishy.APFS.APFS_filesystem.Node import Node

class ObjectMap:

    structure = {
        "B-Tree_Type": {"offset": 0x0, "size": 8, "format": "hex"},
        "root": {"offset": 0x10, "size": 8},
        "reserved": {"offset": 0x18, "size": 56}
        # There are supposed to be more than just the root Node and tree type in the block type, but none of the images
        # show that - so there is a reserved space given just in case the other components show up

    }

    def __init__(self, fs_stream, offset, blocksize):
        self.offset = offset
        self.blocksize = blocksize
        self.data = self.parseObjectMap(fs_stream, offset)
        self.root = self.getRootNode(fs_stream)

    def parseObjectMap(self, fs_stream, offset):
        d = Parser.parse(fs_stream, offset+32, self.blocksize-32, structure=self.structure)
        return d

    def getRootNode(self, fs_stream):
        blocksize = self.blocksize
        root = self.data["root"] * blocksize
        return root

    def map_CObject(self, mapArray):

        # TODO: use mapping parts of this function (receive tuple array, calculate offset of volumes & parse;
        # TODO: \2 remove printing parts as soon as other function of mapping is implemented, keep marked as important

        blocksize = self.blocksize
        # important
        #print("Used Volumes: " + str(len(mapArray)) + "\n")
       # for x, y in mapArray: # important
        #    print("Address: " + str(x) + " | " + " Volume ID: " + str(y))

        mapArrayCalc = []
        for x,y in mapArray:
            singleCalc = ((x*blocksize), y)
            mapArrayCalc.append(singleCalc)

        return mapArrayCalc

    def mapCObjectMap(self, fs_stream):

        root = self.root

        rootnode = Node(fs_stream, root, self.blocksize)

        vm = rootnode.getVolumeMapping()

        calcMap = self.map_CObject(vm)

        volumesList = []

        for x,y in calcMap:
            vol_superblock = vSuperblock(fs_stream, x, self.blocksize)
            d = (vol_superblock.parseVolumeSuperblock(fs_stream, x), y)
            volumesList.append(d)

        return volumesList





