# -*- coding: utf-8 -*-
import pytsk3
from io import BytesIO, BufferedReader
from pytsk3 import *


class FileSlackMetadata:
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
        adds a cluster to the list of clusters
        :param cluster_id: int, id of the cluster
        :param offset: int, offset, where the fileslack begins
        :param length: int, length of the data, which was written
                       to fileslack
        """
        self.addrs.append((addr, length))

    def get_addr(self):
        """
        iterator for clusters
        :returns: iterator, that returns cluster_id, offset, length
        """
        for c in self.addrs:
            yield c[0], c[1]



FILE_TYPE_LOOKUP = {
    TSK_FS_NAME_TYPE_UNDEF : '-',
    TSK_FS_NAME_TYPE_FIFO : 'p',
    TSK_FS_NAME_TYPE_CHR : 'c',
    TSK_FS_NAME_TYPE_DIR : 'd',
    TSK_FS_NAME_TYPE_BLK : 'b',
    TSK_FS_NAME_TYPE_REG : 'r',
    TSK_FS_NAME_TYPE_LNK : 'l',
    TSK_FS_NAME_TYPE_SOCK : 'h',
    TSK_FS_NAME_TYPE_SHAD : 's',
    TSK_FS_NAME_TYPE_WHT : 'w',
    TSK_FS_NAME_TYPE_VIRT : 'v'
}

META_TYPE_LOOKUP = {
    TSK_FS_META_TYPE_REG : 'r',
    TSK_FS_META_TYPE_DIR : 'd',
    TSK_FS_META_TYPE_FIFO : 'p',
    TSK_FS_META_TYPE_CHR : 'c',
    TSK_FS_META_TYPE_BLK : 'b',
    TSK_FS_META_TYPE_LNK : 'h',
    TSK_FS_META_TYPE_SHAD : 's',
    TSK_FS_META_TYPE_SOCK :'s',
    TSK_FS_META_TYPE_WHT : 'w',
    TSK_FS_META_TYPE_VIRT : 'v'
}

NTFS_TYPES_TO_PRINT = [
    TSK_FS_ATTR_TYPE_NTFS_IDXROOT,
    TSK_FS_ATTR_TYPE_NTFS_DATA,
    TSK_FS_ATTR_TYPE_DEFAULT,
]


class slackSpace:
    def __init__(self, size, addr):
        self.size = size
        self.addr = addr
        
class fileLoc:
    def __init__(self, addr, size):
        self.size = size
        self.addr = addr
        
class fileInSlack:
    def __init__(self,name , size, ):
        self.lockList = []
        self.name = name
        self.size = size
    
class NtfsSlack: 
    
    def __init__(self,stream ):
        self.stream = stream
        self.instream = None
        # Open img file
        self.img = pytsk3.Img_Info(stream)        
        # Open the filesystem
        self.fs = pytsk3.FS_Info(self.img, offset = 0)        
        # Get the blocksize
        self.blocksize = self.fs.info.block_size #4096
        #get sector size
        self.sectorsize = self.fs.info.dev_bsize #512
        #get cluster size
        self.cluster_size = self.blocksize / self.sectorsize #8
        
        self.slackList = []
        self.totalSlackSize = 0
        self.fileSizeLeft = 0
        self.args = []
        self.input = ""
        self.filepath =""
        
    def write(self, instream, filepath):
        self.instream = instream
        self.filepath = filepath
        #size of file to hide
        fileSize = self.get_file_size()
        print ("filesize:%s"%fileSize)
        #fill list of slack space objects till file size is reached
        self.fileSizeLeft = fileSize
        self.fill_slack_list()        
        if fileSize>self.totalSlackSize:
            raise Exception("Not enough slack space")
        #.ELF(7F 45 4C 46)
        hiddenfiles = self.write_file_to_slack()
        meta = self.createMetaData(hiddenfiles)
        return meta
        
    def createMetaData(self,hiddenfiles):
        m = FileSlackMetadata()
        for file in hiddenfiles:
            for loc in file.lockList:
                m.add_addr(loc.addr,loc.size)
        return m
        
        
    def read(self, outstream, meta):
        stream = open(self.stream, 'rb+')
        for addr, length in meta.get_addr():
            stream.seek(addr)
            bufferv = stream.read(length)
            outstream.write(bufferv)
            
    def clear(self, meta):
        stream = open(self.stream, 'rb+')
        for addr, length in meta.get_addr():
            stream.seek(addr)
            stream.write(length * b'\x00')
        
    def get_slack(self, f):
        meta = f.info.meta  
        if not meta:
            return 0
        
        #get last block of file to check for slack
        resident = True
        metaBlock = f.info.meta.addr    
        mftEntrySize = 1024
        mftOffset = 16
        mtfOffsetToData = 360
        # File size
        size = f.info.meta.size
        metaAddr = (metaBlock+mftOffset)*mftEntrySize
        for attr in f:
            for run in attr:
                l_offset = run.offset
                last_block_offset = run.len-1
                last_blocks_start = run.addr
                resident = False
        #File data resident in mft $Data entry
        if resident:
            offsetToSlack = mtfOffsetToData + size
            metaSlackStart = metaAddr + offsetToSlack
            metaFreeSlack = mftEntrySize - offsetToSlack
            self.slackList.append(slackSpace(metaFreeSlack,metaSlackStart))
            return metaFreeSlack
                
        #last block = start of last blocks + offset
        last_block = last_blocks_start + last_block_offset
    
        # Last block of the file 
        l_block = (l_offset+last_block_offset) * self.blocksize
        
        # Actual file data in the last block
        l_d_size = size % self.blocksize
    
        #start of slack
        slack_start = l_block + l_d_size
    
        # Slack space size
        s_size = self.blocksize - l_d_size
        
        #check if slack empty
        start_addr_slack = last_block*self.blocksize + l_d_size
        print("%s slack found"%s_size)
        self.slackList.append(slackSpace(s_size,start_addr_slack))
        return s_size
        
        slack_bytes = []
        data = f.read_random(slack_start, self.blocksize, TSK_FS_ATTR_TYPE_DEFAULT, 0, TSK_FS_FILE_READ_FLAG_SLACK )
        slack_bytes.extend([c for c in data if ord(c) != 00])
        if (len(slack_bytes)==0):
            #if slack is empty create slack space object and append it to slack list
            slackList.append(slackSpace(s_size,start_addr_slack))
            return s_size
        
        return 0
        
        
    
    
    def is_fs_directory(self,f):
        """ Checks if an inode is a filesystem directory. """
        
        return FILE_TYPE_LOOKUP.get(int(f.info.name.type), '-') == FILE_TYPE_LOOKUP[TSK_FS_NAME_TYPE_DIR]
    
    
    def is_fs_regfile(self,f):
        """Checks if an inode is a regular file."""
        
        return FILE_TYPE_LOOKUP.get(int(f.info.name.type), '-') == FILE_TYPE_LOOKUP[TSK_FS_NAME_TYPE_REG]
    
    
    def get_file_slack(self,directory, indent = 0):  
        #iterate over files/directories
        for f in directory:
            if self.fileSizeLeft>0:
                if (self.is_fs_regfile(f)):
                    #if file: get slack of file and add slack to total slack size
                    slackSize = self.get_slack(f)
                    self.totalSlackSize += slackSize
                    #subtract slacksize to stop if enough space was found
                    self.fileSizeLeft -= slackSize
                #recurse into directories
                if (self.is_fs_directory(f)):
                    try:
                        d = f.as_directory()    
                        if f.info.name.name != b'.' and f.info.name.name != b'..':
                            self.get_file_slack(d, indent + 1)
                    except RuntimeError:
                        print ('RunError!')
                    except IOError:
                        print ("IOError while opening %s" % (f.info.name.name))
                        
    def get_file_slack_single_file(self, file):
            if self.fileSizeLeft>0:
                slackSize = self.get_slack(file)
                self.totalSlackSize += slackSize
                self.fileSizeLeft -= slackSize
    
    
    
    def write_info_file(self,hiddenFile):
        #write meta data...
        #TODO change
        fInf = "\n%s\n"%hiddenFile.name
        for l in hiddenFile.lockList:
            fInf += "%s:%s\n" % (l.addr, l.size)
        print ("ID:%s"%hiddenFile.name)
        fInf += "--"
        while len(fInf)%16 !=0:
            fInf += "-"
        fInf = fInf[:-1]
        fInf += "\n"
        inf = open("/home/fs/list.list","ab")
        inf.write(bytes(fInf, 'UTF-8'))
        inf.flush
        inf.close
       

        
    def write_file_to_slack(self):
        hiddenFiles = []
        if len(self.args)>0:
            #iterate over files passed as arguments
            for arg in self.args:
                #read file
                inputStream = open(arg,"rb")
                inputFile = inputStream.read()
                length =  len(inputFile)
                #position for input file partitioning
                pos = 0
                #random id for file metadata
                fileID = "123"
                #create hidden file object with id and length
                hiddenFile = fileInSlack(fileID, length)
                #open image
                stream = open(stream, 'rb+')
                #iterate over list of slackspace
                for s in slackList:
                    #go to address of free slack
                    stream.seek(s.addr)
                    #write file to slack space, set position and add a location to the hidden files location list
                    if s.size >= length:
                        stream.write(inputFile[pos:pos+length])
                        hiddenFile.lockList.append(fileLoc(s.addr,length))
                        break
                    else:
                        stream.write(inputFile[pos:pos+s.size])
                        hiddenFile.lockList.append(fileLoc(s.addr,s.size))
                        pos+=s.size
                        length-=s.size
                stream.flush
                stream.close
                inputStream.close
                #write meta data
                write_info_file(hiddenFile)
                #add hidden file object to list of hidden files
                hiddenFiles.append(hiddenFile)
        else:
            #read file
            inputFile = self.input
            length =  len(inputFile)
            #position for input file partitioning
            pos = 0
            #random id for file metadata
            fileID = "123"
            #create hidden file object with id and length
            hiddenFile = fileInSlack(fileID, length)
            #open image
            stream = open(self.stream, 'rb+')
            #iterate over list of slackspace
            for s in self.slackList:
                #go to address of free slack
                stream.seek(s.addr)
                #write file to slack space, set position and add a location to the hidden files location list
                if s.size >= length:
                    stream.write(inputFile[pos:pos+length])
                    hiddenFile.lockList.append(fileLoc(s.addr,length))
                    break
                else:
                    stream.write(inputFile[pos:pos+s.size])
                    hiddenFile.lockList.append(fileLoc(s.addr,s.size))
                    pos+=s.size
                    length-=s.size
            stream.flush
            stream.close
            self.instream.close
            #write meta data
            #self.write_info_file(hiddenFile)
            #add hidden file object to list of hidden files
            hiddenFiles.append(hiddenFile)
        return hiddenFiles
    
    def get_file_size(self):
        if len(self.args)>0:
            length = 0
            #get size of all files
            for arg in self.args:
                inputStream = open(arg,"rb")
                inputFile = inputStream.read()
                inputStream.close()
                length += len(inputFile)
            return length
        else:
            self.input = self.instream.read()
            length = len(self.input)
            return length
            

            
    def get_Volume_Slack(self):
        selectedPartition = None
        #find partition by offset
        for partition in volume:
            if partition.start == options.offset:
                selectedPartition = partition
                break
        #free sectors after filesystem(+1 for copy of boot sector)
        freeSectors = selectedPartition.len - (fs.info.block_count+1)*cluster_size
        print ("free Sectors:%s"%freeSectors )
        #get address of first free sector
        firstFreeSectorAddr = (fs.info.last_block+2)*blocksize
        fileSytemSlackSize = freeSectors*sectorsize
        print ("File System Slack: %s - %s(%s)"%(firstFreeSectorAddr,firstFreeSectorAddr+fileSytemSlackSize,fileSytemSlackSize))
        #create slack space object and append to list
        slackList.append(slackSpace(fileSytemSlackSize,firstFreeSectorAddr))
        #set the total slack size
        self.totalSlackSize += fileSytemSlackSize
         
    def fill_slack_list(self):
        #look file slack
        for path in self.filepath:
            try:
                directory = self.fs.open_dir(path)
                self.get_file_slack(directory)
            except OSError:
                file = self.fs.open(path)
                self.get_file_slack_single_file(file)
        #look for volume slack?
#        if options.slack == "volume":
#            get_Volume_Slack()




    