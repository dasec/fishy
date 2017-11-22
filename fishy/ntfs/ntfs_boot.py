import os
import hashlib

class NTFSMeta: 

	""" init: open ntfs image
		file: saves file name
	""" 
	def __init__(self, file):
		self.file = file
		
		if os.path.isfile(self.file): 
			# test.is_ntfs() TODO is this needed?
		
		else:
			print ("file does not exist.")
			return 0

	""" is_altered:
		compare boot sector with the backup boot sector (via hash values)
			true: the sector was altered
			false: the sector was not altered
	"""
	def is_altered(self): 
		offset = 512 # sector size TODO needs to be determined dynamically
		try:
			# open file
			file = open(self.file, "rb")
			data = file.read(offset)
			# create hash value for boot sector
			hash_boot = hashlib.md5()
			hash_boot.update(data)
			
			# determine file size
			statinfo = os.stat(self.file)
			# skip to last partition (backup boot sector)
			file.seek(statinfo.st_size - offset)
			backup = file.read(offset)
			# create hash value for backup boot sector
			hash_back = hashlib.md5()
			hash_back.update(backup)
			
			# compare hash values
			if hash_boot.hexdigest() == hash_back.hexdigest():
				# nothing to do here
				print("boot sector was not compromised.")
				return False
			else:
				# compromised, further action required
				return True
		except IOError:
			return 0
		finally:
			file.close()

	def scanBoot(self):
		with open(filename, "rb") as f:
			offset = 512
			current_pos = 0
			last = os.stat(filename).st_size - offset
			while current_pos < offset:
				# switch cursor between current position at boot & backup sector
				f.seek(0 + current_pos)
				c = f.read(1)
				f.seek(last + current_pos)
				d = f.read(1)
				if not c:
					print "End of file"
					break
				if not c == d:
					# do something 
					print c
				current_pos = current_pos + 1

