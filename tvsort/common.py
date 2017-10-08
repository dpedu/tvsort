from collections import namedtuple


class Season:
    """
    All episodes are categorized into seasons (or season-like entities). A season may number it's episodes by date or by
    season and episode number. Thirdly, an episode may be associated with a season but not obey the regular naming
    scheme - such as a special episode. This enum is for describing what chronological scheme an episode appears to use.
    """
    none = 0
    by_season = 1
    by_date = 2
    special = 3


Show = namedtuple("Show", "root dir name mode seasons")
"""
Struct describing an in-library tv show
    root : abs path to the folder containing dir
    dir : absolute(?) file path to the show
    name : name of the show
    mode : Season strategy (cannot be 'special')
    seasons : list of season ints
"""


EpInfo = namedtuple("EpInfo", "file mode major minor extra")
"""
Struct for describing an episode file.
    file : file name of the episode file
    mode : chronological scheme of file naming (see Season)
    major : least granular chronological unit. Typically season or year
    minor : medium granular unit. Always episode number
    extra : most granular unit. Always day (only used for date-based episodes)
"""
