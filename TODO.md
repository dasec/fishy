# CLI

* Autodetect filesystem type and check if requested hiding technique is available for it

# Checksums

* We should calculate checksums over input data to detect information loss while reading hidden data
* Maybe [rolling hashes](https://en.wikipedia.org/wiki/Rolling_hash) might be the thing we should use, because with them we don't need to buffer the whole input first, before we can write it to disk.
* Or we refer to archive formats like zip, which have error detection. This way we follow the unix philosophy and don't make things too complicated

# Metadata

To restore hidden data we need to store some additional information about the data that was hidden and the location the information was written to.

## Capabilities of such a metadata module

* Encrypt/decrypt the metadata file with a password
