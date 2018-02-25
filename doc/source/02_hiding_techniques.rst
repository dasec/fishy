Hiding Techniques
=================

Following sections give a brief overview about each implemented hiding technique.


File Slack
----------

The smallest unit in the data area of a filesystem is called "cluster".
This unit is a fixed size value, that can often be configured at creation time
of the filesystem.
It is calculated from the `sector size * sectors per cluster`.
If a file is smaller than the cluster size of the filesystem, writing this file
will result in some unusable space, which starts at the end of the file and ends
at the end of the cluster.
This remaining space can be used to hide data and is in general called File Slack.

The File Slack itself consists of two parts: RAM Slack and Drive Slack.
The RAM Slack begins at the end of the file and ends at the end of the current
sector.
The Drive Slack reaches from the end of RAM Slack to the end of the cluster.

.. image:: _static/fileslack_image.png

Most filesystem implementations for FAT and NTFS pad the RAM Slack with zeros,
nowadays. This padding behaviour must be honoured by our implementation, as
non-zero values in this area would be suspicious to any observer.

We can use these observations to define the general process of hiding data into
the File Slack.

1. Find the last cluster of a file, which File Slack shall be exploited
2. Calculate the start of the Drive Slack
3. Write data until no data is left or the end of the cluster is reached

MFT Entry Slack
---------------

The Master File Table (MFT) contains an entry for every file and directory stored in
a NTFS partition. It contains the necessary metadata such as the file name, -size, and
the location of the stored data. MFT entries allocate a fixed size, usually 1024 bytes,
but only the first 42 bytes have a defined purpose (MFT Entry Header). The remaining bytes
store attributes, which contain the metadata for a file (e.g.: $STANDARD_INFORMATION, 
$FILE_NAME, $DATA). An MFT entry does not have to fill up all of its allocated bytes, which
often leads to some unused space at the end of an entry.

.. image:: _static/mft_entry.png

This unused space, the MFT entry slack, can still contain data of an old MFT entry,
which was previously stored in the same location. This makes the MFT entry slack an
ideal place to hide data inconspicuously.

NTFS uses a concept called Fixup (Brian Carrier, p.253) for its important data structures,
such as the MFT, in order to detect damaged sectors and corrupt data structures. When an
MFT entry is written to the disk the last two bytes of each sector are replaced with a
signature value. To avoid damaging the MFT it is important to not overwrite the last two
bytes of each sector when hiding data in the MFT entry slack.

NTFS stores a copy of at least the first four MFT entries ($MFT, $MFTMirr, $LogFile, $Volume)
in a file called $MFTMirr (Brian Carrier, p.219) to be used during recovery. To avoid detection
by a simple chkdsk it is important to write a copy of the hidden data in $MFT to the corresponding
entries in $MFTMirr. 

The process of hiding data in the MFT entry slack:

1. Find the MFT entry to hide data in
2. Calculate the slack, using the information in the MFT entry header
3. Write data and avoid the last two bytes of each sector
4. If copies exit in $MFTMirr write the same data there

Reserved Group Descriptor Tables
--------------------------------

As described in the filesystem chapter above, the reserved GDT blocks are not used until the filesystem 
is expanded and group descriptors are written to them. The reserved GDT blocks are located behind the 
group descriptors and in each of its copies, their number can read from the superblock at 0xCE.
This hiding technique can hide up to `number of reseved GDT blocks * number of block groups with copies * block size` 
bytes. The number of copies varies depending on the sparse_super flag, which limits the copies of the reserved
GDT blocks to group numbers with numbers of either 0 or to the power of 3,5 or 7, as described earlier.
On a 512Mb image with block size of 4096 bytes you can expect to hide about 64 * 2 * 4096 = 524288 Bytes.

However, this hiding method is quite obvious and might be one of the first places to look at in case you
check a ext4 filesystem for hidden data. Therefore this technique skips the original gdt and its first
copy before writing data. This prevents the file checker from noticing these flaws in the filesystem.

Process-wise the hiding technique firstly calculates the ids of reserved GDT blocks, using the 
available information from the superblock, such as total block count, blocks per group and the 
filesystem's architecture (32 or 64bit) as well as the total number of reserved GDT blocks and considering
the sparse_super flag. 
Each block group's reserved GDT block ids get written to an array of block ids and data can be written.

Advantages of this technique are the size of possible hidden data, on the other hand hidden data would be
overwritten in case of a filesystem expansion and its quite easy to find.

File Slack
----------

Superblock Slack
----------------

Depending on the block size, there is an acceptable amount of slack space following each copy of the superblock
in each block group. This is not applicable in case the block size is 1024 due to the superblock's size of 1024
byte, using all of its block alone. For the superblock's copies the sparse_super flag applies, too, which means 
less hiding space if the flag is set.
Size-wise we speak in dimensions of several Kb, each copy adding block_size - 1024 bytes of hiding space.
The first superblock makes an exception here, due to the bootsector using another 1024 bytes, leaving 
`block_size - 2048 bytes` to hide data with block size 4096.

The hiding technique collects all block ids of the superblock copies from each block group,
taking the sparse_super flag under account. The data then gets written to the slack space of each of 
these blocks, considering the filesystem's block size.

This hiding technique benefits from the superblock's characteristics, resulting in a safe storage because the
superblock slack space does not get overwritten. But like all slack space hiding methods this is easy to find,
too.

Inode
-----
osd2
****

The osd2 hiding technique uses the last two bytes of the 12 byte osd2 field, which is located at 0x74 in each inode.
This field only uses 10 bytes at max, depending on the tag being whether `linux2`, `hurd2` or `masix2`.
This results in `number of inodes * 2 bytes` hiding space, which is not much, but might be enough for small amounts
of valuable data, because its not easy to find. "Unfortunately" ext4 introduced a lot of checksums for all
kinds of metadata, which leads to invalid inode checksums. 
In an ~235Mb image with 60.000 inodes this technique could hide 120.000 bytes.

To hide data, the method writes data directly to the two bytes in the osd2 field in each inode, which address is
taken from the inode table, until there is either no inode or no data left. The method is currently limited to 4Mb.

obso_faddr
**********

The obso_faddr field in each inode at 0x70 is an obsolete fragment address field of 32bit length. 
This technique works accordingly to the osd2 technique, but can hide twice the data. 
Taking the 235Mb example from above, this method could hide 240.000 bytes.
Besides that it has the same flaws and advantages.


