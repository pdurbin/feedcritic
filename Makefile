all:
	go run feedcritic.go -mode=1
	go run feedcritic.go -mode=2
clean:
	rm -f *.xml opml.json files.json podcastdescriptions.json latest.json podcasts.json
