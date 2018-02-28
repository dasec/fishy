Future Work
===========

The current state of the project offers enough functionality to hide data in
our chosen filesystems. However there is still room for improvement of some
features. This section gives a brief overview of some potential key points.

The filesystem auto detection for FAT and NTFS needs improvement. It is
currently performed by checking an ASCII string in the boot sector. In order to
increase the reliability of fishy, it could be reimplemented by using the
detection methods, that are already realized in regular filesystem
implementations.

Likewise, at present the clearing method for all hiding techniques just
overwrites the hidden data with zero bytes. This does not apply to any security
standards for save data removal. This area offers much room for improvements.

At the current state fishy does not provide on the fly data encryption and has
no data integrity methods implemented. As finding unencrypted data is
relatively easy with forensic tools - regardless of the hiding technique -
encrypting all hidden data by default might be a helpful addition.
As most hiding techniques are not stable, if the related files on the
filesystem change often, some data integrity methods would be useful to detect
at least, if the hidden data got corrupted in the meantime.

Currently fishy produces a metadata file with each hiding operation. Although
it can be encrypted, it is visible via conventional data access methods and
hints to hidden data. An idea to tackle this problem might be to hide the
metadata file itself.

Lastly, the implementation of multiple data support would be a welcome
addition. This includes but is not limited to the implementation of a FUSE
filesystem layer, which can use multiple hiding techniques to store data. This
would drastically lower the burden to use this toolkit on a more regular basis.
