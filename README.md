# fishy

`fishy` is a toolkit for filesystem based data hiding techniques, implemented
in Python. It collects various common exploitation methods, that make use of
existing datastructures on the filesystem layer, for hiding data from
conventional file access methods. This toolkit is intended to introduce people
to the concept of established anti-forensic methods associated with data
hiding.

## Code Authors and Project

fishy is a projet initiated by several bachelor students of the Hochschule Darmstadt (h_da), University of Applied Sciences and the da/sec research group.

Student members: Adrian Kailus, Christian Hecht, Matthias Greune, Deniz Celik, Tim Christen, Dustin Kern, Yannick Mau und Patrick Naili.

da/sec members: Thomas Göbel, Sebastian Gärtner and Lorenz Liebler.


## References

* [1] Adrian V. Kailus, Christian Hecht, Thomas Göbel und Lorenz Liebler, „fishy – Ein Framework zur Umsetzung von Verstecktechniken in Dateisystemen“, in D-A-CH Security, Gelsenkirchen (Germany), September 2018.
* [2] Thomas Göbel and Harald Baier, „fishy – A Framework for Implementing Filesystem-based Data Hiding Techniques“, in Proceedings of the 10th EAI International Conference on Digital Forensics & Cyber Crime (ICDF2C), New Orleans (United States), September 2018.

## Attribution

Any publications using the code must cite and reference the conference paper [1] and [2].


## Requirements

* Build:
	* Python version 3.5 or higher
	* argparse - command line argument parsing
	* construct - parsing FAT filesystems
	* pytsk3 - parsing NTFS filesystems
	* simple-crypt - encryption of metadata using AES-CTR
* Testing
	* pytest - unit test framework
	* mount and dd - unix tools. needed for test image generation 
* Documentation
	* sphinx - generates the documentation
	* sphinx-argparse - cli parameter documentation
	* graphviz - unix tool. generates graphs, used in the documentation

## Installation

```bash
# To run unit tests before installing
$ sudo python setup.py test
# Install the program
$ sudo python setup.py install
# Create documentation
$ pip install sphinx sphinx-argparse
$ python setup.py doc
```

To generate the documentation as pdf:
```bash
$ cd doc
$ make latexpdf
```

You may have to install some extra latex dependencies:
```bash
$ sudo apt-get install latexmk
$ sudo apt-get install texlive-formats-extra
```

# Usage and Hiding Techniques

## Techniques we found

* FAT:
	* File Slack [✓]
	* Bad Cluster Allocation [✓]
	* Allocate More Clusters for a file [✓]

* NTFS:
	* File Slack [✓]
	* MFT Slack [✓]
	* Allocate More Clusters for File [✓]
	* Bad Cluster Allocation [✓]
	* Add data attribute to directories
	* Alternate Data Streams
* Ext4:
	* Superblock Slack [✓]
	* reserved GDT blocks [✓]
	* File Slack [✓]
	* inode:
		* osd2 [✓]
		* obso_faddr [✓]

## CLI

