# This class contains code under Copyright (c) by 2017 Jonas Plum licensed through GPL3.0 Licensing
import numpy as np
import typing as typ
import logging
from fishy.APFS.APFS_filesystem.InodeTable import InodeTable
from fishy.APFS.APFS_filesystem.Node import Node
from fishy.APFS.APFS_filesystem.APFS import APFS

LOGGER = logging.getLogger("APFS-Inode-Padding")


class APFSInodePaddingMetadata:
    """
    holds offsets of used inode padding fields and the respective node offsets.
    """
    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of an APFSInodePaddingMetadata
                  object
        """
        if d is None:
            self.inodeAddresses = []
            self.nodeAddresses = []
        else:
            self.inodeAddresses = d["inodeAddresses"]
            self.nodeAddresses = d["nodeAddresses"]

    def add_inodeAddress(self, inodeAddress: int):
        """
        add an inode offset to the list.

        :param inodeAddress: int, exact inode offset
        """
        self.inodeAddresses.append(inodeAddress)

    def add_nodeAddress(self, nodeAddress: int):
        """
        add node offset to the list.

        :param nodeAddress: int, node offset		
        """
        self.nodeAddresses.append(nodeAddress)

    def get_nodeAddresses(self):
        """
        returns list of used node addresses.

        :return: list of node addresses 
        """
        return self.nodeAddresses

    def get_inodeAddresses(self):
        """
        returns list of inode addresses.

        :return: list of inode addresses		
        """
        return self.inodeAddresses



class APFSInodePadding:
    """
    contains methods to write, read and clean hidden data using the padding fields present in every inode in the APFS filesystem.
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
        writes from instream to inode padding fields. 

        :param instream: typ.BinaryIO, stream containing data that is supposed to be hidden 

		:return: APFSInodePaddingMetadata
        """
        metadata = APFSInodePaddingMetadata()
        instream = instream.read()

        if len(instream) > len(self.inodelist)*10:
            raise IOError("Not enough space available")

        instream_chunks = [instream[i:i+10]for i in range (0, len(instream), 10)]
        hidden_chunks = 0
        i = 0
        while hidden_chunks < len(instream_chunks):
            chunk = instream_chunks[hidden_chunks]
            writeaddress = self.inodelist[i][0] + self.inodelist[i][1]
            self.writeToPadding(writeaddress, chunk)
            metadata.add_inodeAddress(self.inodelist[i][0] + self.inodelist[i][1])
            hidden_chunks += 1
            # change has-uncompressed-size-flag. TODO mor elegant solution? (flag+0x4 instead of overwrite) 
            self.stream.seek(self.inodelist[i][0] + self.inodelist[i][1] + 50)
            self.stream.write(b'\x04')

            self.stream.seek(self.inodelist[i][0]+8)
            data = self.stream.read(4088)
            chksm = self.calcChecksum(data)
            self.stream.seek(self.inodelist[i][0])
            metadata.add_nodeAddress(self.inodelist[i][0])
            self.stream.write(chksm)
            self.stream.seek(0)
            i+=1
        return metadata

    def read(self, outstream: typ.BinaryIO, metadata: APFSInodePaddingMetadata):
        """
        writes previously hidden data into outstream.

        :param outstream: stream to write to 

        :param metadata: APFSInodePaddingMetadata object 
        """
        inode_addresses = metadata.get_inodeAddresses()
        for adr in inode_addresses:
            outstream.write(self.readFromPadding(adr))


    def clear(self, metadata: APFSInodePaddingMetadata):
        """
        clears previously hidden data into outstream. 

        :param metadata: APFSInodePaddingMetadata object 
        """
        inode_addresses = metadata.get_inodeAddresses()
        node_addresses = metadata.get_nodeAddresses()
        i = 0
        for adr in inode_addresses:
            self.clearPadding(adr)
            self.stream.seek(node_addresses[i] + 8)
            data = self.stream.read(4088)
            chksm = self.calcChecksum(data)
            self.stream.seek(node_addresses[i])
            self.stream.write(chksm)
            self.stream.seek(0)
            i+=1



    def info(self):
        """
        not yet implemented for this technique
        """
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

    def getTotalOffset(self, a):
        inodePadAdd = a + 82
        # address of inode + offset to 2 padding fields
        return inodePadAdd


    def readFromPadding(self, address):
        """
        reads 10 bytes from one inode padding. 

        :param address: offset of a single inode padding 

        :return: data to be written to outstream 
        """
        self.stream.seek(0)
        readAddress = self.getTotalOffset(address)
        self.stream.seek(readAddress)
        data = self.stream.read(10)
        return data


    def clearPadding(self, address):
        """
        clears 10 bytes from one inode padding. 

        :param address: offset of a single inode padding 
        """
        self.stream.seek(0)
        clearAddress = self.getTotalOffset(address)
        self.stream.seek(clearAddress)
        self.stream.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

    def writeToPadding(self, address, chunk):
        """
        writes 10 bytes to one inode padding.

        :param address: offset of a single inode padding

        :param chunk: 10 byte chunk of data that is supposed to be written to the inode padding referenced by address 
        """
        self.stream.seek(0)
        writeAddress = self.getTotalOffset(address)
        self.stream.seek(writeAddress)
        self.stream.seek(writeAddress)
        self.stream.write(chunk)



