Modules Overview
================

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

Metadata handling
-----------------

To be able to restore hidden data, most hiding techniques will need some
additional information. These information will be stored in a metadata file.
The `fishy.metadata` class provides such a class that will be used to read and
write metadata files. The purpose of this class is to ensure, that all metadata
files have a similar datastructure. Though the program can detect at an
early point, that for example a user uses the wrong hiding technique to restore
hidden data. This metadata class we can call the 'main-metadata' class

When implementing a hiding technique, this technique must implement its own,
hiding technique specific, metadata class. So the hiding technique itself defines
which data will be stored. The write method then returns this technique specific
metadata class which then gets serialized and stored in the main-metadata.
