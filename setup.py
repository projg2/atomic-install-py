#!/usr/bin/python
#	vim:fileencoding=utf-8
# (C) 2010 Michał Górny <gentoo@mgorny.alt.pl>
# Released under the terms of the 3-clause BSD license.

from distutils.core import setup

setup(
	name = 'atomicinstall',
	version = '0.1',
	description = 'Atomically install an image of files onto the live filesystem',
	author = 'Michał Górny',
	packages = ['atomicinstall'],
	license = 'BSD'
)
