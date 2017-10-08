#!/usr/bin/env python3
import argparse
import os
import re
import string
from pprint import pprint
from fuzzywuzzy import fuzz
from collections import namedtuple
from tabulate import tabulate


class Season:
    by_season = 0
    by_date = 1
    special = 3


EpInfo = namedtuple("EpInfo", "file mode major minor extra")
Show = namedtuple("Show", "dir name match")
MatchedEpisode = namedtuple("MatchedEpisode", "ep dest score")


def create_show(dirname):
    dir_lower = dirname.lower()
    return Show(dirname, dir_lower, lambda other: fuzz.token_set_ratio(dir_lower, other.lower()))


def main():
    " parse command line args "
    parser = argparse.ArgumentParser(description="sort tv shows")
    parser.add_argument("-s", "--src", nargs="+", help="", required=True)
    parser.add_argument("-d", "--dest", nargs="+", help="", required=True)
    parser.add_argument("--soft", action="store_true", help="Soft link instead of hard link")#TODO
    parser.add_argument("--match-thresh", type=int, default=65)  #0-100
    parser.add_argument("--mappings", nargs="+", default=[])  # many foo=bar transformations to help witch mapping
    args = parser.parse_args()

    mappings = {}
    for item in args.mappings:
        key, value = item.split("=")
        mappings[key] = value

    # Create index of shows
    shows = []
    for destdir in args.dest:
        for i in os.listdir(destdir):
            shows.append(create_show(i))

    NORMAL_SEASON_EP_RE = re.compile(r'(([sS]([0-9]{2}))x?([eE]([0-9]{2}))?)')  # match something like s01e02
    NORMAL_SEASON_EP_RE2 = re.compile(r'(([0-9]+)[xX]([0-9]{2}))')  # match something like 21x04
    DATE_SEASON_EP_RE = re.compile(r'((201[0-9]).([0-9]{1,2})?.([0-9]{1,2})?)')  # match something like 2017-08-3
    COMMON_CRAP = [re.compile(i, flags=re.I) for i in
                   [r'(720|1080)p',
                    r'hdtv',
                    r'(h.?)?x?264(.[a-z0-9]+)?',
                    r'(ddp\d\.\d)?',
                    r'web(\-?(dl|rip))?',
                    r'[\.\-\s](amzn|amazon)[\.\-\s]',
                    r'dd.5.\d',
                    r'AAC2.\d']]

    failures = []
    results = []

    for srcdir in args.src:
        for item in os.listdir(srcdir):
            if not os.path.isfile(os.path.join(srcdir, item)):
                # TODO go into subdirs too (we assume dir means season pack)
                continue
            fname = item

            # Remove file extension
            item = item.rstrip(".mkv").lower()#TODO make this better

            # Apply manual transformations
            for old, new in mappings.items():
                item = item.replace(old, new)

            # Extract season information
            # And remove seasons info chars from the working name
            epinfo = None
            match = NORMAL_SEASON_EP_RE.search(item) or NORMAL_SEASON_EP_RE2.search(item)
            if match:
                fields = match.groups()
                if len(fields) == 5:
                    whole, _, season, _, episode = fields
                else:
                    whole, season, episode = fields

                if season and not episode:
                    epinfo = EpInfo(fname, Season.special, int(season), None, None)
                else:
                    assert season and episode
                    epinfo = EpInfo(fname, Season.by_season, int(season), int(episode), None)

                # delete everything after the episode number
                pos = item.find(whole)
                if pos >= 10:
                    item = item[0:pos]
                else:
                    # unless it makes it too short
                    item = item.replace(whole, "")
            else:
                match = DATE_SEASON_EP_RE.search(item)
                if match:
                    whole, year, month, day = match.groups()
                    assert year is not None
                    if month:
                        month = int(month)
                    if day:
                        day = int(day)
                    epinfo = EpInfo(fname, Season.by_date, int(year), month, day)
                    # delete everything after the episode number
                    pos = item.find(whole)
                    if pos >= 10:
                        item = item[0:pos]
                    else:
                        # unless it makes it too short
                        item = item.replace(whole, "")
                else:
                    # raise Exception("Could not parse episode: {}".format(repr(item)))
                    failures.append(fname)
                    continue

            # Remove common torrenty names
            for crap in COMMON_CRAP:
                item = crap.sub("", item)

            # print(epinfo, "->", item)

            # Remaining chars should be a show name and possibly and episode title. And random bs
            allowed_chars = string.ascii_lowercase + string.digits
            item = ''.join([i if i in allowed_chars else " " for i in item]).strip()

            match_score = 0
            best_match_show = None
            for show in shows:
                value = show.match(item)
                if value > match_score:
                    match_score = value
                    best_match_show = show

            if match_score > args.match_thresh:
                results.append(MatchedEpisode(epinfo, best_match_show, match_score))
            else:
                failures.append(fname)

    tab_rows = []
    for item in sorted(results, key=lambda x: x.dest.dir):
        row = [item.ep.file, item.ep.major, item.ep.minor, item.dest.dir, item.score]
        tab_rows.append(row)

    print(tabulate(tab_rows, headers=["file", "season", "episode", "dest", "score"]))

    if failures:
        print("\n\n")
        print("Could not match:")
        pprint(failures)


if __name__ == '__main__':
    main()
