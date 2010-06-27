#!/bin/sh

testdir='/tmp/ai'
make TESTDIR="${testdir}" testenv
export PYTHONPATH=${PWD}/build/lib
exec ./atomicinstall "${testdir}"/src "${testdir}"/dst
