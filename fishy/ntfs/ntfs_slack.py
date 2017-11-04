# -*- coding: utf-8 -*-
import pytsk3
from io import BytesIO, BufferedReader
from optparse import OptionParser
from pytsk3 import *
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import random


usage = "Usage: %prog [options]... file(s)..."
parser = OptionParser(usage = usage)

parser.add_option('-o', '--offset', default=2048, type='int',
                  help='Offset in the image')

parser.add_option('-p', '--password', default=None,
                  help='pass for encrytion of list file')

parser.add_option("-i", "--image", default="/dev/sdb",
                  help="The image to use (Default /dev/sdb)")

parser.add_option("-m", "--mode", default="write",
                  help="Select mode. Supported options are 'read', 'write'")

parser.add_option("-s", "--slack", default="file",
                  help="Select type of slack. Supported options are 'file', 'volume'")

parser.add_option("-f", "--file", default=None,
                  help="File ID for read. Empty to list all")

parser.add_option("-l", "--list", default="/home/fs/",
                  help="Path to list file (Default /home/fs/)")

(options, args) = parser.parse_args()


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


slackList = []
totalSlackSize = 0
fileSizeLeft = 0

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


def get_slack(f):
    meta = f.info.meta  
    if not meta:
        return 0
    
    #get last block of file to check for slack
    ok = None
    for attr in f:
        for run in attr:
            l_offset = run.offset
            last_block_offset = run.len-1
            last_blocks_start = run.addr
            ok = run
    if not ok:
        return 0
            
    #last block = start of last blocks + offset
    last_block = last_blocks_start + last_block_offset

    # Last block of the file 
    l_block = (l_offset+last_block_offset) * blocksize

    # File size
    size = f.info.meta.size
    
    # Actual file data in the last block
    l_d_size = size % blocksize

    #start of slack
    slack_start = l_block + l_d_size

    # Slack space size
    s_size = blocksize - l_d_size
    
    #check if slack empty
    start_addr_slack = last_block*blocksize + l_d_size
    slack_bytes = []
    data = f.read_random(slack_start, blocksize, TSK_FS_ATTR_TYPE_DEFAULT, 0, TSK_FS_FILE_READ_FLAG_SLACK )
    slack_bytes.extend([c for c in data if ord(c) != 00])
    if (len(slack_bytes)==0):
        #if slack is empty create slack space object and append it to slack list
        slackList.append(slackSpace(s_size,start_addr_slack))
        return s_size
    
    return 0
    
    


def is_fs_directory(f):
    """ Checks if an inode is a filesystem directory. """
    
    return FILE_TYPE_LOOKUP.get(int(f.info.name.type), '-') == FILE_TYPE_LOOKUP[TSK_FS_NAME_TYPE_DIR]


def is_fs_regfile(f):
    """Checks if an inode is a regular file."""
    
    return FILE_TYPE_LOOKUP.get(int(f.info.name.type), '-') == FILE_TYPE_LOOKUP[TSK_FS_NAME_TYPE_REG]


def get_file_slack(directory, indent = 0):  
    global fileSizeLeft
    #iterate over files/directories
    for f in directory:
        if fileSizeLeft>0:
            if (is_fs_regfile(f)):
                #if file: get slack of file and add slack to total slack size
                slackSize = get_slack(f)
                global totalSlackSize
                totalSlackSize += slackSize
                #subtract slacksize to stop if enough space was found
                fileSizeLeft -= slackSize
            #recurse into directories
            if (is_fs_directory(f)):
                try:
                    d = f.as_directory()    
                    if f.info.name.name != "." and f.info.name.name != "..":
                        get_file_slack(d, indent + 1)
                except RuntimeError:
                    print 'RunError!'
                except IOError:
                    print "IOError while opening %s" % (f.info.name.name)


def encrypt(text):
    #encrypt with aes ecb mode
    hashPw = SHA256.new()
    hashPw.update(options.password)
    encrypter = AES.new(hashPw.digest(), AES.MODE_ECB)
    ciphertext = encrypter.encrypt(text)
    return ciphertext
    
def decrypt(text):
    #dencrypt with aes ecb mode
    hashPw = SHA256.new()
    hashPw.update(options.password)
    decrypter = AES.new(hashPw.digest(), AES.MODE_ECB)
    infFile = decrypter.decrypt(text)
    return infFile

def write_info_file(hiddenFile):
    #write meta data...
    #TODO change
    fInf = "\n%s\n"%hiddenFile.name
    for l in hiddenFile.lockList:
        fInf += "%s:%s\n" % (l.addr, l.size)
    print "ID:%s"%hiddenFile.name
    fInf += "--"
    while len(fInf)%16 !=0:
        fInf += "-"
    fInf = fInf[:-1]
    fInf += "\n"
    if options.password is not None:
        fInf = encrypt(fInf)
    inf = open("%slist.list"%options.list,"ab")
    inf.write(fInf)
    inf.flush
    inf.close
   
