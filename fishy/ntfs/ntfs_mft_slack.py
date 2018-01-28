"""
NtfsMftSlack offers methods to read, write and
clear the slackspace of MFT records

It will start with the mft entry at the given sector offset
and calculate the slack of every entry until the provided data
can be hidden or no more mft enries are left. After data was hidden
successfully it will print out the next position to be used as offset
when trying to hide more data. Without this offset previously
hidden data will be overwritten. If domirr is set to True a copy
of the data will be written to the respective entries in the $MFTMirr.
This will avoid detection by chkdsk. Fixup values will not be overwritten to
avoid damaging the mft entries.


:Example:

>>> mft_slack = NtfsMftSlack('/dev/sdb1')

to write something from stdin into slack:

>>> metadata = mft_slack.write(sys.stdin.buffer)

to write something from stdin into slack with offset:

>>> metadata = mft_slack.write(sys.stdin.buffer, 34)

to read something from slack to stdout:

>>> mft_slack.read(sys.stdout.buffer, metadata)

to wipe hidden data from slackspace:

>>> mft_slack.clear(metadata)

to display info about the mft slack:

>>> mft_slack.info()
"""

import struct
from pytsk3 import FS_Info, Img_Info  # pylint: disable=no-name-in-module


class MftSlackMetadata:
    """ meta data class for ntfs slack """
    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of a MftSlackMetadata
                  object
        """
        if d is None:
            self.addrs = []
        else:
            self.addrs = d["addrs"]

    def add_addr(self, addr, length, mirr):
        """
        adds an address to the list of addresses

        :param address: int, start of slack
        :param length: int, length of the data, which was written
                       to fileslack
        """
        self.addrs.append((addr, length, mirr))

    def get_addr(self):
        """
        iterator for addresses

        :returns: iterator, that returns address, length
        """
        for addr in self.addrs:
            yield addr[0], addr[1], addr[2]

class SlackSpace:  # pylint: disable=too-few-public-methods
    """ class to save slack space start and size"""
    def __init__(self, size, addr, mirr = None):
        """
        :param size: size of slack space
        :param addr: start of slack space
        """
        self.size = size
        self.addr = addr
        self.mirr = mirr


class SlackFile:  # pylint: disable=too-few-public-methods
    """ class to save info about hidden file """
    def __init__(self, name, size):
        """
        :param name: name of file
        :param size: size of file
        """
        self.loc_list = []
        self.name = name
        self.size = size


class NtfsMftSlack:
    """ class for ntfs mft slack operations """
    def __init__(self, path, stream):
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
        self.slack_list = []
        self.total_slacksize = 0
        self.filesize_left = 0
        self.input = ""
        self.info = False
        #only default. actual value will be read from boot record later
        self.mftentry_size = 1024
        #only default. actual value will be read from boot record later
        self.mft_start = 4 * self.blocksize
        #store mft data blocks in here
        self.mft_data = []
        #store mftmirr data blocks in here
        self.mftmirr_data = []
        #write same data to mftmirr or not
        self.domirr = False
        #only default. actual value will be read later
        self.mftmirr_size = self.mftentry_size * 4

    def write(self, instream, mft_offset=0):
        """
        creates list with slack space starting at the provided offset
        and writes from instream into slackspace.

        :param instream: stream to read from
        :param mft_offset: first sector of mft entry to start with

        :raise IOError: Raises IOError if not enough slack was found to hide
                        data or no input was provided.

        :return: MftSlackMetadata
        """
        #get mft record size
        self.stream.seek(4*16)
        mftentry_size_b = self.stream.read(1)
        mftentry_size_i = struct.unpack("<b", mftentry_size_b)[0]
        if mftentry_size_i < 0:
            self.mftentry_size = 2**(mftentry_size_i*-1)
        else:
            self.mftentry_size = mftentry_size_i * self.cluster_size
        #get mft cluster
        self.stream.seek(3*16)
        mft_cluster_b = self.stream.read(8)
        mft_cluster = struct.unpack("<q", mft_cluster_b)[0]
        self.mft_start = mft_cluster * self.blocksize
        self.instream = instream
        # size of file to hide
        file_size = self.get_file_size()
        if file_size < 0:
            raise IOError("No Input")
        # fill list of slack space objects till file size is reached
        self.filesize_left = file_size
        self.fill_slack_list(mft_offset)
        if file_size > self.total_slacksize:
            raise IOError("Not enough slack space")
        # .ELF(7F 45 4C 46)
        hiddenfiles = self.write_file_to_slack()
        print("File hidden")
        meta = self.create_metadata(hiddenfiles)
        return meta

    def fill_slack_list(self, mft_offset=0, mft_limit=-1):
        """
        fill slack list with slack of mft entries starting at offset

        :param mft_offset: first sector of mft entry to start with.
        :param mft_limit: number of mft entries to get slack of. -1 for infinte.
                            only used for print_info.
        """
        #get the necessary info about the mft data runs
        self.get_mft_info(mft_offset)
        num = 0
        # look for mft slack
        for mft_d in self.mft_data:
            mft_end = mft_d[1]
            mft_cursor = mft_d[0]
            mftmirr_offset = None
            if self.domirr:
                mftmirr_start = self.mftmirr_data[num][0]
                mftmirr_offset = mftmirr_start - mft_cursor
            num += 1
            while mft_cursor < mft_end:
                if self.filesize_left > 0:
                    slack_size, mft_cursor = self.get_mft_slack(mft_cursor, self.stream, mftmirr_offset)
                    if slack_size < 0:
                        return
                    self.total_slacksize += slack_size
                    # subtract slacksize to stop if enough space was found
                    self.filesize_left -= slack_size
                else:
                    print("Next position: %s"%int(mft_cursor/self.sectorsize))
                    return
                if mft_limit > 0:
                    mft_limit = mft_limit - 1
                    if mft_limit == 0:
                        return

    def get_mft_info(self, mft_cursor=0, mirr = False):
        """
        get info about data runs of $MFT and $MFTMirr file and save it in self.mft_data to
        use when filling the slacklist.

        :param mft_cursor: first sector of mft entry to start with
        :param mirr: wheter to same for do $MFTMirr or not
        """
        if mirr:
            mft = self.fs_inf.open("$MFTMirr")
            self.mftmirr_size = mft.info.meta.size
        else:
            mft = self.fs_inf.open("$MFT")
        mft_cursor = mft_cursor*self.sectorsize
        if self.info:
            print("$MFT info:")
        for attr in mft:
            for run in attr:
                #get start of mft data runs and store in list
                mft_start_end = []
                mft_start = run.addr*self.blocksize
                mft_end = (run.addr+run.len)*self.blocksize
                #skip to start provided
                if mft_cursor > mft_start and mft_cursor < mft_end:
                    mft_start = mft_cursor
                mft_start_end.append(mft_start)
                mft_start_end.append(mft_end)
                if mirr:
                    self.mftmirr_data.append(mft_start_end)
                else:
                    self.mft_data.append(mft_start_end)
                if self.info:
                    print("\tdata run start: %s"%run.addr)
                    print("\tdata run length: %s"%run.len)
                    print("\t(%s - %s)"%(run.addr*self.blocksize,
                                         (run.addr+run.len)*self.blocksize))
        if self.domirr:
            if mirr is False:
                self.get_mft_info(mft_cursor, True)

    def get_mft_slack(self, mft_cursor, stream, mirr_offset = None):
        """
        calculate mft slack size of mft entry at a specific starting point

        :param mft_cursor: start of mft_entry
        :param stream: stream to read from
        :param mirr_offset: offset to $MFTMirr
        :return: size of mft slack and start of next mft entry. -1 if at end of MFT.
        """
        #check if there is an mft entry
        stream.seek(mft_cursor+0)
        mft_alloc_size = stream.read(4)
        mftalloc_sizedec = struct.unpack("<4s", mft_alloc_size)[0]
        #raise error if end was reached
        if mftalloc_sizedec == b'\x00\x00\x00\x00':
            if self.info:
                print("End of MFT: %s"%mft_cursor)
            return -1, -1
        if self.info:
            print("MFT record signature: %s"%mftalloc_sizedec)
            print("\tOffset to start here: %s"%int(mft_cursor/self.sectorsize))
        #allocated size of mft entry
        stream.seek(mft_cursor+28)
        mft_alloc_size = stream.read(4)
        mftalloc_sizedec = struct.unpack("<L", mft_alloc_size)[0]
        if self.info:
            print("\tMFT entry allocated size: %s"%mftalloc_sizedec)
        #get actual size of mft entry
        stream.seek(mft_cursor+24)
        mft_entry_size = stream.read(4)
        mftentry_sizedec = struct.unpack("<L", mft_entry_size)[0]
        if self.info:
            print("\tMFT entry used size: %s"%mftentry_sizedec)
        #offset to slack in mft entry
        mftslack_start = mft_cursor+mftentry_sizedec
        #write to mft entry after end of attributes
        #-2 at end to avoid overwriting fixup values
        mftslack_end = mft_cursor+mftalloc_sizedec-2
        if mftentry_sizedec >= self.sectorsize:
            mftslack_size = mftslack_end - mftslack_start
            if mftslack_size > 0:
                self.slack_list.append(SlackSpace(mftslack_size, mftslack_start, mirr_offset))
            if self.info:
                print("\tMFT slack size(avoiding fixup value): %s"%mftslack_size)
            return mftslack_size, mftslack_end+2
        mftslack_end1 = (mftslack_start + self.sectorsize - (mftslack_start % self.sectorsize)) - 2
        mftslack_size1 = mftslack_end1 - mftslack_start
        if mftslack_size1 > 0:
            self.slack_list.append(SlackSpace(mftslack_size1, mftslack_start, mirr_offset))
        mftslack_size2 = mftslack_end - (mftslack_end1 + 2)
        if mftslack_size2 > 0:
            self.slack_list.append(SlackSpace(mftslack_size2, mftslack_end1 + 2, mirr_offset))
        if self.info:
            print("\tMFT slack size(avoiding fixup values): %s"
                  %(mftslack_size1 + mftslack_size2))
        return (mftslack_size1 + mftslack_size2), mftslack_end+2

    def create_metadata(self, hiddenfiles):
        """
        create metadata object from SlackFile object returned from write_file_to_slack()

        :param hiddenfiles: SlackFile object returned from write_file_to_slack()
        :return: MftSlackMetadata object
        """
        if self.info:
            print("Creating metadata:")
        meta = MftSlackMetadata()
        for file in hiddenfiles:
            for loc in file.loc_list:
                if self.info:
                    print("\t%s slack at %s"%(loc.size, loc.addr))
                meta.add_addr(loc.addr, loc.size, loc.mirr)
        return meta

    def read(self, outstream, meta):
        """
        writes slackspace of mft entries into outstream

        :param outstream: stream to write into

        :param meta: MftSlackMetadata object
        """
        for addr, length, mirr in meta.get_addr():
            self.stream.seek(addr)
            bufferv = self.stream.read(length)
            outstream.write(bufferv)

    def clear(self, meta):
        """
        clears the slackspace of mft entries specified by metadata

        :param meta: MftSlackMetadata object
        """
        for addr, length, mirr in meta.get_addr():
            self.stream.seek(addr)
            self.stream.write(length * b'\x00')
            if mirr > 0:
                self.stream.seek(mirr)
                self.stream.write(length * b'\x00')

    def write_file_to_slack(self):
        """
        write a file to found slack

        :return: SlackFile to generate metadata with
        """
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
        # iterate over list of slackspace
        for slack in self.slack_list:
            # go to address of free slack
            self.stream.seek(slack.addr)
            mirr_offset = slack.mirr
            # write file to slack space, set position and
            # add a location to the hidden files location list
            if slack.size >= length:
                self.stream.write(input_file[pos:pos + length])
                if mirr_offset is not None and slack.addr < self.mft_start + self.mftmirr_size:
                    self.stream.seek(slack.addr+mirr_offset)
                    self.stream.write(input_file[pos:pos + length])
                    hidden_file.loc_list.append(SlackSpace(length, slack.addr, slack.addr+mirr_offset))
                else:
                    hidden_file.loc_list.append(SlackSpace(length, slack.addr, 0))
                break
            else:
                self.stream.write(input_file[pos:pos + slack.size])
                if mirr_offset is not None and slack.addr < self.mft_start + self.mftmirr_size:
                    self.stream.seek(slack.addr+mirr_offset)
                    self.stream.write(input_file[pos:pos + slack.size])
                    hidden_file.loc_list.append(SlackSpace(slack.size, slack.addr, slack.addr+mirr_offset))
                else:
                    hidden_file.loc_list.append(SlackSpace(slack.size, slack.addr, 0))
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
        """
        get size of file to hide

        :return: size of file to hide. -1 if no input was provided.
        """
        if not self.instream.isatty():
            self.input = self.instream.read()
            length = len(self.input)
            return length
        return -1

    def print_info(self, mft_offset=0, mft_limit=-1):
        """
        prints info about available mft entries

        :param mft_offset: sector offset of first mft entry
        :param mft_limit: amount of mft entries to print info for
        :return: total size of slack found
        """
        self.info = True
        self.filesize_left = float('inf')
        self.fill_slack_list(mft_offset, mft_limit)
        print("\nTotal slack:%s"%self.total_slacksize)
        return self.total_slacksize
