# Feedcritic - wrangle your many podcasts

If you listen to many podcasts, Feedcritic helps you keep track of them and choose which episodes to listen to.

The main idea behind Feedcritic is to use your list of podcasts as a starting point and extract as much value as possible from each podcast "feed."

To make use of Feedcritic, you'll need to export your list of podcasts as [OPML][], as described in the "OPML Export" section below. You'll also need a server on which to install Feedcritic.

[OPML]: https://en.wikipedia.org/wiki/OPML

## Features

- See at a glance when each of your podcasts released a new episode.
- See a combined list of recent episode titles with links to show notes.
- See the official description of the podcast, retrieved from its feed.
- See the date of the oldest available episode in the feed of each podcast.
- Optionally, rate your podcasts and order them however you like.

## Screenshots

### Screenshot of Podcast View

---

![Feedcritic screenshot of podcasts view](feedcritic-screenshot-podcasts.png?raw=true)

---

### Screenshot of Episodes View

---

![Feedcritic screenshot of episodes view](feedcritic-screenshot-episodes.png?raw=true)

---

## Demo

A demo of Feedcritic can be seen at [podcasts.greptilian.com][] and you are welcome to provide feedback by creating an issue.

[podcasts.greptilian.com]: http://podcasts.greptilian.com

## OPML Export

Feedcritic is only useful to podcast enthusiasts who are able to download their list of feeds in [OPML][] format. Here are instructions on how to export your feeds as OPML:

- [AntennaPod][]: Tap the menu, then "Settings", then "OPML Export".
- [Podcasts][]: See this [apple.stackexchange post][].

[AntennaPod]: http://antennapod.org
[Podcasts]: https://itunes.apple.com/us/app/podcasts/id525463029?mt=8
[apple.stackexchange post]: http://apple.stackexchange.com/questions/97254/export-podcast-subscriptions-from-ios-podcast-app-as-opml

## System Requirements

- Linux
- [Go][] 1.2 or higher
- [Make][] (optional but currently used for deployment)

[Go]: https://golang.org
[Make]: https://www.gnu.org/software/make/

## Installation

Please note: Feedcritic is early in its development cycle and should be considered a Minimum Viable Product (MVP). No releases have been made so it should be downloaded from this git repo. If you have any trouble installing Feedcritic, please open an issue.

- Export your list of podcast subscriptions from your podcatcher in OPML format. See the "OPML Export" section above for details. Rename the file to `antennapod-feeds.opml` and copy it to your server.
- ssh to your server.
- Clone the repo with `git clone https://github.com/pdurbin/feedcritic.git` to a directory such as `~/feedcritic`.
- Place a copy of your OPML file in the directory where you cloned the git repo such as `~/feedcritic/antennapod-feeds.opml`.
- Run `make` to see how to build and run Feedcritic or look at the usage section of https://github.com/pdurbin/feedcritic/blob/master/Makefile
- Create a destination directory for the output of Feedcritic. For example, `mkdir /var/www/podcasts.greptilian.com` 
- Configure your web server to serve the destination directory to a URL of your choosing such as http://podcasts.greptilian.com .
- Run `make all DIR=/var/www/podcasts.greptilian.com` passing in as `DIR` the directory you created above.
- Run `crontab -e` to add entry to cron to run Feedcritic every night. For example, `@daily cd /home/pdurbin/feedcritic && make all DIR=/var/www/podcasts.greptilian.com`
- Optionally, create a tab-separated values (TSV) file of your podcasts to put your podcasts in a specific order and give them ratings. The format for the TSV file can be copied from http://wiki.greptilian.com/podcasts/podcasts.tsv and the cronjob should be adjusted to include a `TSV` variable like this: `@daily cd /home/pdurbin/feedcritic && make all DIR=/var/www/podcasts.greptilian.com TSV=/var/www/wiki/podcasts/podcasts.tsv`

## Features under consideration

- Sorting the list of podcast by "most recent episode".
- A place to write reviews of podcasts.
- A place to write reviews of individual episodes.

## Feedback

You are welcome to make suggestions or otherwise give feedback by opening an issue. Thanks for your interest in Feedcritic!
