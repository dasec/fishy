Getting Started
===============

Requirements
------------

* Build:
        * Python version 3.5 or higher
        * argparse - command line argument parsing
        * construct - parsing FAT filesystems
        * pytsk3 - parsing NTFS filesystems
* Testing
        * pytest - unit test framework
        * mount and dd - unix tools. needed for test image generation
* Documentation
        * sphinx
        * sphinx-argparse

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

Usage
-----

The cli interface groups all hiding techniques (and others) into
subcommands. Currently available subcommands are: 


* `fattools <#fattools>`_ - Provides some information about a FAT filesystem 
* `metadata <#metadata>`_ - Provides some information about data that is stored in a metadata file 
* `fileslack <#file-slack>`__ - Exploitation of File Slack 
* `addcluster <#additional-cluster-allocation>`__ - Allocate additional clusters for a file

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

Additional Cluster Allocation
.............................

The ``addcluster`` subcommand provides methods to read, write and clean
additional clusters for a file where data can be hidden.

Available for these filesystem types:

-  FAT

.. code:: bash

    # Allocate additional clusters for a file and hide data in it
    $ echo "TOP SECRET" | fishy -d testfs-fat12.dd addcluster -d myfile.txt -m metadata.json -w

    # read hidden data from additionally allocated clusters
    $ fishy -d testfs-fat12.dd addcluster -m metadata.json -r
    TOP SECRET

    # clean up additionally allocated clusters
    $ fishy -d testfs-fat12.dd addcluster -m metadata.json -c
