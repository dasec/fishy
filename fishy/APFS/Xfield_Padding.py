# This class contains code under Copyright (c) by 2017 Jonas Plum licensed through GPL3.0 Licensing
import numpy as np
import typing as typ
from fishy.APFS.APFS_filesystem.InodeTable import InodeTable
from fishy.APFS.APFS_filesystem.Node import Node
from fishy.APFS.APFS_filesystem.APFS import APFS


class APFSXfieldPaddingMetadata:
    """
    holds information about calculated padding offsets and sizes as well as corresponding node offsets.
    """

    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of an APFSXfieldPaddingMetadata object.
        """
        if d is None:
            self.paddingAddresses = []
            self.nodeAddresses = []
            self.sizes = []
        else:
            self.paddingAddresses = d["paddingAddresses"]
            self.nodeAddresses = d["nodeAddresses"]
            self.sizes = d["sizes"]

    def add_paddingAddress(self, paddingAddress: int):
        """
        add calculated padding address to list of padding addresses.
		:param paddingAddress: int, calculated padding offset
        """
        self.paddingAddresses.append(paddingAddress)

    def add_nodeAddress(self, nodeAddress: int):
        """
        add node offset to list of node offsets.
		:param nodeAddress: int, node offset
        """
        self.nodeAddresses.append(nodeAddress)

    def get_nodeAddresses(self):
        """
        :returns: list of used node addresses
        """
        return self.nodeAddresses

    def get_paddingAddresses(self):
        """
        :returns: list of used calculated padding offsets
        """
        return self.paddingAddresses

    def add_size(self, size: int):
        """
        add size of a padding field to a list of sizes.
        :param size: int, size of a padding field.
        """
        self.sizes.append(size)

    def get_sizes(self):
        """
        :returns: list of used padding field sizes
        """
        return self.sizes


class APFSXfieldPadding:
    """
    contains methods to write, read and clean hidden data using the padding created by the inode extended fields in an APFS filesystem. 
	"""

    def __init__(self, stream: typ.BinaryIO):
        """
        :param stream: typ.BinaryIO, filedescriptor of an APFS filesystem
        """
        self.stream = stream
        self.apfs = APFS(stream)
        self.blocksize = self.apfs.getBlockSize()
        self.inodetable = InodeTable(stream)
        self.inodelist = self.inodetable.getAllInodes(self.stream)


    def write(self, instream: typ.BinaryIO):
        metadata = APFSXfieldPaddingMetadata()

        padding = []
        nopadding = []
        all = []

        for i in range(0, len(self.inodelist)):
            inodeaddress = self.inodelist[i][0] + self.inodelist[i][1]

            #get xfield table of contents address & number of extended fields per inode:
            inodeaddress += 92
            self.stream.seek(inodeaddress)
            xfield_nr = self.stream.read(2)
            xfield_nr = int.from_bytes(xfield_nr, byteorder='little')
            #print(self.inodelist[i][0]/4096)
            #print(xfield_nr)
            #iterate over xfields, calculate space, use prev size to calculate offset if multiple xfields
            prev_size = 0
            self.stream.seek(0)
            for j in range(0, xfield_nr):
                xhdr_size_addr = inodeaddress + (j*4) + 6
                self.stream.seek(xhdr_size_addr)
                xhdr_size = self.stream.read(2)
                xhdr_size = int.from_bytes(xhdr_size, byteorder='little')
                all.append(xhdr_size)
                #print(xhdr_size)
                #add xfield size & potential padding size to prev_size;
                prev_size += xhdr_size
                self.stream.seek(0)
                if not (xhdr_size % 8):
                    nopadding.append(xhdr_size)
                if (xhdr_size % 8):
                    prev_size += (8 - xhdr_size % 8)
                    # calculate slack address & size
                    if j > 0:
                        slack_address = inodeaddress + 4 + (xfield_nr * 4) + xhdr_size + prev_size
                    if j == 0:
                        slack_address = inodeaddress + 4 + (xfield_nr * 4) + xhdr_size
                    #print(slack_address)
                    slack_size = (xhdr_size +(8 - xhdr_size % 8)) - xhdr_size
                    #print(slack_size)

                    padding.append([slack_address, slack_size, self.inodelist[i][0]])

        usedPadding = self.writeToPadding(instream, padding)

        #send padding tuple list and instream to subfunction, subfunction writes until instream size is 0

        for i in range(0, len(usedPadding)):
            self.stream.seek(usedPadding[i][2]+8)
            data = self.stream.read(4088)
            chksm = self.calcChecksum(data)
            self.stream.seek(usedPadding[i][2])
            self.stream.write(chksm)
            self.stream.seek(0)

            metadata.add_nodeAddress(usedPadding[i][2])
            metadata.add_size(usedPadding[i][1])
            metadata.add_paddingAddress(usedPadding[i][0])

        return metadata

    def read(self,outstream: typ.BinaryIO, metadata: APFSXfieldPaddingMetadata):
        paddingAddresses = metadata.get_paddingAddresses()
        sizes = metadata.get_sizes()
        totalsize = 0
        i = 0

        for s in sizes:
            totalsize += s

        for adr in paddingAddresses:
            #           print(str(adr) + "\n")
            outstream.write(self.readFromPadding(adr, sizes[i]))
            totalsize -= 4
            i += 1
            if totalsize <= 0:
                break



    def clear(self, metadata: APFSXfieldPaddingMetadata):
        paddingAddresses = metadata.get_paddingAddresses()
        nodeAddresses = metadata.get_nodeAddresses()
        sizes = metadata.get_sizes()
        totalsize = 0

        for s in sizes:
            totalsize += s

        for j in range(0, len(paddingAddresses)):
            clearspace = self.clearPadding(paddingAddresses[j], sizes[j])
            totalsize -= clearspace
            self.stream.seek(nodeAddresses[j] + 8)
            data = self.stream.read(4088)
            chksm = self.calcChecksum(data)
            self.stream.seek(nodeAddresses[j])
            self.stream.write(chksm)
            self.stream.seek(0)
            if totalsize <= 0:
                break



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

    def writeToPadding(self, instream, padding):
        j = 0
        usedPadding = []
        total_size = 0
        for i in range(0, len(padding)):
            total_size += padding[i][1]
        #print(total_size)

        while instream.peek():
            if total_size <= 0:
                break
            writeaddress = padding[j][0]
#            print(writeaddress)
            writesize = padding[j][1]
 #           print(writesize)
            nodeaddress = padding[j][2]
            total_size -= writesize
            writebuf = instream.read(writesize)
            usedPadding.append([writeaddress, writesize, nodeaddress])
            self.stream.seek(0)
            self.stream.seek(writeaddress)
            self.stream.write(writebuf)
  #          print(writebuf)
            j += 1
            if not instream.peek():
                break
            if total_size <= 0 and instream.peek():
                raise IOError("Not enough space")

        return usedPadding
        # returns "modified" padding tuple list with only the used offset, size and node address

    def clearPadding(self, adr, size):
        l = size
        address = adr
        self.stream.seek(address)
        self.stream.write(l * b'\x00')

        return l

    def readFromPadding(self, address, length):
        self.stream.seek(0)
        readAddress = address
        self.stream.seek(readAddress)
        l = length
        data = self.stream.read(l)

        return data

