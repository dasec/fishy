Module Descriptions
===================

General module structure
------------------------

The following flowchart diagram represents the logical procedure of using a
hiding technique.

.. graphviz:: module_flowchart.dot

The `CLI` evaluates the command line parameters and calls the appropriate `hiding
technique wrapper`.
The `hiding technique wrapper` then checks for the filesystem type of the given
filesystem image and calls the specific `hiding technique` implementation for
this filesystem.
In case of calling the write method, the `hiding technique` implementation
returns metadata, which it needs to restore the hidden data later. This metadata
is written to disk, using a simple json datastructure.

The command line argument parsing part is implemented in the `cli.py` module.
`Hiding techniques wrapper` are located in the root module.
They adopt converting input data into streams, casting/reading/writing hiding
technique specific metadata and calling the appropriate methods of those hiding
technique specific implementations.
To detect the filesystem type of a given image, the `Hiding techniques wrapper`
use the `filesystem_detector`, which uses filesystem detection methods, implemented
in the particular filesystem module.
Filesystem specific `hiding technique` implementations provide at least a write,
read and a clear method to hide/read/delete data.
`Hiding technique` implementation use either `pytsk3` to gather information of
the given filesystem or use custom filesystem parsers, which then are located
under the particular filesystem package.


Filesystem Implementations
--------------------------

FAT Filesystem
**************

This toolkit uses its own FAT implementation, supporting FAT12, FAT16 and FAT32.
It implements most of parsing the filesystem and some basic write operations,
which can be used by hiding techniques.

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
