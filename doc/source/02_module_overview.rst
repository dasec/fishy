Modules Overview
================

General module structure
------------------------

The following flowchart diagram represents the logical procedure of using a
hiding technique.

.. graphviz:: resources/module_flowchart.dot

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

CLI
---

The cli forms the user interface for this toolkit. Each hiding technique is
accessible via a subcommand, which itself defines further options. The CLI
must be able to read data, that the user wants to hide either from stdin or
from a file. Hidden data which the user wants to read from a filesystem are
returned to stdout or a given file.

The cli module takes up the task of parsing the command line arguments and calls,
depending on the given subcommand, the appropriate `Hiding technique wrapper`.

If reading data from a file, the cli is in charge of turning it into a buffered
stream, on which the hiding technique operates.

.. note:: The `CLI` is limited to store only one file per call and won't honour
          other files already written to disk.

Hiding technique wrapper
------------------------

Each type of hiding technique has its own wrapper. This hiding technique wrapper
gets called by the CLI and calls the filesystem specific `hiding technique
implementation`, based on the filesystem type. To detect the filesystem type, the
`filesystem detector` function is called.

Read and clear methods of the hiding techniques require some metadata which
are gathered during a write operation. So the hiding technique wrapper is also
responsible for reading and writing metadata files and providing hiding technique
specific metadata objects for read and write methods.

If the user wants to read hidden data into a file instead of stdout, the hiding
technique wrapper is in charge of opening and writing this file.

Hiding technique
----------------

The hiding technique implementations do the real work of this toolkit. Every
hiding technique must at least offer a read, write and a clear method. They
must operate on streams only to ensure high reusability and reduce boilerplate
code.

All hiding techniques are called by a `hiding technique wrapper`.

To get required information about the filesystem the hiding techniques use
either the `pytsk3` library or use a filesystem parser implementation located
in the aproppriate filesystem package.

The clear method must overwrite all hidden data with zeros and leave the filesystem
in a consistent state.

.. warning:: The clear method does not perform erasure of data in terms of any
             regulatory compliance. It does not ensure that all possible traces
             are removed from the filesystem. So, don't rely on this method to
             securely wipe hidden data from disk.

If a hiding technique needs some metadata to restore hidden data, it must
implement a hiding technique specific metadata class. This is used during the
write process to store those necessary information. The write method must return
this metadata instance, so that the `hiding technique wrapper` can serialize it
and pass it to the read and clear methods.

If a write method failes, already written data must be cleared before exiting.

Hiding techniques may implement furter methods.

Filesystem detector
-------------------

The filesystem detector is a simple wrapper function to unify calls to the
filesystem specific detection functions, which are implemented in the
corresponding filesystem package.

Metadata handling
-----------------

To be able to restore hidden data, most hiding techniques will need some
additional information. These information will be stored in a metadata file.
The `fishy.metadata` class provides functions to read and write metadata files
and automatically de-/encrypting the metadata if a password is provided.
The purpose of this class is to ensure, that all metadata files have a similar
datastructure. Though the program can detect at an early point, that for example
a user uses the wrong hiding technique to restore hidden data. This metadata class
we can call the 'main-metadata' class.

When implementing a hiding technique, this technique must implement its own,
hiding technique specific, metadata class. So the hiding technique itself defines
which data will be stored. The write method then returns this technique specific
metadata class which then gets serialized and stored in the main-metadata.
