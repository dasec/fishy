# This class contains code under Copyright (c) by 2017 Jonas Plum licensed through GPL3.0 Licensing


import typing as typ

import numpy as np

from fishy.APFS.APFS_filesystem.APFS import APFS
from fishy.APFS.APFS_filesystem.Checkpoints import Checkpoints

class APFSSuperblockSlackMetaData:
    """
    holds information about the offsets of all used blocks and the size of the hidden data.
    """
    def __init__(self, d: dict = None):
        """
        :param d: dictionary representation of an APFSSuperblockSlackMetaData object
        """
        if d is None:
            self.cblocks = []
            self.cmblocks = []
            self.vblocks = []
            self.vmblocks = []
            self.length = []
        else:
            self.cblocks = d["cblocks"]
            self.cmblocks = d["cmblocks"]
            self.vblocks = d["vblocks"]
            self.vmblocks = d["vmblocks"]

            self.length = d["length"]

    def add_cblock(self, block_address: int) -> None:
        """
        adds the address of a container superblock to the list of container superblock addresses.

        :param block_address: int, address of a container superblock
        """
        self.cblocks.append(block_address)

    def add_cmblock(self, block_address: int) -> None:
        """
        adds the address of a container object map to the list of container object map addresses.

        :param block_address: int, address of a container object map
        """
        self.cmblocks.append(block_address)

    def add_vblock(self, block_address: int) -> None:
        """
        adds the address of a volume superblock to the list of volume superblock addresses.

        :param block_address: int, address of a volume superblock
        """
        self.vblocks.append(block_address)

    def add_vmblock(self, block_address: int) -> None:
        """
        adds the address of a volume object map to the list of volume object map addresses.

        :param block_address: int, address of a volume object map
        """
        self.vmblocks.append(block_address)

    def add_length(self, length: int) -> None:
        """
        add size of hidden data to metadata object.

        :param length: int, size of hidden data
        """

        self.length.append(length)

    def get_cblocks(self) \
            -> []:
        """
        returns list of container superblock addresses.

        :return: list of container superblock addresses
        """
        return self.cblocks

    def get_cmblocks(self) \
            -> []:
        """
        returns list of container object map addresses.

        :return: list of container object map addresses
        """
        return self.cmblocks

    def get_vblocks(self) \
            -> []:
        """
        returns list of volume superblock addresses.

        :return: list of volume superblock addresses
        """
        return self.vblocks

    def get_vmblocks(self) \
            -> []:
        """
        returns list of volume object map addresses.

        :return: list of volume object map addresses
        """
        return self.vmblocks

    def get_length(self) \
            -> int:
        """
        return size of hidden data.

        :return: size of hidden data
        """
        return self.length[0]


class APFSSuperblockSlack:
    """
    contains methods to write, read and clean hidden data using APFS superblocks and object map structures.
    """

    def __init__(self, stream: typ.BinaryIO):
        """
        :param stream: typ.BinaryIO, filedescriptor of an APFS filesystem
        """
        self.stream = stream
        self.apfs = APFS(stream)
        self.blocksize = self.apfs.getBlockSize()

    def write(self, instream: typ.BinaryIO):
        """
        writes data from instream to superblock and object map structures.

        :param instream: stream containing the data that is supposed to be hidden

        :return: an APFSSuperblockSlackMetaData object
        """
        metadata = APFSSuperblockSlackMetaData()

        checkpoints = Checkpoints(self.stream)

        al = checkpoints.getCheckpointSuperblocks(self.stream)
        csb = len(al)

        cml = checkpoints.getCheckpointCMAP(self.stream, al)
        csbml = len(cml)

        vl = checkpoints.getCheckpointVolumes(self.stream, cml)
        vsb = len(vl)

        vml = checkpoints.getCheckpointVMAP(self.stream, vl)
        vsbml = len(vl)


        opensize = self.calculateHidingSpace(al, cml, vl, vml)
        filesize = 0

