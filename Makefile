.PHONY: all fetch tag examples
all: fetch tag
fetch:
	python3 fetch.py
tag:
	python3 tag.py

# Mirror the gitignored feeds.txt and overrides.json into the tracked example files.
examples:
	{ printf '# One podcast feed URL per line. Copy to feeds.txt and edit.\n# Lines starting with # are ignored.\n'; grep -v '^#' feeds.txt; } > feeds.txt.example
	cp overrides.json overrides.json.example
