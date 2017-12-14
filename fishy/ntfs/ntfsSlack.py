"""
ntfs slack implementation
"""

import struct
from pytsk3 import FS_Info, Img_Info, TSK_FS_NAME_TYPE_DIR, TSK_FS_NAME_TYPE_REG


class FileSlackMetadata:
    """ meta data class for ntfs slack """
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
            
def is_fs_directory(file):
    """ Checks if an inode is a filesystem directory. """
    return file.info.name.type == TSK_FS_NAME_TYPE_DIR

def is_fs_regfile(file):
    """Checks if an inode is a regular file."""
    return file.info.name.type == TSK_FS_NAME_TYPE_REG


class SlackSpace:  # pylint: disable=too-few-public-methods
    """ class for slack space objects"""
    def __init__(self, size, addr):
        self.size = size
        self.addr = addr


class SlackFile:  # pylint: disable=too-few-public-methods
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
        self.info = False

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
            raise IOError("Not enough slack space")
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
        """ calculate slack size of file or mft entry in case of resident $Data attribute"""
        meta = file.info.meta
        if not meta:
            if self.info:
                print("\tError checking MFT entry of file")
            return 0
        #avoid ntfs meta files
        if file.info.meta.addr < 27:
            if self.info:
                print("\tSkipping NTFS metafile")
            return 0
        #if file.info.name.name.decode('utf-8').find("$") != -1:
        #    return 0
        # get last block of file to check for slack
        resident = True
        meta_block = file.info.meta.addr
        mftentry_size = 1024
        mft_offset = 16
        # File size
        size = file.info.meta.size
        meta_addr = (meta_block + mft_offset) * mftentry_size
        for attr in file:
            for run in attr:
                last_block_offset = run.len - 1
                last_blocks_start = run.addr
                resident = False
        # File data resident in mft $Data entry
        if resident:
            if self.info:
                print("\tFile is resident in MFT entry $Data attribute")
            stream = open(self.stream, 'rb+')
            #allocated size of mft entry
            stream.seek(meta_addr+28)
            mft_alloc_size = stream.read(4)
            mftalloc_sizedec = struct.unpack("<L", mft_alloc_size)[0]
            if self.info:
                print("\tMFT entry allocated size: %s"%mftalloc_sizedec)
            #get actual size of mft entry
            stream.seek(meta_addr+24)
            mft_entry_size = stream.read(4)
            mftentry_sizedec = struct.unpack("<L", mft_entry_size)[0]
            if self.info:
                print("\tMFT entry used size: %s"%mftentry_sizedec)
            #offset to slack in mft entry
            mftslack_start = meta_addr+mftentry_sizedec
            #write to mft entry after end of attributes
            #-2 at end to avoid overwriting fixup values
            mftslack_end = meta_addr+mftalloc_sizedec-2
            if mftentry_sizedec >= 512:
                mftslack_size = mftslack_end - mftslack_start
                self.slack_list.append(SlackSpace(mftslack_size, mftslack_start))
                if self.info:
                    print("\tMFT slack size(avoiding fixup value): %s"%mftslack_size)
                return mftslack_size
            mftslack_end1 = (mftslack_start + 512 - (mftslack_start % 512)) - 2
            mftslack_size1 = mftslack_end1 - mftslack_start
            self.slack_list.append(SlackSpace(mftslack_size1, mftslack_start))
            mftslack_size2 = mftslack_end - (mftslack_end1 + 2)
            self.slack_list.append(SlackSpace(mftslack_size2, mftslack_end1 + 2))
            if self.info:
                print("\tMFT slack size(avoiding fixup values): %s"
                      %(mftslack_size1 + mftslack_size2))
            return mftslack_size1 + mftslack_size2
        # last block = start of last blocks + offset
        last_block = last_blocks_start + last_block_offset
        blocknoram = self.blocksize - self.sectorsize
        # Actual file data in the last block
        l_d_size = size % self.blocksize
        if self.info:
            occ_blocks = int(l_d_size / self.sectorsize)
            if l_d_size % self.sectorsize > 0:
                occ_blocks += 1
            print("\tOccupied sectors in last cluster: %s"%occ_blocks)
        #skip ram slack
        size_in_ramslack = l_d_size % self.sectorsize
        ramslack_size = self.sectorsize - size_in_ramslack
        if self.info:
            print("\tRAM Slack: %s"%ramslack_size)
        if size_in_ramslack > 0:
            l_d_size += ramslack_size
        #skip file if data within last sector to avoid RAM slack
        if l_d_size == 0 or l_d_size >= blocknoram:
            return 0
        # Slack space size
        s_size = self.blocksize - l_d_size
        if self.info:
            print("\tDrive Slack: %s"%s_size)
            print("\tFile Slack: %s"%(ramslack_size+s_size))
        start_addr_slack = last_block * self.blocksize + l_d_size
        #print("%s slack found"%s_size)
        self.slack_list.append(SlackSpace(s_size, start_addr_slack))
        return s_size

    def get_file_slack(self, directory, indent=0):
        """ Iterate over directoy recursive and add slackspace until file size is reached """
        for file in directory:
            if self.filesize_left > 0:
                if is_fs_regfile(file):
                    if self.info:
                        print("File: %s"%file.info.name.name.decode("utf8"))
                    # if file: get slack of file and add slack to total slack size
                    slack_size = self.get_slack(file)
                    self.total_slacksize += slack_size
                    # subtract slacksize to stop if enough space was found
                    self.filesize_left -= slack_size
                # recurse into directories
                if is_fs_directory(file):
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
        hidden_file = SlackFile(file_id, length)
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
                hidden_file.loc_list.append(SlackSpace(length, slack.addr))
                break
            else:
                stream.write(input_file[pos:pos + slack.size])
                hidden_file.loc_list.append(SlackSpace(slack.size, slack.addr))
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

    def fill_slack_list(self):
        """ fill slack list with directory or single file """
        # look file slack
        for path in self.filepath:
            try:
                directory = self.fs_inf.open_dir(path)
                self.get_file_slack(directory)
            except OSError:
                if self.info:
                    print("File: %s"%path)
                file = self.fs_inf.open(path)
                self.get_file_slack_single_file(file)
        # look for volume slack?
