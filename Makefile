
SRC = $(TESTDIR)/src
DST = $(TESTDIR)/dst

testenv: clean
	mkdir -p $(SRC) $(DST)
	echo 11 > $(SRC)/a
	echo 12 > $(SRC)/b
	mkdir $(DST)/a

clean:
	rm -rf $(TESTDIR)
