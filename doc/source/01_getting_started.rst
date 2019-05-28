Getting Started
===============

Requirements
------------

* Build:
        * Python version 3.5 or higher
        * argparse - command line argument parsing
        * construct - parsing FAT filesystems
        * pytsk3 - parsing NTFS filesystems
        * simple-crypt - encryption of metadata using AES-CTR
        * numpy - Calculating APFS checksums
* Testing:
        * pytest - unit test framework
        * mount and dd - unix tools. needed for test image generation
* Documentation:
        * sphinx - generates the documentation
        * sphinx-argparse - cli parameter documentation
        * graphviz - unix tool. generates graphs, used in the documentation

Installation
------------

.. code:: shell

    # To run unit tests before installing
    $ sudo python setup.py test
    # Install the program
    $ sudo python setup.py install
    # Generate documentation
    $ pip install sphinx spinx-argparse
    $ python setup.py doc

To generate the documentation as pdf:

.. code:: shell

    $ cd doc
    $ make latexpdf


You may have to install some extra latex dependencies:

.. code:: shell

    $ sudo apt-get install latexmk
    $ sudo apt-get install texlive-formats-extra

Test Filesystem
---------------
To generate a filesystem for a quick test of `fishy`, take a look at the appendix 1 `create_testfs.sh`

Usage
-----

The cli interface groups all hiding techniques (and others) into
subcommands. Following table gives an overview over all implemented hiding techniques:

+---------------------+-------------------------+--------------------------------------------+
| Hiding technique    |  Filesystem             | Description                                |
| (Subcommand)        |                         |                                            |
+---------------------+----+------+------+------+--------------------------------------------+
|                     |FAT | NTFS | Ext4 | APFS |                                            |
+---------------------+----+------+------+------+--------------------------------------------+
| fileslack           | ✓  |  ✓   | ✓    |      | Exploitation of File Slack                 |
+---------------------+----+------+------+------+--------------------------------------------+
| mftslack            |    |  ✓   |      |      | Exploitation of MFT entry Slack            |
+---------------------+----+------+------+------+--------------------------------------------+
| addcluster          | ✓  |  ✓   |     |       | Allocate additional clusters for a file    |
+---------------------+----+------+------+------+--------------------------------------------+
| badcluster          | ✓  |  ✓   |      |      | Bad Cluster Allocation                     |
+---------------------+----+------+------+------+--------------------------------------------+
| reserved_gdt_blocks |    |      |  ✓   |      | Exploitation of Reserved GDT Blocks        |
+---------------------+----+------+------+------+--------------------------------------------+
| superblock_slack    |    |      |  ✓   |   ✓  | Exploitation of Superblock Slack           |
+---------------------+----+------+------+------+--------------------------------------------+
| osd2                |    |      |  ✓   |      | Use unused inode field osd2                |
+---------------------+----+------+------+------+--------------------------------------------+
| obso_faddr          |    |      |  ✓   |      | Use unused inode field obso_faddr          |
+---------------------+----+------+------+------+--------------------------------------------+
| nanoseconds         |    |      |      |  ✓   | Use of nanosecond timestamp part           |
+---------------------+----+------+------+------+--------------------------------------------+
| inode_padding       |    |      |      |  ✓   | Use of Padding in Inodes                   |
+---------------------+----+------+------+------+--------------------------------------------+
| write_gen_counter   |    |      |      |  ✓   | Use of write counter in Inodes             |
+---------------------+----+------+------+------+--------------------------------------------+
| ext_field_padding   |    |      |      |  ✓   | Use of dynamically created Extended Fields |
+---------------------+----+------+------+------+--------------------------------------------+




Additionally to the hiding techniques above, there are following informational
subcommands available:

* fattools - Provides some information about a FAT filesystem 
* metadata - Provides some information about data that is stored in a metadata file 

The following sections will give brief examples on how to use the `fishy` cli tool with each subcommand.

FATtools
........

To get information about a FAT filesystem you can use the ``fattools``
subcommand:

.. code:: bash

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

Metadata
........

