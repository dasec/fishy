# fishy
Toolkit for filesystem based data hiding techniques

# Techniques we found

* FAT:
	* File Slack
		* Simple: Only writing to slackspace of one file  [✓]
		* Advanced: Writing to slackspace of multiple files
	* Partition Slack
	* Mark Clusters as 'bad', but write content to them
	* Allocate More Clusters for a file
	* Overwrite Bootsector Copy?
	* Overwrite FAT Copies when they are not FAT0 or FAT1

# Installation

```bash
$ sudo pip install -r requirements.txt
$ sudo python setup.py install
```

# Usage

Currently only hiding in slack space of a single file on FAT filesystems is available:

```bash
# write into slack space
$ echo "TOP SECRET" | fishy -d testfs-fat12.dd fatsimplefileslack -f myfile.txt -w
# read from slack space
$ fishy -d testfs-fat12.dd fatsimplefileslack -f myfile.txt -r
TOP SECRET
# Wipe slack space
$ fishy -d testfs-fat12.dd fatsimplefileslack -f myfile.txt -c
```

# Development

* with `create_testfs.sh` you can create test filesystem, which already contain files
