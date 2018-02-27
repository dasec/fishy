Future Work
===========

// TODO: Form into full text  

The following list describes a few features that might be implemented in the future to
expand and improve the overall functionality.

* Use a more secure clearing technique for hiding techniques -c option
* Implement a fuse filesystem, which uses multiple hiding techniques to store data
* **Hidden data encryption**:  Currently the encryption of the data that is hidden is not provided by **fishy** but it's up to the user. Therfore it could be useful to provide an option to encrypt the data by **fishy** itself.
* **Hide Metadata**: It might be useful to provide a feature that will hide the generated metadata itself in the filesystem. One possible way to implement that feature would be to use a hiding technique exclusivly for metadata.
* **Hide multiple files**: In order to provide an easier usage it would be senseful to expand the hiding feature with the 
* **Improve filesystem autodetection**: Currently the FAT and NTFS detection is only based on a check for an ASCII string in the bootsector. So these implementations should be improved to provide a higher reliability.
* Add multiple metadata file support to ext4's info switch
