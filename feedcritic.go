package main

import (
	"encoding/csv"
	"encoding/json"
	"encoding/xml"
	"flag"
	"fmt"
	"html/template"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

func main() {

	var mode = flag.Int("mode", 1, "Mode 1 downloads the feeds locally and mode 2 operates on locally downloaded files.")
	flag.Parse()
	var opmlFile = "antennapod-feeds.opml"
	var filesDownloaded = "files.json"
	var fileDetails = "details.json"
	var fileLatest = "latest.json"
	var podcastsAsJsonFile = "podcasts.json"
	var podcastsTsvFile = "podcasts.tsv"
	// Based on the feeds in the OPML file, download each feed to 1.xml, 2.xml, etc.
	if *mode == 1 {
		bytes, _ := ioutil.ReadFile(opmlFile)
		var doc OPML
		xml.Unmarshal(bytes, &doc)
		var podcast Podcast
		var count = 0
		var filemap map[string]Podcast
		filemap = make(map[string]Podcast)
		for _, outline := range doc.Body.Outlines {
			count++
			podcast.Title = outline.Title
			podcast.Feed = outline.XMLURL
			podcast.URL = outline.HTMLURL

			var xmlFile = strconv.Itoa(count) + ".xml"
			filemap[xmlFile] = podcast

			url := podcast.Feed

			response, e := http.Get(url)
			if e == nil {
				//log.Fatal(e)

				defer response.Body.Close()

				file, err := os.Create(xmlFile)
				if err != nil {
					//log.Fatal(err)
				}
				_, err = io.Copy(file, response.Body)
				if err != nil {
					//log.Fatal(err)
				}
				file.Close()
			}

		}
		// FIXME: Got this error so files.json wasn't created. :(
		// 2017/03/11 16:42:01 Get http://www.ladylovescode.com/category/podcast/feed/: dial tcp: lookup www.ladylovescode.com on 127.0.1.1:53: no such host
		//exit status 1

		jsonData, _ := json.MarshalIndent(filemap, "", "  ")
		ioutil.WriteFile(filesDownloaded, jsonData, 0644)
	}
	// Parse XML files downloaded previously (1.xml, 2.xml, etc.).
	if *mode == 2 {
		var podmap map[string]Podcast
		podmap = make(map[string]Podcast)
		file, e := ioutil.ReadFile(filesDownloaded)
		if e != nil {
			fmt.Printf("File error: %v\n", e)
			os.Exit(1)
		}
		var filemap map[string]Podcast
		json.Unmarshal(file, &filemap)
		var allEpisodes []Episode
		for k, v := range filemap {
			var podcast Podcast
			filename := k
			podcast.Filename = filename
			xml, _ := ioutil.ReadFile(filename)
			feed, feedOk, err := parseFeedContent(xml)
			if err == nil {
				if feedOk {
					podcast.Description = feed.Description
					podcast.Title = feed.Title
					podcast.URL = feed.Link

					smalldate := "9999999"
					bigdate := "0"
					for _, each := range feed.ItemList {
						// episodeTitle := strings.TrimSpace(each.Title)
						pubDate := ParsePubDate(each.PubDate)
						if pubDate == "0001-01-01" {
							pubDate = ParseDcDate(each.DcDate)
						}
						var episode Episode
						episode.Title = each.Title
						episode.PubDate = pubDate
						episode.Link = each.Link
						episode.Podcast = feed.Title
						//episode.Description = each.Description
						allEpisodes = append(allEpisodes, episode)
						if pubDate > bigdate {
							bigdate = pubDate
						}
						if pubDate < smalldate {
							smalldate = pubDate
						}
					}
					podcast.Latest = bigdate

				}
			} else {
				//		fmt.Println("problem with " + filename + ": " + port)
			}
			podmap[v.Feed] = podcast
		}
		jsonData2, _ := json.MarshalIndent(podmap, "", "  ")
		//fmt.Println(string(jsonData2))
		ioutil.WriteFile(fileDetails, jsonData2, 0644)

		sort.Sort(ByDate(allEpisodes))
		allEpisodesAsJson, _ := json.MarshalIndent(allEpisodes, "", "  ")
		ioutil.WriteFile(fileLatest, allEpisodesAsJson, 0644)

	}
	// Create podcasts.json which index.html and feedcritic.js will use to render information about the podcasts on an HTML page. If a podcasts.tsv file is present, we will supplement the information with fields such as rating, titleFromFeed, and dead.
	if *mode == 3 {

		var allPodcasts []Podcast
		file, e := ioutil.ReadFile(fileDetails)
		if e != nil {
			fmt.Printf("File error: %v\n", e)
			os.Exit(1)
		}
		var podmap map[string]Podcast
		json.Unmarshal(file, &podmap)

		csvFile, tsvOpenError := os.Open(podcastsTsvFile)
		if tsvOpenError != nil {
			//fmt.Printf("Could not %v ... but we'll get by without it.\n", tsvOpenError)
			for _, v := range podmap {
				// FIXME: sometimes there isn't a title
				allPodcasts = append(allPodcasts, v)
			}
			sort.Sort(ByTitle(allPodcasts))
			podcastsAsJsonData, _ := json.MarshalIndent(allPodcasts, "", "  ")
			ioutil.WriteFile(podcastsAsJsonFile, podcastsAsJsonData, 0644)
		} else {

			defer csvFile.Close()

			reader := csv.NewReader(csvFile)
			reader.Comma = '\t'

			reader.FieldsPerRecord = -1

			_, _ = reader.Read() // delete header

			csvData, err := reader.ReadAll()

			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}

			var allPodcasts2 []Podcast
			var podcast Podcast
			for _, each := range csvData {
				podcast.Title = each[4]
				podcast.Feed = each[5]
				podcast.Description = podmap[podcast.Feed].Description
				podcast.URL = podmap[podcast.Feed].URL
				podcast.Latest = podmap[podcast.Feed].Latest
				allPodcasts2 = append(allPodcasts2, podcast)
			}
			podcastsAsJsonData, _ := json.MarshalIndent(allPodcasts2, "", "  ")
			ioutil.WriteFile(podcastsAsJsonFile, podcastsAsJsonData, 0644)
		}
	}
}

