# this is a simple checkpoint class that only iterates through all container and volume superblocks (and comaps)
# 1/2 So far, this checkpoint parsing system only supports apfs images that have contiguous checkpoint descriptor areas
# 2/2 since it has proven impossible to artificially create a non-contiguous checkpoint descriptor area


from fishy.APFS.APFS_filesystem.Container_Superblock import Superblock
from fishy.APFS.APFS_filesystem.Object_Header import ObjectHeader
from fishy.APFS.APFS_filesystem.Node import Node
from fishy.APFS.APFS_filesystem.Volume_Superblock import vSuperblock
from fishy.APFS.APFS_filesystem.Object_Map import ObjectMap


class Checkpoints:

    def __init__(self, fs_stream):
        self.mainContainerBlock = Superblock(fs_stream, 0)
        self.data = Superblock(fs_stream, 0).parse_superblock(fs_stream, 0)
        self.blocksize = self.data["block_size"]

    def getCheckpointSuperblocks(self, fs_stream):
        # this function only parses contiguous checkpoint descriptor areas;
        mainInfo = self.mainContainerBlock.parse_superblock(fs_stream, 0)
        csdblocks = mainInfo["xp_desc_blocks"]
        addresslist = []
        addressXidlist = []

        for i in range(1, csdblocks+1):
            fs_stream.seek(i*self.blocksize)
            offset = fs_stream.tell()
            fs_stream.seek(offset + 32)
            fs_type = fs_stream.read(4)
            fs_stream.seek(offset)
            if fs_type == b'NXSB':
                addresslist.append(i*self.blocksize)
            fs_stream.seek(0)

            a = addresslist
            addresslist = list(set(a))

        for i in range(0, len(addresslist)):
           temp = ObjectHeader(fs_stream, addresslist[i]).parse_object_header(fs_stream, addresslist[i])
           xid = temp["xid"]
           addressXidlist.append((addresslist[i], xid))

        addressXidlist=sorted(addressXidlist, key = lambda x:x[1], reverse=True)

        return addressXidlist

        # return tuple list of superblockaddresses and corresponding xid

    def getCheckpointCMAP(self, fs_stream, contxidlist):
        maplist = []
        mapxidlist = []

        for address, xid in contxidlist:
            temp = self.mainContainerBlock.parse_superblock(fs_stream, address)
            maplist.append(temp["omap_oid"]*self.blocksize)

        e = maplist
        maplist = list(set(e))

        for i in range(0, len(maplist)):
            temp = ObjectHeader(fs_stream, maplist[i]).parse_object_header(fs_stream, maplist[i])
            xid = temp["xid"]
            mapxidlist.append((maplist[i], xid))

        mapxidlist=sorted(mapxidlist, key = lambda x:x[1], reverse=True)

        return mapxidlist

    #use parsed checkpoints for maps; returns map addresses

    def getCheckpointVolumes(self, fs_stream, cmapxidlist):
        vollist = []
        volxidlist = []
        for address, xid in cmapxidlist:
            temp = ObjectMap(fs_stream, address, self.blocksize).parseObjectMap(fs_stream, address)
            temproot = temp["root"]*self.blocksize
            rootnode = Node(fs_stream, temproot, self.blocksize)
            vm = rootnode.getVolumeMapping()
            add = [x for x, _ in vm]
            vollist.append(add)

        a = [i[0] for i in vollist]
        b = [i[1] for i in vollist]
        c = [i[2] for i in vollist]
        d = [i[3] for i in vollist]

        e = a + b + c + d

        # Turn list of tuples into multiple lists and make them one list without duplicates

        tempvollist = list(set(e))

        for i in range(0, len(tempvollist)):
            temp = ObjectHeader(fs_stream, tempvollist[i]*self.blocksize)\
                .parse_object_header(fs_stream, tempvollist[i]*self.blocksize)
            xid = temp["xid"]
            volxidlist.append((tempvollist[i]*self.blocksize, xid))

        volxidlist=sorted(volxidlist, key = lambda x:x[1], reverse=True)

        return volxidlist

    # use parsed maps for volume addresses; returns volume addresses

    def getCheckpointVMAP(self, fs_stream, vxidlist):
        vmaplist = []
        vmapxidlist = []

        for address, xid in vxidlist:
            temp = vSuperblock(fs_stream, address, self.blocksize).parseVolumeSuperblock(fs_stream, address)
            vmaplist.append(temp["omap_oid"]*self.blocksize)

        f = vmaplist

        vmaplist = list(set(f))
        for i in range(0, len(vmaplist)):
            temp = ObjectHeader(fs_stream, vmaplist[i]).parse_object_header(fs_stream, vmaplist[i])
            xid = temp["xid"]
            vmapxidlist.append((vmaplist[i], xid))

        vmapxidlist=sorted(vmapxidlist, key = lambda x:x[1], reverse=True)

        return vmapxidlist

        # use parsed volumes for maps; returns map addresses

    def getAllCheckpoints(self, fs_stream):
        contxidlist = self.getCheckpointSuperblocks(fs_stream)
        cmapxidlist = self.getCheckpointCMAP(fs_stream, contxidlist)
        vxidlist = self.getCheckpointVolumes(fs_stream, cmapxidlist)
        vmapxidlist = self.getCheckpointVMAP(fs_stream, vxidlist)

        completelist = contxidlist + cmapxidlist + vxidlist + vmapxidlist

        return completelist

        # put all blockaddresses and tuples in one list; remove duplicates (maps and volumes) ?