The cli interface groups all hiding techniques (and others) into subcommands. Currently available subcommands are:
* [`fattools`](#fattools) - Provides some information about a FAT filesystem
* [`metadata`](#metadata) - Provides some information about data that is stored in a metadata file
* [`fileslack`](#file-slack) - Exploitation of File Slack
* [`addcluster`](#additional-cluster-allocation) - Allocate additional clusters for a file
* [`badcluster`](#bad-cluster-allocation) - Allocate bad clusters
* [`superblock_slack`](#superblock-slack) - Exploitation of Superblock Slack
* [`reserved_gdt_blocks`](#reserved-gdt-blocks) - Exploitation of reserved GDT blocks
* [`osd2`](#osd2) - Exploitation of inode's osd2 field
* [`obso_faddr`](#obso_faddr) - Exploitation of inode's obso_faddr field



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
  Associated File Metadata:
    {'clusters': [[3, 512, 11]]}
```

## File Slack

The `fileslack` subcommand provides functionality to read, write and clean the file slack of files in a filesystem.

Available for these filesystem types:

* FAT
* NTFS
* EXT4

```bash
# write into slack space
$ echo "TOP SECRET" | fishy -d testfs-fat12.dd fileslack -d myfile.txt -m metadata.json -w

# read from slack space
$ fishy -d testfs-fat12.dd fileslack -m metadata.json -r
TOP SECRET

# wipe slack space
$ fishy -d testfs-fat12.dd fileslack -m metadata.json -c

# show info about slack space of a file
$ fishy -d testfs-fat12.dd fileslack -m metadata.json -d myfile.txt -i
File: myfile.txt
  Occupied in last cluster: 4
  Ram Slack: 508
  File Slack: 1536
```

## MFT Slack

The `mftslack` subcommand provides functionality to read, write and clean the slack of mft entries in a filesystem.

Available for these filesystem types:

* NTFS

```bash
# write into slack space
$ echo "TOP SECRET" | fishy -d testfs-ntfs.dd mftslack -m metadata.json -w

# read from slack space
$ fishy -d testfs-ntfs.dd mftslack -m metadata.json -r
TOP SECRET

# wipe slack space
$ fishy -d testfs-ntfs.dd mftslack -m metadata.json -c
```


## Additional Cluster Allocation

The `addcluster` subcommand provides methods to read, write and clean additional clusters for a file where data can be hidden.

Available for these filesystem types:

* FAT
* NTFS

```bash
# Allocate additional clusters for a file and hide data in it
$ echo "TOP SECRET" | fishy -d testfs-fat12.dd addcluster -d myfile.txt -m metadata.json -w

# read hidden data from additionally allocated clusters
$ fishy -d testfs-fat12.dd addcluster -m metadata.json -r
TOP SECRET

# clean up additionally allocated clusters
$ fishy -d testfs-fat12.dd addcluster -m metadata.json -c
```

## Bad Cluster Allocation

The `badcluster` subcommand provides methods to read, write and clean
bad clusters, where data can be hidden.

Available for these filesystem types:

* FAT
* NTFS

```bash
# Allocate bad clusters and hide data in it
$ echo "TOP SECRET" | fishy -d testfs-fat12.dd badcluster -m metadata.json -w

# read hidden data from bad clusters
$ fishy -d testfs-fat12.dd badcluster -m metadata.json -r
TOP SECRET

# clean up bad clusters
$ fishy -d testfs-fat12.dd badcluster -m metadata.json -c
```

## Reserved GDT Blocks

The `reserved_gdt_blocks` subcommand provides methods to read, write and clean
the space reserved for the expansion of the GDT.

Available for these filesystem types:

* EXT4

```bash
# write int reserved GDT Blocks
$ echo "TOP SECRET" | fishy -d testfs-ext4.dd reserved_gdt_blocks -m metadata.json -w

# read hidden data from reserved GDT Blocks
$ fishy -d testfs-ext4.dd reserved_gdt_blocks -m metadata.json -r
TOP SECRET

# clean up reserved GDT Blocks
$ fishy -d testfs-ext4.dd reserved_gdt_blocks -m metadata.json -c
```

## Superblock Slack

The `superblock_slack` subcommand provides methods to read, write and clean
the slack of superblocks in an ext4 filesystem

Available for these filesystem types:

* EXT4

```bash
# write int Superblock Slack
$ echo "TOP SECRET" | fishy -d testfs-ext4.dd superblock_slack -m metadata.json -w

# read hidden data from Superblock Slack
$ fishy -d testfs-ext4.dd superblock_slack -m metadata.json -r
TOP SECRET

# clean up Superblock Slack
$ fishy -d testfs-ext4.dd superblock_slack -m metadata.json -c
```
	
## OSD2

The `osd2` subcommand provides methods to read, write and clean
the unused last two bytes of the inode field osd2

Available for these filesystem types:

* EXT4

```bash
# write int osd2 inode field
$ echo "TOP SECRET" | fishy -d testfs-ext4.dd osd2 -m metadata.json -w

# read hidden data from osd2 inode field
$ fishy -d testfs-ext4.dd osd2 -m metadata.json -r
TOP SECRET

# clean up osd2 inode field
$ fishy -d testfs-ext4.dd osd2 -m metadata.json -c	
```
	
## obso_faddr

The `obso_faddr` subcommand provides methods to read, write and clean
the unused inode field obso_faddr

Available for these filesystem types:

* EXT4

```bash
# write int obso_faddr inode field
$ echo "TOP SECRET" | fishy -d testfs-ext4.dd obso_faddr -m metadata.json -w

# read hidden data from obso_faddr inode field
$ fishy -d testfs-ext4.dd obso_faddr -m metadata.json -r
TOP SECRET

# clean up obso_faddr inode field
$ fishy -d testfs-ext4.dd obso_faddr -m metadata.json -c	
```
    
## Encryption and Checksumming

Currently, fishy does not provide on the fly encryption and does not apply any
data integrity methods to the hidden data. Thus its left to the user, to add
those extra functionality before hiding the data. The following listing gives
two examples, on how to use pipes to easily get these features.

To encrypt data with a password, one can use gnupg:

```
$ echo "TOP SECRET" | gpg2 --symmetric - | fishy -d testfs-fat12.dd badcluster -m metadata.json -w
```

To detect corruption of the hidden data, there exist many possibilities and tools.
The following code listing gives an easy example on how to use zip for this purpose.

```
$ echo "TOP SECRET" | gzip | fishy -d testfs-fat12.dd badcluster -m metadata.json -w
```


# Development

* Unittests can be executed by running `pytest`. Please make sure the `create_testfs.sh` script runs as expected.
* To make sure tests will run against the current state of your project and not only against some old installed version, consider installing via `pip install -e .` or `python setup.py develop` instead of `python setup.py install`
* Doctests can by executed with `python3 -m unittest tests/test_doctest.py`.
* To add modules to doctest, extend the `load_tests` funtion under `tests/test_doctest.py`.

## Creating test filesystem images

With `create_testfs.sh` you can create prepared filesystem images. These already include files, which get copied from `utils/fs-files/`.
To create a set of test images, simply run
```
$ ./create_testfs.sh
```

The script has a bunch of options, which will be useful when writing unit tests.
See comments in the script for further information.

If you would like to use existing test images while running unit tests, create
a file called `.create_testfs.conf` under `utils`. Here you can define the
variable `copyfrom` to provide a directory, where your existing test images are
located. For instance:

```
copyfrom="/my/image/folder"
```

To build all images that might be necessary for unittests, run
```
$ ./create_testfs.sh -t all
```


# How to implement a hiding technique

Here some general rules an hints, how one can integrate a hiding technique into the
existing project structure:

1. Under fishy create a **wrapper module** for each hiding technique, which handles
   the filesystem specific hiding technique calls + does main-metadata handling.
   The cli module would only know about this wrapper module, not your filesystem
   specific hiding technique module.
2. Hiding techniques are **located** in either `fat`, `ntfs` or `ext4` submodule.
3. **Create a Metadata class** in your hiding technique implementation. This class
   holds hiding technique dependent metadata, to be able to restore hidden data
   after write operations. Only use primitive data types in this class, so they
   can be serialized via the `__dict__` attribute. Let the write method return
   an instance of this class, which then will be written to the metadata file.
4. Every hiding technique should **implement at least** a `write`, `read` and a
   `clear` method.
5. Ony **operate on streams** in your hiding technique implementation. E.g. don't
   pass a file to the write implementation, which then would be opened, read
   and its content hidden. Instead let the wrapper script handle opening things.
   This shall ensure that the hiding technique gets more reusable and also simpler,
   as non technique specific things don't be handled there.

A simple example would be the `fishy.fat.cluster_allocator.py`

## Metadata handling

To be able to restore hidden data, most hiding techniques will need some
additional information. These information will be stored in a metadata file.
The `fishy.metadata` class provides functions to read and write metadata files
and automatically de-/encrypting the metadata if a password is provided. The
purpose of this class is to ensure, that all metadata
files have a similar datastructure. Though the program can detect at an
early point, that for example a user uses the wrong hiding technique to restore
hidden data. This metadata class we can call the 'main-metadata' class

When implementing a hiding technique, this technique must implement its own,
hiding technique specific, metadata class. So the hiding technique itself defines
which data will be stored. The write method then returns this technique specific
metadata class which then gets serialized and stored in the main-metadata.
