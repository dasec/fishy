# This class contains code under Copyright (c) by 2017 Jonas Plum licensed through GPL3.0 Licensing
import numpy as np
import typing as typ
from fishy.APFS.APFS_filesystem.InodeTable import InodeTable
from fishy.APFS.APFS_filesystem.Node import Node
from fishy.APFS.APFS_filesystem.APFS import APFS



class APFSTimestampHidingMetadata:
    """
    holds information about inode offsets, node offsets and sizes of hidden data chunks.
    """

    def __init__(self, d: dict = None):
        """
        :param d: dictionary representation of APFSTimestampHidingMetadata
        """
        if d is None:
            self.inodeAddresses = []
            self.nodeAddresses = []
            self.length = []
        else:
            self.inodeAddresses = d["inodeAddresses"]
            self.nodeAddresses = d["nodeAddresses"]
            self.length = d["length"]

    def add_length(self, length: int) -> None:
        """
        add size of the hidden data to metadata object.

        :param length: int, size of hidden data
        """
        self.length.append(length)

    def add_inodeAddress(self, inodeAddress: int):
        """
        add inode offset to list of inode offsets.

        :param inodeAddress: int, offset of an inode
        """
        self.inodeAddresses.append(inodeAddress)

    def add_nodeAddress(self, nodeAddress: int):
        """
        add node offset to list of node offsets.

        :param nodeAddress: int, offset of a node
        """
        self.nodeAddresses.append(nodeAddress)

    def get_nodeAddresses(self):
        """
        return list of node offsets.

        :return: list of node offsets
        """
        return self.nodeAddresses

    def get_inodeAddresses(self):
        """
        return list of inode offsets.

        :return: list of inode offsets
        """
        return self.inodeAddresses

    def get_length(self) \
            -> int:
        """
        return size of hidden data.

        :return: size of hidden data
        """
        return self.length[0]



