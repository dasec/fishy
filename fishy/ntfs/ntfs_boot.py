import os
import hashlib

class NTFSMeta: 

    def __init__(self, file):
		""" init: open ntfs image
			file: saves file name
		""" 
		self.file = file
		
		if os.path.isfile(self.file): 
			print("ok")
			# test.is_ntfs() TODO is this needed?
		else:
			print ("file does not exist.")
			return 0

	def is_altered(self): 
		""" is_altered:
			compare boot sector with the backup boot sector (via hash values)
				true: the sector was altered
				false: the sector was not altered
		"""
		offset = 512 # sector size TODO needs to be determined dynamically
		try:
			# open file
			file = open(self.file, "rb")
			data = file.read(offset)
			# create hash value for boot sector
			hash_boot = hashlib.sha256()
			hash_boot.update(data)
			
			# determine file size
			statinfo = os.stat(self.file)
			# skip to last partition (backup boot sector)
			file.seek(statinfo.st_size - offset)
			backup = file.read(offset)
			# create hash value for backup boot sector
			hash_back = hashlib.sha256()
			hash_back.update(backup)
			
			# compare hash values
			if hash_boot.hexdigest() == hash_back.hexdigest():
				# nothing to do here
				print ("boot sector was not compromised.")
				return False
			else:
				# compromised, further action required
				print ("boot sector was compromised.")
				return True
		except IOError:
			return 0
		finally:
			file.close()

	def scanBoot(self):
		""" scanBoot: scans the boot sector for hidden data
		"""
		with open(self.file, "rb") as f:
			offset = 512
		# 	f.seek(0) jump to start of file needed?
			pos = f.tell()
			current_pos = 0
			last = os.stat(filename).st_size - offset
			while current_pos < offset:
				# switch cursor between current position at boot & backup sector
				f.seek(pos + current_pos)
				c = f.read(1)
				f.seek(last + current_pos)
				d = f.read(1)
				if not c:
					print ("End of file")
					break
				if not c == d:
					# do something 
					print(c)
				current_pos = current_pos + 1
			f.seek(pos)


