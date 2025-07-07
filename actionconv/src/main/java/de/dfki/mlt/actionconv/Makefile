ROOT       = $(HOME)/src/external/jflex
#JFLEX      = $(ROOT)/jflex/bin/jflex
JFLEX	   = jflex
JAVA       = java
JAVAC      = javac
BISON	   = bison


# --------------------------------------------------

%.java : %.y
	$(BISON) -Wall -rall --language java --debug $<
#	$(BISON) -Wall -rall --language java -Wcounterexamples --debug $< 2>&1 | tee counterexamples.out

all: CondParser.java

clean:
	rm -f *.class
	rm -f *~
	rm -f CondParser.java
	rm -f CondParser.output
