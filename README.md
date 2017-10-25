# fishy
Toolkit for filesystem hiding techniques

# Techniques we found

* FAT:
	* Disk Slack
	* Partition Slack
	* Mark Clusters as 'bad', but write content to them
	* Allocate Clusters without adding them as directory entries
	* Overwrite Bootsector Copy?
	* Overwrite FAT Copies when they are not FAT0 or FAT1


# Development

* with `create_testfs.sh` you can create test filesystem, which already contain files
