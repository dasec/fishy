# -*- coding: utf-8 -*-
from pytsk3 import FS_Info, Img_Info, TSK_FS_NAME_TYPE_DIR, TSK_FS_NAME_TYPE_REG


class FileSlackMetadata:
        """ meta data class for ntfs slack """
    def __init__(self, d=None):
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


class slackSpace:
        """ class for slack space objects"""
    def __init__(self, size, addr):
        self.size = size
        self.addr = addr


class fileLoc:
        """ class for single file location """
    def __init__(self, addr, size):
        self.size = size
        self.addr = addr


class fileInSlack:
        """ class file in slack with list of locations """
    def __init__(self, name, size, ):
        self.lockList = []
        self.name = name
        self.size = size


class NtfsSlack:
        """ class for ntfs slack operations """
    def __init__(self, stream):
        self.stream = stream
        self.instream = None
        # Open img file
        self.img = Img_Info(stream)
        # Open the filesystem
        self.fs = FS_Info(self.img, offset=0)
        # Get the blocksize
        self.blocksize = self.fs.info.block_size  # 4096
        # get sector size
        self.sectorsize = self.fs.info.dev_bsize  # 512
        # get cluster size
        self.cluster_size = self.blocksize / self.sectorsize  # 8
        self.slack_list = []
        self.total_slacksize = 0
        self.filesize_left = 0
        self.args = []
        self.input = ""
        self.filepath = ""

    def write(self, instream, filepath):
        """ write data to slack """
        self.instream = instream
        self.filepath = filepath
        # size of file to hide
        fileSize = self.get_file_size()
        # print ("filesize:%s"%fileSize)
        # fill list of slack space objects till file size is reached
        self.filesize_left = fileSize
        self.fill_slack_list()
        if fileSize > self.total_slacksize:
            raise Exception("Not enough slack space")
        # .ELF(7F 45 4C 46)
        print ("File hidden")
        hiddenfiles = self.write_file_to_slack()
        meta = self.createMetaData(hiddenfiles)
        return meta

    def createMetaData(self, hiddenfiles):
        """ create meta data object """
        m = FileSlackMetadata()
        for file in hiddenfiles:
            for loc in file.lockList:
                m.add_addr(loc.addr, loc.size)
        return m

    def read(self, outstream, meta):
        """ read hidden data from slack """
        stream = open(self.stream, 'rb+')
        for addr, length in meta.get_addr():
            stream.seek(addr)
            bufferv = stream.read(length)
            outstream.write(bufferv)

    def clear(self, meta):
        """ delete hidden data from slack """
        stream = open(self.stream, 'rb+')
        for addr, length in meta.get_addr():
            stream.seek(addr)
            stream.write(length * b'\x00')

    def get_slack(self, f):
        """ calculate slack size of file """
        meta = f.info.meta
        if not meta:
            return 0

        # get last block of file to check for slack
        resident = True
        metaBlock = f.info.meta.addr
        mftEntrySize = 1024
        mftOffset = 16
        mtfOffsetToData = 360
        # File size
        size = f.info.meta.size
        metaAddr = (metaBlock + mftOffset) * mftEntrySize
        for attr in f:
            for run in attr:
                last_block_offset = run.len - 1
                last_blocks_start = run.addr
                resident = False
        # File data resident in mft $Data entry
        if resident:
            offsetToSlack = mtfOffsetToData + size
            metaSlackStart = metaAddr + offsetToSlack
            metaFreeSlack = mftEntrySize - offsetToSlack
            self.slack_list.append(slackSpace(metaFreeSlack, metaSlackStart))
            return metaFreeSlack

        # last block = start of last blocks + offset
        last_block = last_blocks_start + last_block_offset

        # Actual file data in the last block
        l_d_size = size % self.blocksize

        # Slack space size
        s_size = self.blocksize - l_d_size

        start_addr_slack = last_block * self.blocksize + l_d_size
        # print("%s slack found"%s_size)
        self.slack_list.append(slackSpace(s_size, start_addr_slack))
        return s_size

    def is_fs_directory(self, f):
        """ Checks if an inode is a filesystem directory. """
        return f.info.name.type == TSK_FS_NAME_TYPE_DIR

    def is_fs_regfile(self, f):
        """Checks if an inode is a regular file."""
        return f.info.name.type == TSK_FS_NAME_TYPE_REG

    def get_file_slack(self, directory, indent=0):
        """ Iterate over directoy recursive and add slackspace until file size is reached """
        for f in directory:
            if self.filesize_left > 0:
                if(self.is_fs_regfile(f)):
                    # if file: get slack of file and add slack to total slack size
                    slackSize = self.get_slack(f)
                    self.total_slacksize += slackSize
                    # subtract slacksize to stop if enough space was found
                    self.filesize_left -= slackSize
                # recurse into directories
                if(self.is_fs_directory(f)):
                    try:
                        d = f.as_directory()
                        if f.info.name.name != b'.' and f.info.name.name != b'..':
                            self.get_file_slack(d, indent + 1)
                    except RuntimeError:
                        print ('RunError!')
                    except IOError:
                        print ("IOError while opening %s" % (f.info.name.name))

    def get_file_slack_single_file(self, file):
        """ get slack size of single file"""
        if self.filesize_left > 0:
            slackSize = self.get_slack(file)
            self.total_slacksize += slackSize
            self.filesize_left -= slackSize

    def write_file_to_slack(self):
        """ write a file in found slack """
        hiddenFiles = []
        # read file
        inputFile = self.input
        length = len(inputFile)
        # position for input file partitioning
        pos = 0
        # random id for file metadata
        fileID = "123"
        # create hidden file object with id and length
        hiddenFile = fileInSlack(fileID, length)
        # open image
        stream = open(self.stream, 'rb+')
        # iterate over list of slackspace
        for s in self.slack_list:
            # go to address of free slack
            stream.seek(s.addr)
            # write file to slack space, set position and add a location to the hidden files location list
            if s.size >= length:
                stream.write(inputFile[pos:pos + length])
                hiddenFile.lockList.append(fileLoc(s.addr, length))
                break
            else:
                stream.write(inputFile[pos:pos + s.size])
                hiddenFile.lockList.append(fileLoc(s.addr, s.size))
                pos += s.size
                length -= s.size
        stream.flush
        stream.close
        self.instream.close
        # write meta data
        # self.write_info_file(hiddenFile)
        # add hidden file object to list of hidden files
        hiddenFiles.append(hiddenFile)
        return hiddenFiles

    def get_file_size(self):
        """ get size of file to hide """
        if len(self.args) > 0:
            length = 0
            # get size of all files
            for arg in self.args:
                inputStream = open(arg, "rb")
                inputFile = inputStream.read()
                inputStream.close()
                length += len(inputFile)
            return length
        else:
            self.input = self.instream.read()
            length = len(self.input)
            return length



            #    def get_Volume_Slack(self):
            #        #TODO do
            #        selectedPartition = None
            #        #find partition by offset
            #        for partition in volume:
            #            if partition.start == options.offset:
            #                selectedPartition = partition
            #                break
            #        #free sectors after filesystem(+1 for copy of boot sector)
            #        freeSectors = selectedPartition.len - (fs.info.block_count+1)*cluster_size
            #        print ("free Sectors:%s"%freeSectors )
            #        #get address of first free sector
            #        firstFreeSectorAddr = (fs.info.last_block+2)*blocksize
            #        fileSytemSlackSize = freeSectors*sectorsize
            #        print ("File System Slack: %s - %s(%s)"%(firstFreeSectorAddr,firstFreeSectorAddr+fileSytemSlackSize,fileSytemSlackSize))
            #        #create slack space object and append to list
            #        slack_list.append(slackSpace(fileSytemSlackSize,firstFreeSectorAddr))
            #        #set the total slack size
            #        self.total_slacksize += fileSytemSlackSize

    def fill_slack_list(self):
        """ fill slack list with directory or single file """
        # look file slack
        for path in self.filepath:
            try:
                directory = self.fs.open_dir(path)
                self.get_file_slack(directory)
            except OSError:
                file = self.fs.open(path)
                self.get_file_slack_single_file(file)
                # look for volume slack?

# if options.slack == "volume":
#            get_Volume_Slack()
