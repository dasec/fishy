# This class contains code under Copyright (c) by 2017 Jonas Plum licensed through GPL3.0 Licensing
import numpy as np
import typing as typ
from fishy.APFS.APFS_filesystem.InodeTable import InodeTable
from fishy.APFS.APFS_filesystem.Node import Node
from fishy.APFS.APFS_filesystem.APFS import APFS

class APFSWriteGenMetadata:
    """
    holds information about node and corresponding inode offsets.
    """

    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of an APFSWriteGenMetadata object.
        """
        if d is None:
            self.inodeAddresses = []
            self.nodeAddresses = []
        else:
            self.inodeAddresses = d["inodeAddresses"]
            self.nodeAddresses = d["nodeAddresses"]

    def add_inodeAddress(self, inodeAddress: int):
        """
        adds inode offset to list of inode offsets.
        
		:param inodeAddress: int, single inode offset
        """
        self.inodeAddresses.append(inodeAddress)

    def add_nodeAddress(self, nodeAddress: int):
        """
        adds node offset to list of node offsets.
        
		:param nodeAddress: int, single node offset
        """
        self.nodeAddresses.append(nodeAddress)

    def get_nodeAddresses(self):
        """
        returns list of node offsets
        
		:returns: list of node offsets
        """
        return self.nodeAddresses

    def get_inodeAddresses(self):
        """
        returns list of node offsets
        
		:returns: list of node offsets
        """
        return self.inodeAddresses



class APFSWriteGen:
    """
    contains methods to write, read and clear data using the Write-Gen-Counter present in APFS inodes.
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
        writes from instream to Write-Gen-Counter field in inodes.
        
		:param instream: typ.BinaryIO, stream containing data that is supposed to be hidden
		
		:returns: APFSWriteGenMetadata object
        """
        metadata = APFSWriteGenMetadata()
        instream = instream.read()

        if len(instream) > len(self.inodelist)*4:
            raise IOError("Not enough space available")

# Aufteilung des Instreams in Chunks der Größe der einzelnen Verstecke

        instream_chunks = [instream[i:i+4]for i in range (0, len(instream), 4)]

        hidden_chunks = 0
        i = 0
        # Chunks werden an durch InodeTable geschrieben. Hierfür wird die Submethode writeToPadding aufgerufen
        # Danach wird die Checksumme neu kalkuliert
        while hidden_chunks < len(instream_chunks):
            chunk = instream_chunks[hidden_chunks]
            writeaddress = self.inodelist[i][0] + self.inodelist[i][1]
            self.writeToPadding(writeaddress, chunk)
            metadata.add_inodeAddress(self.inodelist[i][0] + self.inodelist[i][1])
            hidden_chunks += 1
            self.stream.seek(self.inodelist[i][0]+8)
            data = self.stream.read(4088)
            chksm = self.calcChecksum(data)
            self.stream.seek(self.inodelist[i][0])
            metadata.add_nodeAddress(self.inodelist[i][0])
            self.stream.write(chksm)
            self.stream.seek(0)
            i+=1
        return metadata

    def read(self, outstream: typ.BinaryIO, metadata: APFSWriteGenMetadata):
        """
        reads from Write-Gen-Counter fields and writes found data to outstream.

        :param outstream: chosen stream to display found hidden data

        :param metadata: an APFSWriteGenMetadata object
        """
        inode_addresses = metadata.get_inodeAddresses()
        for adr in inode_addresses:
            outstream.write(self.readFromPadding(adr))


    def clear(self, metadata: APFSWriteGenMetadata):
        """
        clears hidden data from Write-Gen-Counter.

        :param metadata: an APFSWriteGenMetadata object
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
        """
        calculates offset of the Write-Gen-Counter field within an inode.

        :param a: an inode offset

        :returns: exact offset of the Write-Gen-Counter field within the inode
        """
        inodePadAdd = a + 64 


        return inodePadAdd


    def readFromPadding(self, address):
        """
        subfunction that reads a single Write-Gen-Counter field

        :param address: offset of an inode that contains a manipulated Write-Gen-Counter field

        :returns: data found in Write-Gen-Counter field
        """
        self.stream.seek(0)
        #standard version
        readAddress = self.getTotalOffset(address)
        # ext field test version
  #      readAddress = (9088 * 4096) + 4049
        self.stream.seek(readAddress)
#        data = self.stream.read(10)
        data = self.stream.read(4)

        return data


    def clearPadding(self, address):
        """
        subfunction that clears a single Write-Gen-Counter field

        :param address: offset of a Write-Gen-Counter field      
        """
        self.stream.seek(0)
        clearAddress = self.getTotalOffset(address)
        self.stream.seek(clearAddress)
        self.stream.write(b'\x00\x00\x00\x00')

    def writeToPadding(self, address, chunk):
        """
        subfunction that writes a 4 byte chunk of data to a single Write-Gen-Counter field

        :param address: offset of a single Write-Gen-Counter field

        :param chunk: 4 byte sized part of the data that is supposed to be hidden
        """
        self.stream.seek(0)
        writeAddress = self.getTotalOffset(address)
      
        self.stream.seek(writeAddress)
        self.stream.seek(writeAddress)
        self.stream.write(chunk)



