Command Line Option Reference
=============================

.. argparse::
   :module: fishy.cli
   :func: build_parser
   :prog: fishy

   fileslack 
        Implemented for following filesystems: FAT, NTFS

        Warning: When using the -d option in combination with a directory,
        make sure that no other filename in this directory is specified. Otherwise
        this would lead to multiple writes into the same slack space of this file
        and result in data loss.


   addcluster
        Implemented for following filesystems: FAT
