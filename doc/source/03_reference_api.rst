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