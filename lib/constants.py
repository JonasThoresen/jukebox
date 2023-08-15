import os
import sys

# Directories
DIR_BASE = sys.path[0]

# Files
FILE_CONFIG = os.path.join(DIR_BASE, "config.ini")

# Base config file
DEFAULT_CONFIG = ["[SETTINGS]",
                  "volume = 50"]
DEFAULT_VOLUME = 50


# Youtube
YOUTUBE_START_URL = "https://www.youtube.com/watch?v="
YOUTUBE_ARTIST_URL = "https://www.youtube.com/channel/"
YOUTUBE_VIDEO_ID = r"(?<=\?v=)[^&]+"

# Errors
IS_PLAYING_ERROR = ("The player is currently playing music, you cannot start the player again. "
                    + "This is because the MusicPlayer class runs music in a thread and the "
                    + "tool is not expected to run more than one song from the same player. "
                    + "Multiple songs can be run at the same time from different players, but "
                    + "not from the same one. If you got this error, it is likely that you "
                    + "should instead have called 'MusicPlayer.abort()' before calling run, "
                    + "as we need to shut down the player first.")

IS_NOT_PLAYING_ERROR = ("The player is not currently playing any music. The action performed "
                        + "is not allowed until the player is playing music. "
                        + "Illegal action -> ")

QUEUE_EMPTY_ERROR = ("There are no queued songs. The action performed is not allowed until "
                     + "there are songs in the queue. Songs can be added using the "
                     + "'add_song()' command. "
                     + "Illegal action -> ")

OLD_QUEUE_EMPTY_ERROR = ("There are no finished queued songs. The action performed is not "
                         + "allowed until there are songs in the old queue. "
                         + "Illegal action -> ")

# States
VLC_STATES = {0: 'NothingSpecial',
              1: 'Opening',
              2: 'Buffering',
              3: 'Playing',
              4: 'Paused',
              5: 'Stopped',
              6: 'Ended',
              7: 'Error'}

PLAYER_OK_STATES = ["playing",
                    "nothingspecial",
                    "opening",
                    "paused"]
