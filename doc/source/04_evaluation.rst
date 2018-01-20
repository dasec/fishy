Evaluation
==========

This section summarizes some evaluations we made for the different implemented
hiding techniques.

FileSlack
---------

* **Gained capacity**: Depending on the configured block and cluster size as well
  as the size of the original file, that is used to hide data, this hiding technique
  can store *(cluster_size - block_size) x storable_files*. Though the gained capacity is very high.
* **Detection rate**: A check with fsck.fat neither detected the hidden files, nor
  showed any other suspicious output. Same for chkdsk on NTFS.
* **Stability**: Low. If the original file changes in size, the hidden data might be
  overwritten by further writes. So, this technique should preferably used with
  non-changing filesystems or files that don't change.

MFTSlack
--------

* **Gained capacity**: Depending on the allocated MFT entry size as well
  as the actual size of data in each entry, that is used to hide data, this hiding
  technique can store *(allocated_size - actual_size) - 2 bytes per fixup value in slack*.
  Though the gained capacity is high.
* **Detection rate**: With the --domirr option a check with chkdsk neither detected the hidden files,
  nor showed any other suspicious output. Without chkdsk detects an error in the $MFTMirr.
* **Stability**: Low. If attributes in the original mft entry change, the hidden data might be
  overwritten. So, this technique should preferably used with non-changing filesystems.