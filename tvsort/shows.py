import os
from tvsort.common import Show, Season
import string


def create_show(root_path, dirname):
    dir_lower = dirname.lower()

    # Inspect contents of show directory and guess naming scheme
    yearish = 0
    seasonish = 0
    wtfish = 0
    buckets_season = []
    buckets_year = []
    for item in os.listdir(os.path.join(root_path, dirname)):
        if item.lower().startswith("season "):
            seasonish += 1
            buckets_season.append(int(''.join([i if i in string.digits else " " for i in item]).strip()))  # todo flexible season dir detection
            continue
        try:
            year = int(item)
            buckets_year.append(year)
            if year > 1900 and year < 2050:
                yearish += 1
                continue
        except ValueError:
            pass
        wtfish += 1

    mode = None
    episodes = None

    if yearish > seasonish and yearish > wtfish:
        mode = Season.by_date
        episodes = buckets_year
    elif seasonish > yearish and seasonish > wtfish:
        mode = Season.by_season
        episodes = buckets_season
    else:
        mode = Season.none
        episodes = []

    return Show(root_path, dirname, dir_lower, mode, episodes)


def create_index(fs_paths):
    shows = []
    for d in fs_paths:
        for i in os.listdir(d):
            if os.path.isdir(os.path.join(d, i)):
                shows.append(create_show(d, i))

    return shows