#        if (len(instream) > opensize):
 #           raise IOError("Not enough hiding space")


        while instream.peek():
            if opensize == 0:
                break
            else:
                if csb > 0:
                    containerblock = al.pop(0)
                    caddress = containerblock[0] + 32 + 1448
                    tempsize = self.writeToContainerBlock(caddress, instream)
                    opensize -= tempsize
                    filesize += tempsize
                    metadata.add_cblock(caddress)
                    csb -= 1
                    self.stream.seek(containerblock[0]+8)
                    tocheck = self.stream.read(4088)
                    a = self.calcChecksum(tocheck)
                    self.stream.seek(containerblock[0])
                    self.stream.write(a)
                    if not instream.peek():
                        break
                if csbml > 0:
                    containermap = cml.pop(0)
                    cmaddress = containermap[0] + 32 + 80
                    tempsize = self.writeToContainerMap(cmaddress, instream)
                    opensize -= tempsize
                    filesize += tempsize
                    metadata.add_cmblock(cmaddress)
                    csbml -= 1
                    self.stream.seek(containermap[0]+8)
                    tocheck = self.stream.read(4088)
                    a = self.calcChecksum(tocheck)
                    self.stream.seek(containermap[0])
                    self.stream.write(a)
                    if not instream.peek():
                        break
                if vsb > 0:
                    volumeblock = vl.pop(0)
                    vaddress = volumeblock[0] + 32 + 1004
                    tempsize = self.writeToVolumeBlock(vaddress, instream)
                    opensize -= tempsize
                    filesize += tempsize
                    metadata.add_vblock(vaddress)
                    vsb -= 1
                    self.stream.seek(volumeblock[0]+8)
                    tocheck = self.stream.read(4088)
                    a = self.calcChecksum(tocheck)
                    self.stream.seek(volumeblock[0])
                    self.stream.write(a)
                    if not instream.peek():
                        break
                if vsbml > 0:
                    volumemap = vml.pop(0)
                    vmaddress = volumemap[0] + 32 + 80
                    tempsize = self.writeToVolumeMap(vmaddress, instream)
                    opensize -= tempsize
                    filesize += tempsize
                    metadata.add_vmblock(vmaddress)
                    vsbml - 1
                    self.stream.seek(volumemap[0]+8)
                    tocheck = self.stream.read(4088)
                    a = self.calcChecksum(tocheck)
                    self.stream.seek(volumemap[0])
                    self.stream.write(a)
                    if not instream.peek():
                        break

        if instream.peek():
            raise IOError("Not enough space")
        metadata.add_length(filesize)

