#!/usr/bin/python

from atomicinstall import AtomicInstall
import os

testdir = '/tmp/ai'

os.system('make TESTDIR=%s testenv' % testdir)
a = AtomicInstall('%s/src' % testdir, '%s/dst' % testdir)

def printfl(fl):
	for rf, f, d, stt, dstt, st, dst in fl:
		print '%s: %s -> %s' % (rf, f, d)

def printcb(fle):
	if fle[0] == 'move':
		print '>>> /%s <= /%s' % (fle[2], fle[1])
	elif fle[0] == 'install':
		print '>>> /%s' % fle[1]

# P: engage the lock here
print 'check()'
a.check()
# P: write MERGING vdb entry (with notice that real merge wasn't started)
print 'prepare()'
a.prepare(printcb)
# P: write MERGING vdb entry (with notice that real merge was started)
print 'merge()'
a.merge()
# P: write real vdb entry
print 'cleanup()'
a.cleanup()
# P: release the lock
