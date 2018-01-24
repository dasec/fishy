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
in a file called $MFTMirr (Brian Carrier, p.219) to be used during recovery. To avoid detecion
by a simple chkdsk it is important to write a copy of the hidden data in $MFT to the corresponding
entries in $MFTMirr. 

The process of hiding data in the MFT entry slack:

1. Find the MFT entry to hide data in
2. Calculate the slack, using the information in the MFT entry header
3. Write data and avoid the last two bytes of each sector
4. If copies exit in $MFTMirr write the same data there
