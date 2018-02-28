This file collects issues, that were still open at the time of our commitment.

# Checksums

* We should calculate checksums over input data to detect information loss while reading hidden data
* Maybe [rolling hashes](https://en.wikipedia.org/wiki/Rolling_hash) might be the thing we should use, because with them we don't need to buffer the whole input first, before we can write it to disk.
* Or we refer to archive formats like zip, which have error detection. This way we follow the unix philosophy and don't make things too complicated

# FileSlack: possible overwrites in directory autoexpand feature

If a user supplies a directory plus a file in this directory as destinations for fileslack exploitation, the autoexpansion of directories could lead to multiple writes into the slack space of the same file. For instance:
```
$ fishy -d testfs_fat12.dd fileslack -w -m "meta.json" -d adir/afile.txt -d adir longfile.txt
```
would first write into `adir/afile.txt`, then expand `adir` to `adir/afile.txt` and then write again into the slack space of `adir/afile.txt`.

This is an issue in FAT fileslack implementation, but I'm not sure if the NTFS implementation is affected.

# Refine cli interface

The are some inconsistencies in the cli interface.

* The `metadata` subcommand does not require a device (`-d`), but all other commands do.
* The info option of `fileslack` subcommand should not require a metadata file

Also it might be nicer to move the `-d` option behind the subcommand.

The argparse configuration should require all options which are actually required and should not require options, which are not required...

* Maybe we should seperate informational functionality (fattools, metadata) from hiding techniques via additional subgroups
* Read/write/clear/info options of a hiding technique should only be used once at a time. We could propably implement this via `add_mutually_exclusive_group`
* for fileslack subcommand, the `-d` option must be required, when writing to fileslack

Some other things are wrong or need extension in the help output:
* as the mftslack options were copied from fileslack, this keyword occures in the help output, but is wrong there.
* subcommand help output should be more descriptive

# FAT, NTFS: construct incompatibility

The construct library changed some things in their recent 2.9.X release so that our code is currently incompatible with their current version.

Maybe someone has the time to fix those incompatibilities. Meanwhile I will fix our requirements to construct in its pre 2.9 version.
