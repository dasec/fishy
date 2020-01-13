"""
interface for ntfs boot sector
"""
import os
import hashlib

class NTFSMeta:
    """ class to analyze and scan boot sector of ntfs systems.
    """
    def __init__(self, stream):
        """ init: open ntfs image
            file: saves file name
        """
        self.stream = stream
        if os.path.isfile(self.stream):
            print("ok")
            # test.is_ntfs() TODO is this needed?
        else:
            print("file does not exist.")

    def is_altered(self):
        """ is_altered:
            compare boot sector with the backup boot sector (via hash values)
            true: the sector was altered
            false: the sector was not altered
        """
        offset = 512 # sector size TODO needs to be determined dynamically
        try:
            # open file
            file = open(self.stream, "rb")
            data = file.read(offset)
            # create hash value for boot sector
            hash_boot = hashlib.sha256()
            hash_boot.update(data)
            # determine file size
            statinfo = os.stat(self.stream)
            # skip to last partition (backup boot sector)
            file.seek(statinfo.st_size - offset)
            backup = file.read(offset)
            # create hash value for backup boot sector
            hash_back = hashlib.sha256()
            hash_back.update(backup)
            # compare hash values
            if hash_boot.hexdigest() == hash_back.hexdigest():
                # nothing to do here
                print("boot sector was not compromised.")
                return False
            else:
                # compromised, further action required
                print("boot sector was compromised.")
                return True
        except IOError:
            return 0
        finally:
            file.close()

    def scan_boot_sector(self):
        """ scan_boot_sector: scans the boot sector for hidden data
        """
        with open(self.stream, "rb") as file:
            offset = 512
            # 	file.seek(0) jump to start of file needed?
            pos = file.tell()
            current_pos = 0
            last = os.stat(self.stream).st_size - offset
            while current_pos < offset:
                # switch cursor between current position at boot & backup sector
                file.seek(pos + current_pos)
                boot_c = file.read(1)
                file.seek(last + current_pos)
                back_c = file.read(1)
                if not boot_c:
                    print("End of file")
                    break
                if boot_c != back_c:
                    # do something
                    print(boot_c)
                current_pos = current_pos + 1
            file.seek(pos)
            file.close()

