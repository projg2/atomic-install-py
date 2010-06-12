#	vim:fileencoding=utf-8
# (C) 2010 Michał Górny <gentoo@mgorny.alt.pl>
# Released under the terms of the 3-clause BSD license.

import os, stat

class FilesystemChanged(Exception):
	pass
class InvalidCallOrder(Exception):
	pass

class FileType:
	file = 1
	dir = 2

	@classmethod
	def from_stat(cls, st):
		stm = st.st_mode
		if stat.S_ISREG(stm):
			return cls.file
		elif stat.S_ISDIR(stm):
			return cls.dir
		else:
			return None

class AtomicInstall:
	mergingprefix = '.MERGING-'
	strayprefix = '.STRAY-'

	def __init__(self, image, root, allowedcollision = None):
		self.image = image
		self.root = root
		self.allowedcollision = allowedcollision

	def check(self):
		""" Check whether all the file types inside 'image' are supported
		and whether there are no collisions. """

		out = {
			'notsupported': [],
			'notsupportedreplace': [],
			'collision': [],
			'unacceptable': []
		}
		fl = []

		imagelen = len(self.image)
		for (fp, dirs, files) in os.walk(self.image):
			p = fp[imagelen:]
			dp = os.path.join(self.root, p)
			for fn in dirs + files:
				rf = os.path.join(p, fn)
				f = os.path.join(fp, fn)
				# if we make sure those aren't installed
				# we don't need to worry when replacing them
				if fn.startswith(self.mergingprefix) or fn.startswith(self.strayprefix):
					out['unacceptable'].append(rf)
				try:
					st = os.lstat(f)
				except OSError:
					raise FilesystemChanged('%s disappeared!' % f)
				stt = FileType.from_stat(st)
				if not stt:
					out['notsupported'].append(rf)
					continue

				d = os.path.join(dp, fn)
				try:
					dst = os.lstat(d)
				except OSError:
					dst = None
					ddp = d
					while dst is None:
						 (ddp,_ddpfn) = os.path.split(ddp)
						 try:
							 dst = os.lstat(ddp)
						 except OSError:
							 if ddp == '' and _ddpfn == '':
								 raise
					dstt = None
				else:
					dstt = FileType.from_stat(dst)
					if self.allowedcollision and rf not in self.allowedcollision:
						out['collision'].append(rf)
						continue

				fl.append((rf, f, d, stt, dstt, st, dst))

		for k,v in out.items():
			if v:
				return (out,fl)
		
		self.filelist = fl
		return (out,fl)

	def prepare(self, progresscb = None):
		""" Prepare all the files for the atomic rename. Copy them to the target
		filesystem if necessary. Update the movelist. """

		try:
			fl = self.filelist
		except AttributeError:
			raise InvalidCallOrder('check() needs to be called before prepare() and needs not to return any problems.')

		outfl = []
		moves = []
		for rf, f, d, stt, dstt, st, dst in fl:
			if st.st_dev != dst.st_dev:
				raise Exception('XXX: copy the file')
			if dstt and dstt != stt: # need to get rid of stray file
				(dir, fn) = os.path.split(rf)
				sname = os.path.join(dir, self.strayprefix + fn)
				ssrc = os.path.join(self.root, rf)
				sdst = os.path.join(self.root, sname)
				outfl.append((sname, ssrc, sdst, dstt, None, dst, None))
				moves.append((rf, sname))
				if progresscb:
					progresscb(('move', rf, sname))
			outfl.append((rf, f, d, stt, dstt, st, dst))
			if progresscb:
				progresscb(('install', rf))

		self.filelist = outfl
		self.moves = moves
		return outfl

	def merge(self):
		""" Perform the atomic rename. Return a list of collision-protected
		file moves (which needed to be done to make space for new files) -- it
		should be used to update the filelist used to remove replaced packages.
		"""

		try:
			fl = self.filelist
		except AttributeError:
			raise InvalidCallOrder('check() and prepare() need to be called before merge().')

		for rf, f, d, stt, dstt, st, dst in fl:
			os.rename(f, d)

		return self.moves

	def cleanup(self):
		""" Remove any leftover files. """

		pass

	def rollback(self, list):
		""" Rollback changes performed by prepare() if merge() hasn't started
		yet, using the saved filelist. """

		pass

	def replay(self, list):
		""" Replay the merge() using the saved filelist. """

		pass