#        self.stream.seek(0)
        return metadata

    def calcChecksum(self, data):
        # Copyright (c) 2017 Jonas Plum under GPL3.0 Licensing

        sum1 = np.uint64(0)
        sum2 = np.uint64(0)

        modValue = np.uint64(4294967295)  # 2<<31 - 1

        for i in range(int(len(data) / 4)):
            dt = np.dtype(np.uint32)
            dt = dt.newbyteorder('L')
            d = np.frombuffer(data[i * 4:(i + 1) * 4], dtype=dt)

            sum1 = (sum1 + np.uint64(d)) % modValue
            sum2 = (sum2 + sum1) % modValue

        check1 = modValue - ((sum1 + sum2) % modValue)
        check2 = modValue - ((sum1 + check1) % modValue)

        return (check2 << 32) | check1


    def calculateHidingSpace(self, cl, cml, vl, vml):
        # Not needed as of right now; stays implemented in case info method or other method gets added and needs it

        cl_space = self.blocksize - 32 - 1448
        #container superblocks: used biggest possible container superblock : 1448 bytes or 0x5A8 hex
        cml_space = self.blocksize - 32 - 80
        vml_space = self.blocksize - 32 - 80
        #object map largest possible + 56 potentially reserved space: 80 bytes or 0x50
        vl_space = self.blocksize - 32 - 1004


        total_cl_space = len(cl) * cl_space
        total_cml_space = len(cml) * cml_space
        total_vml_space = len(vml) * vml_space
        total_vl_space = len(vl) * vl_space
        #calculate amount of object maps and superblocks times the free space

        total_space = total_cl_space + total_cml_space + total_vl_space + total_vml_space

        return total_space

    def writeToContainerBlock(self, address, instream):
        """
        subfunction to write data to a container superblock.

        :param address: offset of a container superblock

        :param instream: stream containing the data that is supposed to be hidden

        :return: size of the chunk of data that was hidden in this structure
        """
        cl_space = self.blocksize - 32 - 1448
        buf = instream.read(cl_space)
        self.stream.seek(address)
        self.stream.write(buf)
        self.stream.seek(0)
        return len(buf)

    def writeToContainerMap(self, address, instream):
        """
        subfunction to write data to a container object map.

        :param address: offset of a container object map

        :param instream: stream containing the data that is supposed to be hidden

        :return: size of the chunk of data that was hidden in this structure
        """
        cml_space = self.blocksize - 32 - 80
        buf = instream.read(cml_space)
        self.stream.seek(address)
        self.stream.write(buf)
        self.stream.seek(0)
        return len(buf)

    def writeToVolumeBlock(self, address, instream):
        """
        subfunction to write data to a volume superblock.

        :param address: offset of a volume superblock

        :param instream: stream containing the data that is supposed to be hidden

        :return: size of the chunk of data that was hidden in this structure
        """
        vl_space = self.blocksize - 32 - 1004
        buf = instream.read(vl_space)
        self.stream.seek(address)
        self.stream.write(buf)
        self.stream.seek(0)
        return len(buf)

    def writeToVolumeMap(self, address, instream):
        """
        subfunction to write data to a volume object map.

        :param address: offset of a volume object map

        :param instream: stream containing the data that is supposed to be hidden

        :return: size of the chunk of data that was hidden in this structure
        """
        vml_space = self.blocksize - 32 - 80
        buf = instream.read(vml_space)
        self.stream.seek(address)
        self.stream.write(buf)
        self.stream.seek(0)
        return len(buf)

    def clear(self, metadata: APFSSuperblockSlackMetaData):
        """
        removes data from APFS superblock and object map structures.

        :param metadata: an APFSSuperblockSlackMetaData object
        """

        checkpoints = Checkpoints(self.stream)

        al = checkpoints.getCheckpointSuperblocks(self.stream)
        csb = len(al)

        cml = checkpoints.getCheckpointCMAP(self.stream, al)
        csbml = len(cml)

        vl = checkpoints.getCheckpointVolumes(self.stream, cml)
        vsb = len(vl)

        vml = checkpoints.getCheckpointVMAP(self.stream, vl)
        vsbml = len(vl)

        checkpoints = Checkpoints(self.stream)
        al = checkpoints.getCheckpointSuperblocks(self.stream)
        cml = checkpoints.getCheckpointCMAP(self.stream, al)
        vl = checkpoints.getCheckpointVolumes(self.stream, cml)
        vml = checkpoints.getCheckpointVMAP(self.stream, vl)


        length = metadata.get_length()
        i = 0
        blocksize = self.blocksize
        cblocks = metadata.get_cblocks()
        cmblocks = metadata.get_cmblocks()
        vblocks = metadata.get_vblocks()
        vmblocks = metadata.get_vmblocks()

        if len(cblocks) == 0:
            raise IOError("Nothing has been hidden")

        while length >= 0:
            containerblock = al.pop(0)
            caddress = cblocks[i]
            cspace = blocksize - 32 - 1448
            self.stream.seek(caddress)
            self.stream.write(cspace * b'\x00')
            length -= cspace
            self.stream.seek(containerblock[0] + 8)
            tocheck = self.stream.read(4088)
            a = self.calcChecksum(tocheck)
            self.stream.seek(containerblock[0])
            self.stream.write(a)
            if length <= 0:
                break
            containermap = cml.pop(0)
            cmaddress = cmblocks[i]
            cmspace = blocksize - 32 - 80
            self.stream.seek(cmaddress)
            self.stream.write(cmspace * b'\x00')
            length -= cmspace
            self.stream.seek(containermap[0] + 8)
            tocheck = self.stream.read(4088)
            a = self.calcChecksum(tocheck)
            self.stream.seek(containermap[0])
            self.stream.write(a)
            if length <= 0:
                break
            volumeblock = vl.pop(0)
            vaddress = vblocks[i]
            vspace = blocksize - 32 - 1004
            self.stream.seek(vaddress)
            self.stream.write(vspace * b'\x00')
            length -= vspace
            self.stream.seek(volumeblock[0] + 8)
            tocheck = self.stream.read(4088)
            a = self.calcChecksum(tocheck)
            self.stream.seek(volumeblock[0])
            self.stream.write(a)
            if length <= 0:
                break
            volumemap = vml.pop(0)
            vmaddress = vmblocks[i]
            vmspace = blocksize - 32 - 80
            self.stream.seek(vmaddress)
            self.stream.write(vmspace * b'\x00')
            length -= vmspace
            self.stream.seek(volumemap[0] + 8)
            tocheck = self.stream.read(4088)
            a = self.calcChecksum(tocheck)
            self.stream.seek(volumemap[0])
            self.stream.write(a)
            if length <= 0:
                break
            i += 1

    def read(self, outstream: typ.BinaryIO, metadata: APFSSuperblockSlackMetaData):
        """
        reads data hidden in APFS superblock and object map structures and writes that data to an outstream.

        :param outstream: chosen outstream to display found hidden data

        :param metadata: an APFSSuperblockSlackMetaData object
        """
        length = metadata.get_length()
        foundlength = 0
        i = 0
        blocksize = self.blocksize
        cblocks = metadata.get_cblocks()
        cmblocks = metadata.get_cmblocks()
        vblocks = metadata.get_vblocks()
        vmblocks = metadata.get_vmblocks()

        if len(cblocks) == 0:
            raise IOError("Nothing has been hidden")

        while length > 0:
            cspace = blocksize - 32 - 1448
            caddress = cblocks[i]
            self.stream.seek(caddress)
            if length <= cspace:
                buf = self.stream.read(length)
            else:
                buf = self.stream.read(cspace)
            outstream.write(buf)
            length -= cspace
            if length <= 0:
                break
            cmspace = blocksize - 32 - 80
            cmaddress = cmblocks[i]
            self.stream.seek(cmaddress)
            if length <= cmspace:
                buf = self.stream.read(length)
            else:
                buf = self.stream.read(cmspace)
            outstream.write(buf)
            length -= cmspace
            if length <= 0:
                break
            vspace = blocksize - 32 - 1004
            vaddress = vblocks[i]
            if length <= vspace:
                buf = self.stream.read(length)
            else:
                buf = self.stream.read(vspace)
            outstream.write(buf)
            length -= vspace
            if length <= 0:
                break
            vmspace = blocksize - 32 - 80
            vmaddress = vmblocks[i]
            self.stream.seek(vmaddress)
            if length <= vmaddress:
                buf = self.stream.read(length)
            else:
                buf = self.stream.read(vmspace)
            outstream.write(buf)
            length -= vmspace
            if length <= 0:
                break
            i += 1

    def info(self):
        raise NotImplementedError("Not implemented for this file system")













