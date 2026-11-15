.PHONY: all fetch tag
all: fetch tag
fetch:
	python3 fetch.py
tag:
	python3 tag.py