def read_info_file():
    #open meta data gile
    inf = open("%slist.list"%options.list,"rb")
    #id of file to extract
    fId = options.file
    #decrypt if password is set
    if options.password is not None:
        cryptFile = inf.read()
        infFile = decrypt(cryptFile)    
    else:
        infFile[0:4] = inf.read()
    infLines = infFile.splitlines()
    #create hidden file object
    hiddenFile = None
    #iterate over lines, look for file id and get locations of the hidden file
    for line in infLines:        
        if options.file is None:
            print line
        if line == fId:
            hiddenFile = fileInSlack(fId,0)
        elif "-" in line and hiddenFile is not None:
            break
        elif hiddenFile is not None:
            vals = line.split(":",1)
            #fill hidden file object locations
            hiddenFile.lockList.append(fileLoc(vals[0],vals[1]))
        
    inf.close
    return hiddenFile
    
def write_file_to_slack():
    hiddenFiles = []
    if len(args)>0:
        #iterate over files passed as arguments
        for arg in args:
            #read file
            inputStream = open(arg,"rb")
            inputFile = inputStream.read()
            length =  len(inputFile)
            #position for input file partitioning
            pos = 0
            #random id for file metadata
            fileID = random.randint(10000,99999)
            #create hidden file object with id and length
            hiddenFile = fileInSlack(fileID, length)
            #open image
            stream = open(options.image, 'rb+')
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
        return hiddenFiles
    else:
        #TODO use std in
        raise Exception("No Input Files")

def get_file_size():
    if len(args)>0:
        length = 0
        #get size of all files
        for arg in args:
            inputStream = open(arg,"rb")
            inputFile = inputStream.read()
            inputStream.close()
            length +=  len(inputFile)
        return length
    else:
        #TODO use std in
        raise Exception("No Input Files")
        
def read_file_from_slack():
    #get hiddenFile object from meta data
    hiddenFile = read_info_file()
    if hiddenFile is not None:
        stream = open(options.image, 'rb+')
        fileOut = open("%s.txt"%hiddenFile.name,"wb")
        #go through hidden file locations
        for l in hiddenFile.lockList:
            #read hidden data and wirte into fileOut
            stream.seek(int(l.addr))
            buff = bytearray(int(l.size))
            stream.readinto(buff)
            fileOut.write(buff)
        stream.flush
        stream.close
        fileOut.flush
        fileOut.close
        
def get_Volume_Slack():
    selectedPartition = None
    #find partition by offset
    for partition in volume:
        if partition.start == options.offset:
            selectedPartition = partition
            break
    #free sectors after filesystem(+1 for copy of boot sector)
    freeSectors = selectedPartition.len - (fs.info.block_count+1)*cluster_size
    print "free Sectors:%s"%freeSectors 
    #get address of first free sector
    firstFreeSectorAddr = (fs.info.last_block+2)*blocksize
    fileSytemSlackSize = freeSectors*sectorsize
    print "File System Slack: %s - %s(%s)"%(firstFreeSectorAddr,firstFreeSectorAddr+fileSytemSlackSize,fileSytemSlackSize)
    #create slack space object and append to list
    slackList.append(slackSpace(fileSytemSlackSize,firstFreeSectorAddr))
    #set the total slack size
    global totalSlackSize
    totalSlackSize += fileSytemSlackSize
     
def fill_slack_list():
    #look file slack
    if options.slack == "file":
        directory = fs.open_dir("/")
        get_file_slack(directory)
    #look for volume slack?
    if options.slack == "volume":
        get_Volume_Slack()

# Open img file
img = pytsk3.Img_Info(options.image)

#open volume
volume = pytsk3.Volume_Info(img)

#get sector size
sectorsize = volume.info.block_size #512

# Open the filesystem
fs = pytsk3.FS_Info(img, offset = (options.offset * sectorsize ))


# Get the blocksize
blocksize = fs.info.block_size #4096

#get cluster size
cluster_size = blocksize / sectorsize #8


if options.mode == "write":
    #size of file to hide
    fileSize = get_file_size()
    print "filesize:%s"%fileSize
    #fill list of slack space objects till file size is reached
    fileSizeLeft = fileSize
    fill_slack_list()
    
    if fileSize>totalSlackSize:
        raise Exception("Not enough slack space")
    #.ELF(7F 45 4C 46)
    write_file_to_slack()
elif options.mode == "read":
    read_file_from_slack()

fs.exit()




    