Create test images with `create_testfs.sh`
------------------------------------------

FAT and NTFS
............

With `create_testfs.sh` you can create prepared filesystem images. These
already include files, which get copied from `utils/fs-files/`.
These file systems are intended to be used by unit tests and for developing
a new hiding technique.

The script requires:

* `sudo` to get mount permissions while creating images
* `mount` and `umount` executables
* `mkfs.vfat`, `mkfs.ntfs`, `mkfs.ext4`
* `dd` for creating an empty image file

To create a set of test images, simply run

.. code:: bash

    $ ./create_testfs.sh


The script is capable of handling "branches" to generate multiple images with a
different filestructure. These are especially useful for writing unit tests
that expect a certain file structure on the tested filesystem.

If you would like to use existing test images while running unit tests, create
a file called `.create_testfs.conf` under `utils`. Here you can define the
variable `copyfrom` to provide a directory, where your existing test images are
located. For instance:

.. code::

    copyfrom="/my/image/folder"


To build all images that might be necessary for unittests, run

... code bash
$ ./create_testfs.sh -t all



These files are currently included in the stable1 branch:

.. code::

                                                 .
    regular file                                 ├── another
    parse longfilenames in fat parser            ├── areallylongfilenamethatiwanttoreadcorrectly.txt
    parse files greater than one cluster         ├── long_file.txt
    test fail of writes into empty file slack    ├── no_free_slack.txt
    regular directory                            ├── onedirectory
    test reading files in sub directories        │   ├── afileinadirectory.txt
    parse long filenames in directories          │   ├── areallylongfilenamethatialsowanttoreadassoonaspossible.txt
    test parsing files in nested sub dirs        │   └── nested_directory
    test parsing files in nested sub dirs        │       └── royce.txt
    test if recursive directory parsing works    └── testfile.txt

Ext4
....

Currently, you have to generate the ext4 filesystem by hand.

.. code::

    dd if=/dev/zero of=file.img bs=4M count=250
    mkfs ext4 -F file.img
    sudo mkdir -p /tmp/mount_tmp/ && sudo mount -o loop,rw,sync file.img /tmp/mount_tmp
    sudo chmod -R ug+rw /tmp/mount_tmp
    sudo mv <files> /tmp/mount_tmp/


APFS
....

As of right now, you have manually create an APFS image using a macOS machine. This can be achieved through multiple means,
though it might be the most comfortable to use an external tool like AutoDMG. An official guide to create .dmg images can be found here.
Once you have acquired a .dmg image file, you need to convert it to a .dd raw image. This can be achieved following these steps:

* Use sleuthkit's mmls command to find the starting point of the container.

* Follow up by using sleuthkit's mmcat command. An example would be: mmcat apfs_image.dmg 4 > apfs_volume.dd In this example "apfs_image.dmg" would represent the name of the extracted image, "4" is the starting point found through mmls and "apfs_volume.dd" would be the name of the extracted image.