Metadata files will be created while writing information into the
filesystem. They are required to restore those information or to wipe
them from filesystem. To display information, that are stored in those
metadata files, you can use the ``metadata`` subcommand.

.. code:: bash

    # Show metadata information from a metadata file
    $ fishy metadata -m metadata.json
    Version: 2
    Module Identifier: fat-file-slack
    Stored Files:
      File_ID: 0
      Filename: 0
      Associated File Metadata:
        {'clusters': [[3, 512, 11]]}

File Slack
..........

The ``fileslack`` subcommand provides functionality to read, write and
clean the file slack of files in a filesystem.

Available for these filesystem types:

-  FAT
-  NTFS
-  EXT4

.. code:: bash

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

MFT Slack
.........

The ``mftslack`` subcommand provides functionality to read, write and clean the slack of mft entries in a filesystem.

Available for these filesystem types:

- NTFS

.. code:: bash

    # write into slack space
    $ echo "TOP SECRET" | fishy -d testfs-ntfs.dd mftslack -m metadata.json -w

    # read from slack space
    $ fishy -d testfs-ntfs.dd mftslack -m metadata.json -r
    TOP SECRET

    # wipe slack space
    $ fishy -d testfs-ntfs.dd mftslack -m metadata.json -c



Additional Cluster Allocation
.............................

The ``addcluster`` subcommand provides methods to read, write and clean
additional clusters for a file where data can be hidden.

Available for these filesystem types:

- FAT
- NTFS

.. code:: bash

    # Allocate additional clusters for a file and hide data in it
    $ echo "TOP SECRET" | fishy -d testfs-fat12.dd addcluster -d myfile.txt -m metadata.json -w

    # read hidden data from additionally allocated clusters
    $ fishy -d testfs-fat12.dd addcluster -m metadata.json -r
    TOP SECRET

    # clean up additionally allocated clusters
    $ fishy -d testfs-fat12.dd addcluster -m metadata.json -c

Bad Cluster Allocation
......................

The ``badcluster`` subcommand provides methods to read, write and clean
bad clusters, where data can be hidden into.

Available for these filesystem types:

- FAT
- NTFS

.. code:: bash

    # Allocate bad clusters and hide data in it
    $ echo "TOP SECRET" | fishy -d testfs-fat12.dd badcluster -m metadata.json -w

    # read hidden data from bad clusters
    $ fishy -d testfs-fat12.dd badcluster -m metadata.json -r
    TOP SECRET

    # clean up bad clusters
    $ fishy -d testfs-fat12.dd badcluster -m metadata.json -c

Reserved GDT Blocks
......................

The ``reserved_gdt_blocks`` subcommand provides methods to read, write and clean
the space reserved for the expansion of the GDT.

Available for these filesystem types:

- EXT4

.. code:: bash

    # write int reserved GDT Blocks
    $ echo "TOP SECRET" | fishy -d testfs-ext4.dd reserved_gdt_blocks -m metadata.json -w

    # read hidden data from reserved GDT Blocks
    $ fishy -d testfs-ext4.dd reserved_gdt_blocks -m metadata.json -r
    TOP SECRET

    # clean up reserved GDT Blocks
    $ fishy -d testfs-ext4.dd reserved_gdt_blocks -m metadata.json -c

Superblock Slack
......................

The ``superblock_slack`` subcommand provides methods to read, write and clean
the slack of superblocks in an ext4 filesystem

Available for these filesystem types:

- EXT4
- APFS

.. code:: bash

    # write int Superblock Slack
    $ echo "TOP SECRET" | fishy -d testfs-ext4.dd superblock_slack -m metadata.json -w

    # read hidden data from Superblock Slack
    $ fishy -d testfs-ext4.dd superblock_slack -m metadata.json -r
    TOP SECRET

    # clean up Superblock Slack
    $ fishy -d testfs-ext4.dd superblock_slack -m metadata.json -c

OSD2
......................

The ``osd2`` subcommand provides methods to read, write and clean
the unused last two bytes of the inode field osd2

Available for these filesystem types:

- EXT4

