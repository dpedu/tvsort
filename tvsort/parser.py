import re
import string
from tvsort.common import Season, Show, EpInfo


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


class EpisodeParseException(Exception):
    pass


def parse_episode(fname):
    """
    Given a file name, parse out any information we can from the name
    :return:
    """

    # Remove file extensions
    item = fname.rstrip(".mkv").lower()#TODO make this better

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
            raise EpisodeParseException("Could not parse episode {}".format(repr(fname)))

    # Remove common torrenty names
    for crap in COMMON_CRAP:
        item = crap.sub("", item)

    # Remaining chars should be a show name and possibly and episode title. And random bs
    allowed_chars = string.ascii_lowercase + string.digits
    item = ''.join([i if i in allowed_chars else " " for i in item]).strip()

    return epinfo, item


def sub_bucket_name(show, major, minor, extra):
    if show.mode == Season.by_date:
        return str(major)
    elif show.mode == Season.by_season:
        return "Season {}".format(major)
    else:
        return ''
