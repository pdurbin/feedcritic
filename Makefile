usage:
	@echo "Run one of these:"
	@echo " -'make all DIR=path/to/deploy'"
	@echo " -'make all DIR=path/to/deploy TSV=path/to/podcasts.tsv'"
all:
	make clean
	# mode 1 is the one that's expensive since it downloads all the feeds as XML files
	make cleanxml
	go run feedcritic.go -mode=1
	go run feedcritic.go -mode=2
	# FIXME only run this if TSV was passed in
	cp $(TSV) .
	go run feedcritic.go -mode=3
	make deploy
deploy:
	echo "Copying files to $(DIR)"
	cp index.html feedcritic.js rssfeed.svg podcasts.json latest.json $(DIR)
clean:
	rm -f opml.json details.json latest.json podcasts.json podcasts.tsv
cleanxml:
	rm -f *.xml files.json