type Podcast struct {
	Title       string `json:"title"`
	Feed        string `json:"feed"`
	URL         string `json:"url"`
	Description string `json:"description"`
	Filename    string
	Latest      string `json:"latest"`
	//Latest      string `json:"updated"`
	/*
	   "title": "Functional Geekery",
	   "url": "",
	   "description": "Functional Geeks, Geeking Functionally",
	   "feed": "https://www.functionalgeekery.com/feed/mp3/",
	   "updated": "2017-03-07",
	   "titleFromFeed": "000 Functional Geekery",
	   "rating": "5",
	   "dead": "",
	*/

}

type Episode struct {
	Title       string
	Link        string
	PubDate     string
	Podcast     string
	Description template.HTML
}

type OPML struct {
	Body Body `xml:"body"`
}

type Body struct {
	Outlines []Outline `xml:"outline"`
}

type Outline struct {
	Title   string `xml:"title,attr"`
	XMLURL  string `xml:"xmlUrl,attr"`
	HTMLURL string `xml:"htmlUrl,attr"`
}

type ByDate []Episode

func (a ByDate) Len() int           { return len(a) }
func (a ByDate) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByDate) Less(i, j int) bool { return a[i].PubDate > a[j].PubDate }

type ByTitle []Podcast

func (a ByTitle) Len() int           { return len(a) }
func (a ByTitle) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByTitle) Less(i, j int) bool { return a[i].Title < a[j].Title }

// modified from https://github.com/siongui/userpages/blob/master/content/code/go-xml/parseFeed.go
func parseFeedContent(content []byte) (Rss2, bool, error) {
	v := Rss2{}
	err := xml.Unmarshal(content, &v)
	if err != nil {
		if err.Error() == atomErrStr {
			// try Atom 1.0
			//return parseAtom(content), err
		}
		//log.Println(err)
		return v, false, err
	}
	if v.Version == "2.0" {
		// RSS 2.0
		for i, _ := range v.ItemList {
			if v.ItemList[i].Content != "" {
				v.ItemList[i].Description = v.ItemList[i].Content
			}
		}
		return v, true, err
	}

	log.Println("not RSS 2.0")
	return v, false, err
}

type Rss2 struct {
	XMLName     xml.Name `xml:"rss"`
	Version     string   `xml:"version,attr"`
	Title       string   `xml:"channel>title"`
	Link        string   `xml:"channel>link"`
	Description string   `xml:"channel>description"`
	PubDate     string   `xml:"channel>pubDate"`
	ItemList    []Item   `xml:"channel>item"`
}

type Item struct {
	Title       string        `xml:"title"`
	Link        string        `xml:"link"`
	Description template.HTML `xml:"description"`
	Content     template.HTML `xml:"encoded"`
	PubDate     string        `xml:"pubDate"`
	DcDate      string        `xml:"date"`
}

const atomErrStr = "expected element type <rss> but have <feed>"

func ParsePubDate(datein string) string {
	//log.Println(datein)
	datein = strings.TrimSpace(datein)
	parsedTime, err := time.Parse(time.RFC1123Z, datein)
	if err != nil {
		parsedTime, err = time.Parse(time.RFC1123, datein)
		if err != nil {
			// added for http://leoville.tv/podcasts/floss.xml etc.
			parsedTime, err = time.Parse("Mon, _2 Jan 2006 15:04:05 -0700", datein)
			if err != nil {
				// Monday, 7 December 2015 9:30:00 EST
				parsedTime, err = time.Parse("Monday, _2 January 2006 15:04:05 MST", datein)
				if err != nil {
					// 22 Dec 2015 03:00:00 GMT
					parsedTime, err = time.Parse("02 Jan 2006 15:04:05 MST", datein)
				}
			}
		}
	}
	customTime := parsedTime.Format("2006-01-02")
	return customTime
}

func ParseDcDate(datein string) string {
	//log.Println(datein)
	parsedTime, _ := time.Parse(time.RFC3339, datein)
	customTime := parsedTime.Format("2006-01-02")
	return customTime
}
