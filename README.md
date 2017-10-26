# fishy
Toolkit for filesystem hiding techniques

# Techniques we found

* FAT:
	* Disk Slack
		* Simple: Only writing to slackspace of one file  [✓]
		* Advanced: Writing to slackspace of multiple files
	* Partition Slack
	* Mark Clusters as 'bad', but write content to them
	* Allocate More Clusters for a file
	* Overwrite Bootsector Copy?
	* Overwrite FAT Copies when they are not FAT0 or FAT1

# Installation

By now there is no ready to use install routine. But to install all required python modules you need, simply run:
```
sudo pip install -r requirements.txt
```

# Development

* with `create_testfs.sh` you can create test filesystem, which already contain files
