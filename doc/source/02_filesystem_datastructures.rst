Filesystem Data Structures
==========================

This chapter summarizes the most important data structures of FAT, NTFS and ext4.

TODO: Write Content!

FAT
---

Despite its age, the FAT filesystem is a heavily used filesystem, most often
found on small sized devices such as USB sticks and SD-Cards.
Its simple structure makes it easy to understand and lightweight implementations
are possible.
During its evolution the original FAT specification was extended to fit the
growing disk sizes of hard drives, and resulted in various variants.
Nowadays, the most common variants are FAT12, FAT16 and FAT32.
Besides some details, which we will cover later, the main difference between
these FAT types is the address size, used for addressing clusters in
the data area.
All three FAT types share a similar structure, consisting of

* reserved sectors, including the bootsector
* file allocation table
* root directory region
* data region

Important units in a FAT filesystem are `sectors` as the smallest logical unit
for the pre data region and `clusters` as the smallest logical unit in the data
region. The size of a cluster is defined by `cluster size = sector size * 
sectors per cluster`.

Reserved Sectors
................

Reserved sectors are always located at the beginning of a FAT filesystem. The
most important types are the bootsector, which starts at offset 0 and the
FS Information Sector which is used by FAT32.

Bootsector
**********

The bootsector contains important metadata about the filesystem. It constists
of a core section, which is the same for every FAT type, and an extended region,
which differs across the different types.

Among others, the core region of the bootsector includes the sector size,
the count of sectors per cluster and the count of root directory entries.

The extended region stores the filesystem type value.
FAT32 filesystems also store the address of the root directory cluster and the
start value of the FS information sector here.

FS Information Sector
*********************

FAT32 includes a Filesystem information sector in the reserved sectors. It stores
some additional metadata about the filesystem, which can be used to increase
read and write performance. Interesting values are the count of free sectors
and the id of the last written cluster.

File Allocation Table
.....................

The File Allocation Table records the status of data clusters. Depending on the
type the size varies between 12 to 32 bit per record. Mainly there are four
different status values.

* Free cluster
* Bad cluster
* Last cluster
* Next cluster in a cluster chain

The free cluster status is used to mark a cluster as free.
This means, that during the write process this cluster can be used to write
data into.
If data was written into a cluster, the corresponding FAT entry is set to
the last cluster value.
If the written file is greater than the cluster size, multiple clusters will
be allocated. The first cluster then points to the id of the next cluster, 
creating a chain of used clusters. The last cluster in this chain is terminated
with the 'Last cluster' value.
The bad cluster status indicates a faulty sector in this cluster.
Once this status is set, the filesystem will never use this cluster again.

Root- and Subdirectories
........................

The root directory holds the start directory of the filesysten ("/"). For FAT12 and
FAT16 it starts directly behind the file allocation table. The location in FAT32
filesystems is determined by the `Root directory address` field of the bootsector.
It holds a series of directory entries.

A directory entry stores information about a file or subdirectory:

* Name
* Extension
* Attributes (subdirectory, hidden, readonly, ...)
* start cluster
* size

Subdirectory entries use the `start cluster` field to point to a cluster
that then again holds a series of directory entries.

EXT4
---

The fourth extended filesystem is ext3s successor in linux's journaling filesystems, 
firstly published in 2006 by Andrew Morton. It still supports ext3, but uses 48bit for
block numbers instead of 32bit. This results in bigger partitions up to 1 EiB. Furthermore it 
is now possible to use extends, which unite serveral contigunous blocks, improving 
handling of large files and performance. Moreover ext4 introduces better timestamps on a 
nanosecond basis, checksums for its journal and metadata, online defragmentation, flex groups and 
other improvements.

The standard block size for ext4 is 4096 byte, but 1024 and 2048 are possible, too. These 
interfere with the 'superblock-slack' hiding technique shown later. 
The filesystem itself consists of a bootsector and flex groups, holding block groups.

.. image:: _static/ext4_structure.png

Flex Groups
...........

Superblock
**********

The superblock contains general information about the filesystem bock counts and sizes, 
states, versions, timestamps and others. It is located at byte 1024 of the filesystem and 
uses 1024 byte of its block, creating a superblock-slack (depending on the block size).
Redundant copies of the superblock are stored in each block group, unless the sparse_super 
feature flag is set, which will store these redundant copies in block groups 0 and to the 
power of 3, 5 and 7 instead.
Entries are amongst other information:

* total block and inode count
* blocks per block group
* unused block count
* first unused inode
* reserved GDT block count

GDT
***

The Group Descriptor Table is located behind the superblock in the filesystem and 
gets stored accordingly. It holds group descriptor entries for each block group, containing:

* address of block bitmap
* address of inode bitmap
* address of inode table
* unused block, inode and directory count
* flags
* checksums

Inodes
******

An inode stores metadata of a file, such as:

* timestamps
* user/group permissions
* data references

The size varries, default is 256 Byte. An inode table holds a list of all inodes of its block group.

Inode Extends
*************

The extents replace ext3s indirect addressing and reduce data fragmentation. An inode can store 4 extents,
further extents can be stored in a tree structure, each mapping up to 128MiB of contiguous blocks.

.. image:: _static/ext4_extents.png

Reserved GDT Blocks
*******************

These blocks are reserved for expansion of the filesystem, which creates larger group descriptor tables.
Therefore it is usable for datahiding as long as the filesystem does not get expanded.

Journal
*******

The journal guarantees a successful write operation, after a commited data transaction is written to the disk,
it is saved to a 128MiB big section on the disk, the journal. From there it gets written to its final 
destination and can be restored in case of a power outage or data corruption during the write operation.