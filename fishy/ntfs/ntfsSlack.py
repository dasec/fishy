"""
ntfs slack implementation
"""

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


class slack_space:
    """ class for slack space objects"""
    def __init__(self, size, addr):
        self.size = size
        self.addr = addr


class file_loc:
    """ class for single file location """
    def __init__(self, addr, size):
        self.size = size
        self.addr = addr


class slack_file:
    """ class file in slack with list of locations """
    def __init__(self, name, size, ):
        self.loc_list = []
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
        self.fs_inf = FS_Info(self.img, offset=0)
        # Get the blocksize
        self.blocksize = self.fs_inf.info.block_size  # 4096
        # get sector size
        self.sectorsize = self.fs_inf.info.dev_bsize  # 512
        # get cluster size
        self.cluster_size = self.blocksize / self.sectorsize  # 8
        self.slack_list = []
        self.total_slacksize = 0
        self.filesize_left = 0
        self.input = ""
        self.filepath = ""

    def write(self, instream, filepath):
        """ write data to slack """
        self.instream = instream
        self.filepath = filepath
        # size of file to hide
        file_size = self.get_file_size()
        # fill list of slack space objects till file size is reached
        self.filesize_left = file_size
        self.fill_slack_list()
        if file_size > self.total_slacksize:
            raise Exception("Not enough slack space")
        # .ELF(7F 45 4C 46)
        print("File hidden")
        hiddenfiles = self.write_file_to_slack()
        meta = self.create_metadata(hiddenfiles)
        return meta

    def create_metadata(self, hiddenfiles):
        """ create meta data object """
        meta = FileSlackMetadata()
        for file in hiddenfiles:
            for loc in file.loc_list:
                meta.add_addr(loc.addr, loc.size)
        return meta

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

    def get_slack(self, file):
        """ calculate slack size of file """
        meta = file.info.meta
        if not meta:
            return 0
        #file.info.meta.mode==365???
        if file.info.name.name.decode('utf-8').find("$") != -1:
            return 0

        # get last block of file to check for slack
        resident = True
        meta_block = file.info.meta.addr
        mftentry_size = 1024
        mft_offset = 16
        mftoffset_todata = 360
        # File size
        size = file.info.meta.size
        meta_addr = (meta_block + mft_offset) * mftentry_size
        #avoid special files
        for attr in file:
            for run in attr:
                last_block_offset = run.len - 1
                last_blocks_start = run.addr
                resident = False
        # File data resident in mft $Data entry
        if resident:
            offsetto_slack = mftoffset_todata + size
            metaslack_start = meta_addr + offsetto_slack
            meta_freeslack = mftentry_size - offsetto_slack
            self.slack_list.append(slack_space(meta_freeslack, metaslack_start))
            return meta_freeslack

        # last block = start of last blocks + offset
        last_block = last_blocks_start + last_block_offset
        
        blocknoram = self.blocksize - self.sectorsize
        # Actual file data in the last block
        l_d_size = size % self.blocksize
        
        #skip ram slack
        size_in_ramslack = l_d_size % self.sectorsize
        if size_in_ramslack > 0:
            l_d_size += self.sectorsize - size_in_ramslack
        
        #skip file if data within last sector to avoid RAM slack
        if l_d_size == 0 or l_d_size >= blocknoram:
            return 0
        
        # Slack space size
        s_size = self.blocksize - l_d_size

        start_addr_slack = last_block * self.blocksize + l_d_size
        # print("%s slack found"%s_size)
        self.slack_list.append(slack_space(s_size, start_addr_slack))
        return s_size

    def is_fs_directory(self, file):
        """ Checks if an inode is a filesystem directory. """
        return file.info.name.type == TSK_FS_NAME_TYPE_DIR

    def is_fs_regfile(self, file):
        """Checks if an inode is a regular file."""
        return file.info.name.type == TSK_FS_NAME_TYPE_REG

    def get_file_slack(self, directory, indent=0):
        """ Iterate over directoy recursive and add slackspace until file size is reached """
        for file in directory:
            if self.filesize_left > 0:
                if self.is_fs_regfile(file):
                    # if file: get slack of file and add slack to total slack size
                    slack_size = self.get_slack(file)
                    self.total_slacksize += slack_size
                    # subtract slacksize to stop if enough space was found
                    self.filesize_left -= slack_size
                # recurse into directories
                if self.is_fs_directory(file):
                    try:
                        direc = file.as_directory()
                        if file.info.name.name != b'.' and file.info.name.name != b'..':
                            self.get_file_slack(direc, indent + 1)
                    except RuntimeError:
                        print('RunError!')
                    except IOError:
                        print("IOError while opening %s" % (file.info.name.name))

    def get_file_slack_single_file(self, file):
        """ get slack size of single file"""
        if self.filesize_left > 0:
            slack_size = self.get_slack(file)
            self.total_slacksize += slack_size
            self.filesize_left -= slack_size

    def write_file_to_slack(self):
        """ write a file in found slack """
        hidden_files = []
        # read file
        input_file = self.input
        length = len(input_file)
        # position for input file partitioning
        pos = 0
        # random id for file metadata
        file_id = "123"
        # create hidden file object with id and length
        hidden_file = slack_file(file_id, length)
        # open image
        stream = open(self.stream, 'rb+')
        # iterate over list of slackspace
        for slack in self.slack_list:
            # go to address of free slack
            stream.seek(slack.addr)
            # write file to slack space, set position and 
            # add a location to the hidden files location list
            if slack.size >= length:
                stream.write(input_file[pos:pos + length])
                hidden_file.loc_list.append(file_loc(slack.addr, length))
                break
            else:
                stream.write(input_file[pos:pos + slack.size])
                hidden_file.loc_list.append(file_loc(slack.addr, slack.size))
                pos += slack.size
                length -= slack.size
        # stream.flush
        # stream.close
        # self.instream.close
        # write meta data
        # self.write_info_file(hidden_file)
        # add hidden file object to list of hidden files
        hidden_files.append(hidden_file)
        return hidden_files

    def get_file_size(self):
        """ get size of file to hide """
        self.input = self.instream.read()
        length = len(self.input)
        return length



            #    def get_Volume_Slack(self):
            #        selectedPartition = None
            #        #find partition by offset
            #        for partition in volume:
            #            if partition.start == options.offset:
            #                selectedPartition = partition
            #                break
            #        #free sectors after filesystem(+1 for copy of boot sector)
            #        freeSectors = selectedPartition.len - (fs_inf.info.block_count+1)*cluster_size
            #        print ("free Sectors:%s"%freeSectors )
            #        #get address of first free sector
            #        firstFreeSectorAddr = (fs_inf.info.last_block+2)*blocksize
            #        fileSytemSlackSize = freeSectors*sectorsize
            #        print ("File System Slack: %s - %s(%s)"
            #        %(firstFreeSectorAddr,firstFreeSectorAddr+fileSytemSlackSize,fileSytemSlackSize))
            #        #create slack space object and append to list
            #        slack_list.append(slack_space(fileSytemSlackSize,firstFreeSectorAddr))
            #        #set the total slack size
            #        self.total_slacksize += fileSytemSlackSize

    def fill_slack_list(self):
        """ fill slack list with directory or single file """
        # look file slack
        for path in self.filepath:
            try:
                directory = self.fs_inf.open_dir(path)
                self.get_file_slack(directory)
            except OSError:
                file = self.fs_inf.open(path)
                self.get_file_slack_single_file(file)
                # look for volume slack?

# if options.slack == "volume":
#            get_Volume_Slack()
