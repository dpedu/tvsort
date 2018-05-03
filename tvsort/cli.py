#!/usr/bin/env python3
import argparse
import os
import pickle
from tvsort import shows
from tvsort.parser import EpisodeParseException, parse_episode, sub_bucket_name
from appdirs import user_config_dir
from fuzzywuzzy import fuzz
from tabulate import tabulate
from pprint import pprint
from collections import namedtuple


MatchedEpisode = namedtuple("MatchedEpisode", "root ep dest subdest score")
"""
Struct describing the intent to sort and episode file into a location
    root : abs path to the folder containing ep.file
    ep : associated EpInfo object
    dest : associated Show object
    score : scoring value Show::match returned
"""


def main():
    " parse command line args "
    parser = argparse.ArgumentParser(description="sort tv shows")
    parser.add_argument("-s", "--src", nargs="+", help="", required=True)
    parser.add_argument("-d", "--dest", nargs="+", help="", required=True)
    parser.add_argument("--soft", action="store_true", help="Soft link instead of hard link")
    parser.add_argument("-r", "--rescan", action="store_true", help="Rescan library instead of using cache")
    parser.add_argument("--match-thresh", type=int, default=65)
    parser.add_argument("--mappings", nargs="+", default=[])  # many foo=bar transformations to help witch mapping
    args = parser.parse_args()

    if args.match_thresh <= 0 or args.match_thresh > 100:
        parser.error("--match-thresh must be 1-100")

    # mappings allow simple string transforms as workarounds for poorly named episodes
    mappings = {}
    for item in args.mappings:
        key, value = item.split("=")
        mappings[key] = value

    # load the library, an index of shows already sorted. the dirnames will be compared to incoming files
    cachedir = user_config_dir("tvsort")
    os.makedirs(cachedir, exist_ok=True)
    cache_file = os.path.join(cachedir, "library.cache")
    library = None
    if os.path.exists(cache_file) and not args.rescan:
        with open(cache_file, "rb") as f:
            try:
                library = pickle.load(f)
            except:
                print("Failed to load library cache")
    if not library:
        library = shows.create_index(args.dest)
        with open(cache_file, "wb") as f:
            pickle.dump(library, f)

    failures = []
    results = []

    # iterate through all children of the src dirs
    for srcdir in args.src:
        for fname in os.listdir(srcdir):
            # TODO season dirs are ignored for now
            if not os.path.isfile(os.path.join(srcdir, fname)):
                continue

            # Apply manually specified transformations
            item = fname
            for old, new in mappings.items():
                item = item.replace(old, new)

            # Parse information from the episode file name
            try:
                epinfo, item = parse_episode(item)
            except EpisodeParseException:
                failures.append(fname)

            # Find a show from the library best matching this episode
            match_score = 0
            best_match_show = None
            for show in library:
                value = fuzz.token_set_ratio(show.name.lower(), item.lower())  #TODO add algorithm swap arg for snakeoil
                if value > match_score:
                    match_score = value
                    best_match_show = show
            if match_score >= args.match_thresh:
                results.append(
                    MatchedEpisode(srcdir, epinfo, best_match_show,
                                   sub_bucket_name(best_match_show, epinfo.major, epinfo.minor, epinfo.extra),
                                   match_score))
            else:
                failures.append(fname)

    before = len(results)
    results = list(
        filter(
            lambda r: not os.path.exists(os.path.join(r.dest.root, r.dest.dir, r.subdest, r.ep.file)),
            results))
    already_there = before - len(results)

    go = False
    while not go:
        tab_rows = []
        i = 0
        results.sort(key=lambda x: x.dest.dir)
        for item in results:
            row = [i,
                   item.ep.file,
                   item.ep.major,
                   item.ep.minor,
                   os.path.join(item.dest.dir, item.subdest) + "/",
                   item.score,
                   "soft" if args.soft else "hard"]
            tab_rows.append(row)
            i += 1

        print(tabulate(tab_rows, headers=["number", "file", "season", "episode", "dest", "score", "link"]))

        if already_there:
            print("\n{} already in library and ignored".format(already_there))

        if failures:
            print("\n")
            print("Could not match:")
            pprint(failures)

        if not results:
            print("no candidates for linking found!")
            return

        resp = input("create links? [y/N/<lines to skip and print again>]: ").lower().strip()

        if not resp or resp == "n":
            return

        if resp == "y":
            break

        exclude = []
        for number in resp.split():
            exclude.append(int(number))
        exclude.sort(reverse=True)
        for number in exclude:
            results.pop(number)

    link = os.symlink if args.soft else os.link

    for item in results:
        src = os.path.join(item.root, item.ep.file)
        destdir = os.path.join(item.dest.root, item.dest.dir, item.subdest)
        dest = os.path.join(destdir, item.ep.file)
        # print("mkdir ", destdir)
        os.makedirs(destdir, exist_ok=True)
        # print(src, "   ->   ", dest)
        link(src, dest)


if __name__ == '__main__':
    main()
