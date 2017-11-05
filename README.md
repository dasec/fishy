# fishy
Toolkit for filesystem based data hiding techniques

# Techniques we found

* FAT:
	* File Slack
		* Simple: Only writing to slackspace of one file  [✓]
		* Advanced: Writing to slackspace of multiple files
	* Partition Slack
	* Mark Clusters as 'bad', but write content to them
	* Allocate More Clusters for a file
	* Overwrite Bootsector Copy?
	* Overwrite FAT Copies when they are not FAT0 or FAT1

# Installation

```bash
$ sudo pip install -r requirements.txt
$ sudo python setup.py install
```

# Usage

The cli interface groups all hiding techniques (and others) into subcommands. Currently available subcommands are:
* [`fattools`](#fattools) - Provides some information about a FAT filesystem
* [`metadata`](#metadata) - Provides some information about information that is stored in a metadata file
* [`fileslack`](#file-slack) - Exploitation of File Slack

## FATtools

To get information about a FAT filesystem you can use the `fattools` subcommand:

```bash
# Get some meta information about the FAT filesystem
$ fishy -d testfs-fat32.dd fattools -i
FAT Type:                                  FAT32
Sector Size:                               512
Sectors per Cluster:                       8
Sectors per FAT:                           3904
FAT Count:                                 2
Dataregion Start Byte:                     4014080
Free Data Clusters (FS Info):              499075
Recently Allocated Data Cluster (FS Info): 8
Root Directory Cluster:                    2
FAT Mirrored:                              False
Active FAT:                                0
Sector of Bootsector Copy:                 6

# List entries of the file allocation table
$ fishy -d testfs-fat12.dd fattools -f
0 last_cluster
1 last_cluster
2 free_cluster
3 last_cluster
4 5
5 6
6 7
7 last_cluster
[...]

# List files in a directory (use cluster_id from second column to list subdirectories)
$ fishy -d testfs-fat12.dd fattools -l 0
f     3        4        another
f     0        0        areallylongfilenamethatiwanttoreadcorrectly.txt
f     4        8001     long_file.txt
d     8        0        onedirectory
f     10       5        testfile.txt
```

## Metadata

Metadata files will be created while writing information into the filesystem.
They are required to restore those information or to wipe them from filesystem.
To display information, that are stored in those metadata files, you can use
the `metadata` subcommand.

```bash
# Show metadata information from a metadata file
$ fishy metadata -m metadata.json
Version: 2
Module Identifier: fat-file-slack
Stored Files:
  File_ID: 0
  Filename: 0
  Accesiated File Metadata:
    {'clusters': [[3, 512, 11]]}
```

## File Slack

The `fileslack` subcommand provides functionality to read, write and clean the file slack of files in a filesystems.

Available for these Filesystem types:
	* FAT

```bash
# write into slack space
$ echo "TOP SECRET" | fishy -d testfs-fat12.dd fileslack -d myfile.txt -m metadata.json -w

# read from slack space
$ fishy -d testfs-fat12.dd fileslack -m metadata.json -r 0
TOP SECRET

# Wipe slack space
$ fishy -d testfs-fat12.dd fileslack -m metadata.json -c
```

# Development

* with `create_testfs.sh` you can create test filesystem, which already contain files
* Unittests can be executed by running `python -m unittest`. Please make sure the `create_testfs.sh` script runs as expected.
