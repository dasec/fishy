import struct
import typing
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

        :param addr: int, address of cluster
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


class BadCluster:  
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
    def __init__(self, path, stream: typing.BinaryIO):
        """
        :param path: path to NTFS filesystem
        :param stream: opened stream of NTFS filesystem
        """
        self.stream = stream
        self.instream = None
        # Open img file
        self.img = Img_Info(path)
        # Open the filesystem
        self.fs_inf = FS_Info(self.img, offset=0)
        # Get the blocksize
        self.blocksize = self.fs_inf.info.block_size  # 4096
        # get sector size
        self.sectorsize = self.fs_inf.info.dev_bsize  # 512
        # get cluster size
        self.cluster_size = self.blocksize / self.sectorsize  # 8
        #default values, will be updated from boot record later
        self.mftentry_size = 1024
        self.mft_start = 4 * self.blocksize
        self.mft_badclus = 32768 
        self.mft_bitmap = 24576

    def write(self, instream):
        """
        find next free cluster in instream and write into it

        :param instream: stream to read from

        :raise IOError: Raises IOError if the file was too big or no input was provided.

        :return: BadClusterMetadata
        """
        self.instream = instream
        #get mft record size
    #    with open(self.stream, 'rb+') as mftstream:
        self.stream.seek(4*16)
        mftentry_size_b = self.stream.read(1)
        mftentry_size_i = struct.unpack("<b", mftentry_size_b)[0]
        if mftentry_size_i < 0:
            self.mftentry_size = 2**(mftentry_size_i*-1)
        else:
            self.mftentry_size = mftentry_size_i * self.cluster_size
        #get mft cluster
   #     with open(self.stream, 'rb+') as mftstream:
        self.stream.seek(self.mft_start * 16)
        mft_cluster_b = self.stream.read(8)
        mft_cluster = struct.unpack("<q", mft_cluster_b)[0]
        self.mft_start = mft_cluster * self.blocksize
        # figure out position of $bitmap and $badclus location
        self.mft_badclus = self.mft_start + self.blocksize * 8
        self.mft_bitmap = self.mft_start + self.blocksize * 6
        # size of file to hide
        file_size = self.get_file_size()
        if file_size < 0:
            raise IOError("No Input")

        # determine clusters needed 
        cluster_count = int((file_size / self.sectorsize))
        # find position of next available cluster
        clusters = []
   #     with open(self.stream, 'rb+') as mftstream:
            # start after mft
        it = 17
        while cluster_count > -1:
            self.stream.seek(self.mft_bitmap + it)
            cluster = self.stream.read(1)
            if (cluster == b'\x00'):
                clusters.append(it)
                cluster_count = cluster_count - 1
            it = it + 1
        if (len(clusters) < cluster_count):
            print("not enough free cluster found.")
        else:
            hidden_data = []
            for cluster in clusters:
                data = self.write_file_to_cluster(instream, int(cluster * self.cluster_size))
           #     with open(self.stream, 'rb+') as mftstream:
                # do not overwrite header
                self.stream.seek(self.mft_badclus + 7)
                # write cluster into $badclus
                self.stream.write(cluster.to_bytes(1, byteorder='big'))
                self.stream.seek(self.mft_badclus)
                # set used in $bitmap
                self.stream.seek(self.mft_bitmap + cluster)
                self.stream.write(b'\x01')
            print("data hidden")
            hidden_data.append(data)
            meta = self.create_metadata(hidden_data)
            return meta

    def write_file_to_cluster(self, instream, offset):
        """
        write a file into position of offset

        :return: BadCluster object to generate metadata with
        """
        # read file
        input_file = self.input
        length = len(input_file)
        # open image
        self.stream.seek(offset)
        # write file to cluster, save position and size to var
        self.stream.write(input_file)
        hidden_data = BadCluster(length, offset)
        return hidden_data

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

    def create_metadata(self, hidden_data):
        """
        create metadata object from BadCluster objects returned from write_file_to_cluster()

        :param hiddenfile: BadCluster objects returned from write_file_to_cluster()
        :return: BadClusterMetadata object
        """
        print("Creating metadata:")
        meta = BadClusterMetadata()
        for cluster in hidden_data:
            meta.add_addr(cluster.size, cluster.addr)
            print("\thid %sb of data starting at address %s"%(cluster.size, cluster.addr))
        return meta

    def read(self, outstream, meta):
        """
        writes bad clusters into outstream

        :param outstream: stream to write into
        :param meta: BadClusterMetadata object
        """
        for length, addr in meta.get_addr():
            self.stream.seek(addr)
            bufferv = self.stream.read(length)
            outstream.write(bufferv)


    def clear(self, meta: BadClusterMetadata):
        """
        clears the bad clusters specified by metadata, removes entries in $badclus and frees space in $bitmap

        :param meta: BadClusterMetadata object
        """
        for length, addr in meta.get_addr():
            self.stream.seek(addr)
            self.stream.write(length * b'\x00')
            it = 0
            bitmap = self.stream.seek(self.mft_bitmap + int(addr / self.cluster_size))
            self.stream.write(b'\x00')
            while it < self.mftentry_size:
                self.stream.seek(self.mft_badclus + it)
                badclus = self.stream.read(1)
                if badclus == addr.to_bytes(1, byteorder='big'):
                    self.stream.write(b'\x00')
                    print("removed hidden data")
                    break;
                it = it + 1         