class APFSTimestampHiding:
    """
    contains methods to write, read and clear data using the nanosecond timestamp found in APFS inodes.
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
        """
        writes data from instream to chosen inode timestamps.

        :param instream: typ.BinaryIO, stream containing data that is supposed to be hidden

        :return: APFSTimestampHidingMetadata object
        """
        metadata = APFSTimestampHidingMetadata()
       # instream = instream.read()

        #if len(instream) > len(self.inodelist)*16:
         #   raise IOError("Not enough space available")

#        instream_chunks = [instream[i:i+4]for i in range (0, len(instream), 4)]

    #TODO: 30 BIT CHUNKS -> FILL WITH 30 BIT FROM INSTREAM IN FOR LOOP; PUT INTO LIST INSTREAM_CHUNKS

        #hidden_chunks = 0
        opensize = len(self.inodelist)*16
        filesize = 0
        i = 0
        j = 0
        # Chunks werden an durch InodeTable geschrieben. Hierfür wird die Submethode writeToPadding aufgerufen
        # Danach wird die Checksumme neu kalkuliert
        #while hidden_chunks < len(instream_chunks):
        while instream.peek():
            if opensize == 0:
                break
            #chunk = instream_chunks[hidden_chunks]

            writeaddress = self.inodelist[i][0] + self.inodelist[i][1]
            tempsize = self.writeToPadding(writeaddress, instream, j)
            opensize -= tempsize
            filesize += tempsize
            metadata.add_inodeAddress(self.inodelist[i][0] + self.inodelist[i][1])

            print(str(self.inodelist[i][0]) + " " + str(self.inodelist[i][1]))
            print(str(writeaddress))

            #hidden_chunks += 1

            self.stream.seek(self.inodelist[i][0]+8)
            data = self.stream.read(4088)
            chksm = self.calcChecksum(data)
            self.stream.seek(self.inodelist[i][0])
            metadata.add_nodeAddress(self.inodelist[i][0])
            self.stream.write(chksm)
            self.stream.seek(0)
            j += 1
            if j == 4:
                j = 0
                i += 1
            if not instream.peek():
                break
        if instream.peek():
            raise IOError("Not enough space")
        metadata.add_length(filesize)
        return metadata

    def read(self, outstream: typ.BinaryIO, metadata: APFSTimestampHidingMetadata):
        """
        reads data from chosen inode timestamps and writes the data to chosen outstream.

        :param outstream: chosen outstream to display found data

        :param metadata: an APFSTimestampHidingMetadata object
        """
        inode_addresses = metadata.get_inodeAddresses()
        length = metadata.get_length()
        j = 0
        for adr in inode_addresses:
 #           print(str(adr) + "\n")
            outstream.write(self.readFromPadding(adr, length, j))
            length -= 4
            if length <= 0:
                break
            j += 1
            if j == 4:
                j = 0


    def clear(self, metadata: APFSTimestampHidingMetadata):
        """
        clears data from chosen inode timestamps.

        :params metadata: an APFSTimestampHidingMetadata object
        """
        inode_addresses = metadata.get_inodeAddresses()
        node_addresses = metadata.get_nodeAddresses()
        length = metadata.get_length()
        i = 0
        j = 0
        for adr in inode_addresses:
            clearspace=self.clearPadding(adr, length, j)
            length -= clearspace
#            print(str(adr))
            self.stream.seek(node_addresses[i] + 8)
            data = self.stream.read(4088)
            chksm = self.calcChecksum(data)
            self.stream.seek(node_addresses[i])
            self.stream.write(chksm)
            self.stream.seek(0)
            j+=1
            if j == 4:
                j = 0
                i+=1
            if length <= 0:
                break


    def info(self):
        raise NotImplementedError("Not implemented for this filesystem")




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

    def getTotalOffset(self, a, j):
        """
        calculates offset of hiding space within an inode.

        :param a: offset of an inode

        :param j: indicating the chosen timestamp. j can be any valuable from 0 to 3 as there are 4 possible timestamps

        :return: exact offset of hiding space
        """

        if j == 0:
            inodePadAdd = a + 16
        elif j == 1:
            inodePadAdd = a + 24
        elif j == 2:
            inodePadAdd = a + 32
        elif j == 3:
            inodePadAdd = a + 40

        return inodePadAdd


    def readFromPadding(self, address, length, j):
        """
        subfunction that reads data from single timestamps.

        :params address: offset of an inode

        :params length: size of the hidden data

        :param j: indicating the chosen timestamp. j can be any valuable from 0 to 3 as there are 4 possible timestamps

        :return: data found in timestamp
        """
        self.stream.seek(0)
        readAddress = self.getTotalOffset(address, j)
        self.stream.seek(readAddress)
        if length > 4:
            l = 4
            data = self.stream.read(l)
        if length <= 4:
            l = length
            data = self.stream.read(l)

        return data


    def clearPadding(self, address, length, j):
        """
        subfunction that clears a single timestamp of previously hidden data.

        :param address: offset of an inode

        :param length: size of the hidden data

        :param j: indicating the chosen timestamp. j can be any valuable from 0 to 3 as there are 4 possible timestamps

        :return: size of removed data chunk
        """
        self.stream.seek(0)
        l = 0
        if length > 4:
            l = 4
        elif length <= 4:
            l = length
        clearAddress = self.getTotalOffset(address, j)
        self.stream.seek(clearAddress)
        self.stream.write(l * b'\x00')
        return l

    def writeToPadding(self, address, instream, j):
        """
        writes data to a single timestamp.

        :param address: offset of an inode

        :param instream: stream containing the data that is supposed to be hidden

        :param j: indicating the chosen timestamp. j can be any valuable from 0 to 3 as there are 4 possible timestamps

        :return: size of the hidden data chunk
        """

        buf = instream.read(4)
        self.stream.seek(0)
        writeAddress = self.getTotalOffset(address, j)
        self.stream.seek(writeAddress)
        self.stream.write(buf)
        print(str(writeAddress) + " " + str(buf))
        return len(buf)



