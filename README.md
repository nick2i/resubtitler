# resubtitler (WIP)

`resubtitler` is a (WIP) utility tool to rename subtitle files in bulk. It's intended for scenarios where subtitle files follow a different naming format compared to their corresponding media files.

When the subtitle and media files follow the same naming scheme, they can be automatically detected by applications like VLC media player.

# How to use

(TODO - also add a picture or two)

Uses Python regexes. Specify the episode and subtitle filetypes (usually this is the letters after '.' in the filename, you do not need to write '.' in the input). For episodes where all numerical digits in filenames correspond to episode numbers, the default regexes should be adequate. The entire input is used as the matching regex for the episode number:

```python
for ep in episode_files:
    # user input -> episode_regex, ep.name is the episode filename
    match = re.search(episode_regex, ep.name)
    if match:
        episode_number_raw = match.group()
```

and likewise for the subtitle number:

```python
for sub in subtitle_files:
    # user input -> subtitle_regex, sub.name is the subtitle filename
    match = re.search(subtitle_regex, sub.name)
```

The match variables in each loop are the basis of comparison between the two file types. 0-padding is ignored in the comparison.

These two links contain plenty of information on Python regex: https://docs.python.org/3/library/re.html, https://docs.python.org/3/howto/regex.html

You can test regexes here first. Select "Python" from the FLAVOR menu, and put newline-separated sample filenames in the TEST STRING area.

https://regex101.com/ 

# Roadmap

I'd like to support re-timing subtitles eventually as well (e.g. adjust every subtitle so it appears .5 seconds later). Probably just .srt files to start, maybe expanding to a couple other common formats.

