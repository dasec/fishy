Module Documentation
====================

Filesystem Implementations
--------------------------

FAT Filesystem
**************

This toolkit uses its own FAT implementation, supporting FAT12, FAT16 and
FAT32.  It implements most parts of parsing the filesystem and some basic write
operations, which can be used by hiding techniques.

To parse a filesystem image use the wrapper function `create_fat`.
This parses a file stream and returns the appropriate FAT instance.

.. code-block:: python

        from fishy.fat.fat_filesystem.fat_wrapper import create_fat

        f = open('testfs.dd', 'rb')
        fs = create_fat(f)


This filesystem instance provides some important methods.

.. autoclass:: fishy.fat.fat_filesystem.fat.FAT
        :members:

Metadata
--------

.. automodule:: fishy.metadata
        :members:

Hiding Techniques
-----------------

FAT
***

File Slack
..........

.. automodule:: fishy.fat.file_slack
        :members:

Additional Cluster Allocation
.............................

.. automodule:: fishy.fat.cluster_allocator
        :members:

Bad Cluster Allocation
......................

.. automodule:: fishy.fat.bad_cluster
        :members:

NTFS
****

File Slack
..........

.. automodule:: fishy.ntfs.ntfs_file_slack
        :members:

MFT Slack
.........

.. automodule:: fishy.ntfs.ntfs_mft_slack
        :members:

Ext4
****

Reseved GDT Blocks
..................

.. automodule:: fishy.ext4.reserved_gdt_blocks
        :members:

Superblock Slack
................

.. automodule:: fishy.ext4.superblock_slack
        :members:

File Slack
..........

.. automodule:: fishy.ext4.ext4_file_slack
        :members:

osd2
....

.. automodule:: fishy.ext4.osd2
        :members:

obso_faddr
..........

.. automodule:: fishy.ext4.obso_faddr
        :members:

			
			
