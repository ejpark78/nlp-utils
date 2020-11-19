
# dmz
open-dmz:
	ssh -fqN \
	  	-L 12376:localhost:2376 \
	 	-L 27018:localhost:27017 \
	 	-L 19200:localhost:9200 \
	 	gandalf01

close-dmz:
	ps -ef | grep gandalf01 | grep fqN | perl -ple 's/\s+/\t/g' | cut -f2 | xargs kill
