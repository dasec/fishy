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

Most filesystem implementations for FAT and NTFS pad the RAM Slack with zeros,
nowadays. This padding behaviour must be honoured by our implementation, as
non-zero values in this area would be suspicious to any observer.

We can use these observations to define the general process of hiding data into
the File Slack.

1. Find the last cluster of a file, which File Slack shall be exploited
2. Calculate the start of the Drive Slack
3. Write data until no data is left or the end of the cluster is reached
