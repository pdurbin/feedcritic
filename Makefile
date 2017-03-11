all:
	go run feedcritic.go -mode=1
	go run feedcritic.go -mode=2
clean:
	rm -f *.xml files.json podcastdescriptions.json
