The current state of the project offers enough functionality to hide data in our chosen filesystems. However there is still room for improvement of some features. This section lists a brief overview of some potential key points. 

The filesystem auto detection for FAT and NTFS needs improvement. It is currently performed by checking an ASCII string in the boot sector. In order to increase the reliability of fishy, it should be improved. 

Likewise, at present the clearing technique used for hiding techniques -c option is kept rather simple. A more secure clearing technique would be preferred. 

Related to it is the (lack of) hidden data encryption. At the current state it is not provided by fishy but left to the user. It would be useful to provide an option that enables fishy to encrypt the data by itself. 

Another potential feature is the hiding of metadata itself in the filesystem. One possible implementation of this feature is a hiding technique exclusively 
for metadata. 

Lastly, the implementation of multiple data support would be a welcome addition. This includes but is not limited to the implementation of a fuse filesystem, which can use multiple hiding techniques to store data, the option to enable hiding techniques to hide multiple files, to provide an easier usage, or the addition of multiple metadata file support to ext4's info switch.
