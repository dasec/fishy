# CLI

* Shorter subcommand name(s)
* Autodetect filesystem type and check if requested hiding technique is available for it

# Checksums

* We should calculate checksums over input data to detect information loss while reading hidden data
* Maybe [rolling hashes](https://en.wikipedia.org/wiki/Rolling_hash) might be the thing we should use, because with them we don't need to buffer the whole input first, before we can write it to disk.
* Or we refer to archive formats like zip, which have error detection.

# Metadata

To restore hidden data we need to store some additional information about the data that was hidden and the location the information was written to.

## Capabilities of such a metadata module

* Encrypt/decrypt the metadata file with a password

## What to store

* Hiding technique identifier
* Stored data checksum
* Stored data length

# FAT

## Simple Disk Slack

* add length option to read method to avoid outputting empty bytes
* read chunks instead of whole input and write progressively to disk
* Padded RAM Slack: As [1] points out, RAM Slack is (on NTFS -.-) padded with zeros, so we should give the option (or enforce) that data, written to file slack space, starts at drive slack (at the start of the next sector). Needs further research for FAT implementations.

[1]: https://www.scribd.com/document/6642954/Ntfs-Hidden-Data-Analysis