.. code:: bash

    # write int osd2 inode field
    $ echo "TOP SECRET" | fishy -d testfs-ext4.dd osd2 -m metadata.json -w

    # read hidden data from osd2 inode field
    $ fishy -d testfs-ext4.dd osd2 -m metadata.json -r
    TOP SECRET

    # clean up osd2 inode field
    $ fishy -d testfs-ext4.dd osd2 -m metadata.json -c

obso_faddr
......................

The ``obso_faddr`` subcommand provides methods to read, write and clean
the unused inode field obso_faddr

Available for these filesystem types:

- EXT4

.. code:: bash

    # write int obso_faddr inode field
    $ echo "TOP SECRET" | fishy -d testfs-ext4.dd obso_faddr -m metadata.json -w

    # read hidden data from obso_faddr inode field
    $ fishy -d testfs-ext4.dd obso_faddr -m metadata.json -r
    TOP SECRET

    # clean up obso_faddr inode field
    $ fishy -d testfs-ext4.dd obso_faddr -m metadata.json -c
	
timestamp_hiding
......................

The ``timestamp_hiding`` subcommand provides methods to read, write and clean
the nanosecond part of a timestamp.

Available for these filesystem types:

- APFS

.. code:: bash

	# write to timestamp
	$ echo "TOP SECRET" | fishy -d testfs-apfs.dd timestamp_hiding -m metadata.json -w
	
	# read hidden data from timestamp
	$ fishy -d testfs-apfs.dd timestamp_hiding -m metadata.json -r
	TOP SECRET
	
	# clean up timestamps
	$ fishy -d testfs-apfs.dd timestamp_hiding -m metadata.json -c
	
inode_padding
......................

The ``inode_padding`` subcommand provides methods to read, write and clean
padding fields in inodes.

Available for these filesystem types:

- APFS

..code:: bash

	# write to inode padding
	$ echo "TOP SECRET" | fishy -d testfs-apfs.dd inode_padding -m metadata.json -w
	
	# read from inode padding
	$ fishy -d testfs-apfs.dd inode_padding -m metadata.json -r
	TOP SECRET
	
	# clean up inode padding
	$ fishy -d testfst-apfs.dd inode_padding -m metadata.json -c

write_gen_counter
......................

The ``write_gen`` subcommand provides methods to read, write and clean
the write counter found in inodes.

Available for these filesystem types:

- APFS

..code:: bash

	# write to write counter
	$ echo "TOP SECRET" | fishy -d testfs-apfs.dd write_gen -m metadata.json -w
	
	# read from write counter
	$ fishy -d testfs-apfs.dd write_gen -m metadata.json -r
	TOP SECRET
	
	# clean up write counter
	$ fishy -d testfst-apfs.dd write_gen -m metadata.json -c
	
ext_field_padding
......................

The ``xfield_padding`` subcommand provides methods to read, write and clean
dynamically created padding fields in the extended field section of an inode.

Available for these filesystem types:

- APFS

..code:: bash

	# write to extended field padding
	$ echo "TOP SECRET" | fishy -d testfs-apfs.dd xfield_padding -m metadata.json -w
	
	# read from extended field padding
	$ fishy -d testfs-apfs.dd xfield_padding -m metadata.json -r
	TOP SECRET
	
	# clean up extended field padding
	$ fishy -d testfst-apfs.dd xfield_padding -m metadata.json -c	



Encryption and Checksumming
...........................

Currently, fishy does not provide on the fly encryption and does not apply any
data integrity methods to the hidden data. Thus its left to the user, to add
those extra functionality before hiding the data. The following listing gives
two examples, on how to use pipes to easily get these features.

To encrypt data with a password, one can use gnupg:

.. code:: bash

    $ echo "TOP SECRET" | gpg2 --symmetric - | fishy -d testfs-fat12.dd badcluster -m metadata.json -w

To detect corruption of the hidden data, there exist many possibilities and tools.
The following code listing gives an easy example on how to use zip for this purpose.

.. code:: bash

    $ echo "TOP SECRET" | gzip | fishy -d testfs-fat12.dd badcluster -m metadata.json -w
