import struct
import os
from pytsk3 import FS_Info, Img_Info 

class BadClusterMetadata:
""" meta data class for ntfs bad cluster """
    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of a MftClusterMetadata
                  object
        """
        if d is None:
            self.addrs = []
        else:
            self.addrs = d["addrs"]

    def add_addr(self, addr, length):
        """
        adds an address to the list of addresses

        :param address: int, start of cluster
        :param length: int, length of the data written into cluster
        """
        self.addrs.append((addr, length))

    def get_addr(self):
        """
        iterator for addresses

        :returns: iterator, that returns address, length
        """
        for addr in self.addrs:
            yield addr[0], addr[1]


class BadCluster:  # pylint: disable=too-few-public-methods
    """ class to save bad cluster space start and size"""
    def __init__(self, size, addr):
        """
        :param size: size of bad cluster
        :param addr: start of bad cluster
        """
        self.size = size
        self.addr = addr

class NtfsBadCluster:
""" class for ntfs mft cluster operations """
    def __init__(self, stream):
        """
        :param stream: path to NTFS filesystem
        """
        self.stream = stream
        self.instream = None
        # Open img file
        self.img = Img_Info(stream)
        # Open the filesystem
        self.fs_inf = FS_Info(self.img, offset=0)
        # Get the blocksize
        self.blocksize = self.fs_inf.info.block_size  # 4096
        # get sector size
        self.sectorsize = self.fs_inf.info.dev_bsize  # 512
        # get cluster size
        self.cluster_size = self.blocksize / self.sectorsize  # 8
        self.fs_size = os.stat(self.stream).st_size
        #only default. actual value will be read from boot record later
        self.mftentry_size = 1024
        #only default. actual value will be read from boot record later
        self.mft_start = 4 * self.blocksize
        #position of $badclus, $bitmap metadata file
        self.mft_badclus = -1
        self.mft_bitmap = -1

    def write(self, instream, offset=0):
        """
        find next free cluster in instream and write into it

        :param instream: stream to read from
        :param offset: offset to write to

        :raise IOError: Raises IOError if the file was too big or no input was provided.

        :return: BadClusterMetadata
        """
        #get mft record size
        with open(self.stream, 'rb+') as mftstream:
            mftstream.seek(4*16)
            mftentry_size_b = mftstream.read(1)
            mftentry_size_i = struct.unpack("<b", mftentry_size_b)[0]
            if mftentry_size_i < 0:
                self.mftentry_size = 2**(mftentry_size_i*-1)
            else:
                self.mftentry_size = mftentry_size_i * self.cluster_size
        #get mft cluster
        with open(self.stream, 'rb+') as mftstream:
            mftstream.seek(self.mft_start * 16)
            mft_cluster_b = mftstream.read(8)
            mft_cluster = struct.unpack("<q", mft_cluster_b)[0]
            self.mft_start = mft_cluster * self.blocksize
            # todo: figure out position of $bitmap and $badclus location
            self.mft_badclus = mft_start + self.blocksize * 8
            self.mft_bitmap = mft_start + self.blocksize * 6
        self.instream = instream
        # size of file to hide
        file_size = self.get_file_size()
        if file_size < 0:
            raise IOError("No Input")

        # find position of next available cluster
        offset = -1
        with open(self.stream, 'rb+') as mftstream:
            it = 0
            cluster = mftstream.seek(mft_bitmap + it)
            if (cluster == b'\x00')
                offset = cluster
                break
            it = it + 1
        if offset != -1:
            # todo: write data into cluster
            hiddenfile = self.write_file_to_cluster(offset * self.clustersize)
            print("File hidden")
            # todo: write cluster into $badclus
            mftstream.seek(self.mft_badclus)
            mftstream.write(b'\x00')
            # todo: set cluster in $bitmap to used
            mftstream.seek(mft)
            mftstream.write(b'\x01')
            meta = self.create_metadata(hiddenfile)
            return meta
        print("no free cluster found.")

    def write_file_to_cluster(self, offset):
        """
        write a file into position of offset

        :return: BadClusterFile to generate metadata with
        """
        # read file
        input_file = self.input
        length = len(input_file)
        # open image
        stream = open(self.stream, 'rb+')
        stream.seek(offset)
        # write file to cluster, save position and size to data
        stream.write(input_file[length])
        hidden_file = BadCluster(offset, length)
        return hidden_file

    def get_file_size(self):
        """
        get size of file to hide

        :return: size of file to hide. -1 if no input was provided.
        """
        if not self.instream.isatty():
            self.input = self.instream.read()
            length = len(self.input)
            return length
        return -1

    def create_metadata(self, hiddenfile):
        """
        create metadata object from BadCluster object returned from write_file_to_cluster()

        :param hiddenfile: BadCluster object returned from write_file_to_cluster()
        :return: BadClusterMetadata object
        """
        if self.info:
            print("Creating metadata:")
        meta = BadClusterMetadata()
        for file in hiddenfile:
            if self.info:
                print("\thid %sb of data at offset %s"%(self.size, self.addr))
                meta.add_addr(loc.addr, loc.size)
        return meta

    def read(self, outstream, meta):
        """
        writes bad clusters into outstream

        :param outstream: stream to write into
        :param meta: BadClusterMetadata object
        """
        stream = open(self.stream, 'rb+')
        for addr, length in meta.get_addr():
            stream.seek(addr)
            bufferv = stream.read(length)
            outstream.write(bufferv)

    def clear(self, meta):
        """
        clears the bad clusters specified by metadata, removes entries in $badclus and frees space in $bitmap

        :param meta: BadClusterMetadata object
        """
        stream = open(self.stream, 'rb+')
        for addr, length in meta.get_addr():
            stream.seek(addr)
            stream.write(length * b'\x00')
        with open(self.stream, 'rb+') as mftstream:
            it = 0
            for addr in meta.get_addr():
                bitmap = mftstream.seek(self.mft_bitmap + addr)
                mftstream.write(b'\x00')
                while it < mftentry_size:
                    badclus = mftstream.seek(self.mft_badclus + it)
                    if badclus == addr:
                        mftstream.write(b'\x00')
                        break;
                    it = it + 1

