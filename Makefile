
TESTDIR ?= /tmp/ai
SRC = $(TESTDIR)/src
DST = $(TESTDIR)/dst

testenv: clean
	mkdir -p $(SRC)/c/a $(SRC)/c/b $(DST)
	echo 11 > $(SRC)/a
	echo 12 > $(SRC)/b
	ln -s /dupa $(SRC)/c/test
	mkdir $(DST)/a
	echo 150 > $(SRC)/c/a/11
	echo 150 > $(SRC)/c/b/11
	ln $(SRC)/a $(SRC)/c/z

clean:
	rm -rf $(TESTDIR)
