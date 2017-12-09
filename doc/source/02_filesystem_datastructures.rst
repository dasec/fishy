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
