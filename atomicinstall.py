#	vim:fileencoding=utf-8
# (C) 2010 Michał Górny <gentoo@mgorny.alt.pl>
# Released under the terms of the 3-clause BSD license.

import os, shutil, stat

class FilesystemChanged(Exception):
	pass
class InvalidCallOrder(Exception):
	pass

class FileType:
	file = 1
	dir = 2
	link = 3

	@classmethod
	def from_stat(cls, st):
		stm = st.st_mode
		if stat.S_ISREG(stm):
			return cls.file
		elif stat.S_ISDIR(stm):
			return cls.dir
		elif stat.S_ISLNK(stm):
			return cls.link
		else:
			return None

class FileRec:
	def __init__(self, rf, f, d, stt, dstt, st = None, dst = None, ddp = None):
		self.name = rf
		self.f = f
		self.d = d
		self.ftype = stt
		self.dtype = dstt
		self.fstat = st
		self.dstat = dst
		self.dparentpath = ddp

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
			'unacceptable': [],
			'leftoverstray': []
		}
		fl = []

		imagelen = len(self.image)
		for (fp, dirs, files) in os.walk(self.image):
			p = fp[imagelen:].lstrip('/')
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
					elif stt != dstt:
						# check for leftover moved stray files
						(dir, fn) = os.path.split(d)
						sname = os.path.join(dir, self.strayprefix + fn)
						if os.path.exists(sname):
							out['leftoverstray'].append(rf)
							continue
					ddp = None

				fl.append(FileRec(rf, f, d, stt, dstt, st, dst, ddp))

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
		dirignore = []

		for f in sorted(fl, key=lambda x: x.name):
			for di in dirignore:
				# was the directory 'moved' already?
				if f.name.startswith(di):
					if progresscb:
						progresscb(('install', f.name))
					break
			else:
				# stray file handling
				if f.dtype and f.dtype != f.ftype: # need to get rid of stray file
					(dir, fn) = os.path.split(f.name)
					sname = os.path.join(dir, self.strayprefix + fn)
					ssrc = os.path.join(self.root, f.name)
					sdst = os.path.join(self.root, sname)
					outfl.append(FileRec(sname, ssrc, sdst, f.dtype, None, f.dstat))
					moves.append((f.name, sname))
					if progresscb:
						progresscb(('move', f.name, sname))
				# report the filename before copying it
				if progresscb:
					if f.ftype == FileType.link:
						progresscb(('link', f.name, os.readlink(f.f)))
					else:
						progresscb(('install', f.name))
				# directories need to be treated specially
				# if they exist, we ignore the dir itself and just move the files
				# if they do not, we move the whole dir and ignore the files
				if f.ftype == FileType.dir and not f.dtype:
					dirignore.append(os.path.join(f.name, ''))
				if f.ftype != FileType.dir or not f.dtype:
					# cross-device moving
					if f.fstat.st_dev != f.dstat.st_dev:
						(dir, fn) = os.path.split(f.name)
						mname = os.path.join(dir, self.mergingprefix + fn)
						mpath = os.path.join(self.root, mname)
						# we assume .MERGING* is ours and can remove it
						if os.path.exists(mpath):
							shutil.rmtree(mpath)
						if f.ftype == FileType.file:
							shutil.copy2(f.f, mpath)
						elif f.ftype == FileType.dir:
							shutil.copytree(f.f, mpath, symlinks=True)
						f.f = mpath
					outfl.append(f)

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

		for f in fl:
			os.rename(f.f, f.d)

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
