import typing as typ
from pytsk3 import FS_Info, Img_Info, TSK_FS_META_TYPE_DIR, TSK_FS_META_TYPE_REG

from fishy.ext4.ext4_filesystem.EXT4 import EXT4


class Ext4FileSlackMetadata:
    """
    meta data class for ext4 Fileslack, holds addresses and length of saved data
    """

    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of a FileSlackMetadata
                  object
        """
        if d is None:
            self.addrs = []
        else:
            self.addrs = d["addrs"]

    def add_addr(self, addr, length):
        """
        adds an address to the list of addresses

        :param address: int, start of slack
        
		:param length: int, length of the data, which was written
                       to fileslack
        """
        self.addrs.append((addr, length))

    def get_addr(self):
        """
        iterator for addresses

        :returns: iterator, that returns address, length
        """
        for addr in self.addrs:
            yield addr[0], addr[1]


class EXT4FileSlack:
    """ class for ext4 fileslack operqations"""

    def __init__(self, stream: typ.BinaryIO, dev: str):
        """
        :param dev: path to an ext4 filesystem
        
		:param stream: filedescriptor of an ext4 filesystem
        """
        self.dev = dev
        self.stream = stream
        self.ext4fs = EXT4(stream, dev)
        self.img = Img_Info(dev)
        self.fs_inf = FS_Info(self.img)

    def write(self, instream: typ.BinaryIO, filepaths: typ.List[str]) \
            -> Ext4FileSlackMetadata:
        """
        writes from instream into Fileslack of files passed in filepaths
        
		:param instream: stream to read from
        
		:param filepaths: list of strings, path to files or directories containing files which slackspace will be used
        
		:return: Ext4FileSlackMetadata
        """
        meta = Ext4FileSlackMetadata()
        if filepaths is None:
            filepaths = ["/"]
        slackspace = self.get_Slackspace_list(filepaths)
        for address in slackspace:
            if instream.peek():
                space = address[1]
                buf = instream.read(space)
                self.stream.seek(address[0])
                self.stream.write(buf)
                meta.add_addr(address[0], len(buf))
            else:
                break;
        if instream.peek():
            raise IOError("No slackspace left to write data to, but there are"
                          + " still %d Bytes in stream" % len(instream.read()))
        return meta

    def read(self, outstream: typ.BinaryIO, metadata: Ext4FileSlackMetadata) \
            -> None:
        """
        writes data hidden in Fileslack into outstream
        
		:param outstream: stream to write into
        
		:param metadata: Ext4FileSlackMetadata object
        """
        for address, length in metadata.get_addr():
            self.stream.seek(address)
            buf = self.stream.read(length)
            outstream.write(buf)

    def clear(self, metadata: Ext4FileSlackMetadata) -> None:
        """
        clears fileslack in which data has been hidden
        
		:param metadata: Ext4FileSlackMetadata object
        """
        for address, length in metadata.get_addr():
            self.stream.seek(address)
            self.stream.write(length * b'\x00')

    def info(self, filepaths):
        """
        prints avaible slackspace
        
		:param filepaths: list of strings, path to files or directories containing files which slackspace will be used
        
		:return: amount of slackspace
        """
        if filepaths is None:
            filepaths = ["/"]
        slackspace = self.get_Slackspace_list(filepaths)
        space = 0
        for address in slackspace:
            space += address[1]
        print("Total slackspace:%s Bytes" % space)

    def get_Slackspace_list(self, filepaths):
        """
        creates a list of the location of slackspace
        
		:param filepaths: list of strings, path to files or directories containing files which slackspace will be used
        
		:return: list containing physical addresses and length of slackspace
        """
        filelist = list()
        slackspace = list()
        # create a list of files that are passed by the user or located in directories passed by the user
        for path in filepaths:
            try:
                file = self.fs_inf.open(path)
                if file.info.meta.type == TSK_FS_META_TYPE_DIR:
                    filelist = filelist + (self.get_dir_content(file.as_directory()))
                elif file.info.meta.type == TSK_FS_META_TYPE_REG:
                    filelist.append(file)
            except OSError:
                print("Cant open " + path)
        # locate slackspace for every file in the list
        for file in filelist:
            size = file.info.meta.size
            for attr in file:
                for run in attr:
                    if run.len * self.ext4fs.blocksize > size:
                        slackstart = run.addr * self.ext4fs.blocksize + size
                        slackend = (run.addr + run.len) * self.ext4fs.blocksize - 1
                        length = slackend - slackstart + 1
                        # check for duplicates
                        if [slackstart, length] not in slackspace:
                            slackspace.append([slackstart, length])
        return slackspace

    def get_dir_content(self, dir):
        """
        lists all files contained in a given directory, recursively entering subdirectories
        
		:param dir: pytsk3 directory object
        
		:return: list of pytsk3 file objects
        """
        filelist = []
        for file in dir:
            if file.info.name.name != b'.' and file.info.name.name != b'..':
                if file.info.meta.type == TSK_FS_META_TYPE_DIR:  # directory
                    filelist = filelist + (self.get_dir_content(file.as_directory()))
                elif file.info.meta.type == TSK_FS_META_TYPE_REG:  # regular file
                    filelist.append(file)
        return filelist
