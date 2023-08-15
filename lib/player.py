import pafy
import vlc
from . import constants
from .exceptions import IsPlayingError, IsSpawned, IsNotPlayingError, QueueEmptyError
import re
import threading


class MusicPlayer:
    def __init__(self, start_volume: int = constants.DEFAULT_VOLUME):
        # Create instance
        self._instance = vlc.Instance()
        self._player = self._instance.media_player_new()
        
        # Set player
        self._thread = threading.Thread(target=self._play_songs)

        # Set up queue
        self._queue = []
        self._old_queue = []
        self._skip = False

        # Set up defaults
        self.set_volume(start_volume)
        self._volume_before_mute = start_volume
        self._cancel_operation = False

    # Internal actions
    def _play_songs(self):
        """ The main loop of the music player that keeps it playing """
        self._cancel_operation = False

        # Loop all songs in the queue
        while self.get_current_song():
            if self._cancel_operation:
                # If we have aborted, we stop the player then exit the thread
                self._player.stop()
                return

            self._skip = False

            # Load data from youtube
            print("Loading new video")
            next_song = self.get_current_song()
            print()
            try:
                video = pafy.new(constants.YOUTUBE_START_URL + next_song["video_id"])
            except OSError as os_e:
                print("Song could not be played since PAFY is trash ->", os_e)
                print("Attempting to play the song again")
                continue
            except Exception as exc_e:
                print(f"Could not play '{constants.YOUTUBE_START_URL}{next_song['video_id']}' as it cannot be loaded or streamed. "
                      f"Full error is -> {exc_e}")
                print("Skipping this song")
                self.next_song()
                continue

            # Load stream data
            best = video.getbestaudio()
            play_url = best.url

            # Create media instance and play it
            media = self._instance.media_new(play_url)
            media.get_mrl()
            self._player.set_media(media)
            self._player.play()

            while self.get_state() in constants.PLAYER_OK_STATES:
                if self._cancel_operation:
                    # If we have aborted, we stop the player then exit the thread
                    self._player.stop()
                    return

                if self._skip:
                    break

            # Natural song end
            if not self._skip:
                self.next_song()

        return

    # External player actions
    def start(self):
        """
        Starts the music player loop in its own thread.
        If the player is playing, it raises PlayerIsPlayingError, as
        it is not allowed for the player to start more than one thread.
        """
        if self._thread.is_alive():
            raise IsSpawned(constants.IS_PLAYING_ERROR)
        else:
            if len(self._queue) > 0:
                self._thread = threading.Thread(target=self._play_songs)
                self._thread.start()
            else:
                if len(self._old_queue) > 0:
                    print("Restarting queue...")
                    self._queue = self._old_queue
                    self._old_queue = []
                    self._thread = threading.Thread(target=self._play_songs)
                    self._thread.start()
                else:
                    raise QueueEmptyError(constants.QUEUE_EMPTY_ERROR + "start().")

    def play(self) -> None:
        """
        Toggles the player between paused and playing. If the player
        is not running, it will return an exception.
        """
        if self.get_state() == "playing":
            print("Pausing...")
            self._player.pause()
        elif self.get_state() == "paused":
            print("Playing...")
            self._player.pause()
        else:
            raise IsNotPlayingError(constants.IS_NOT_PLAYING_ERROR + "pause().")

    def abort(self) -> None:
        """ Abort any running operation and close down its running thread. """
        if self.get_state() in constants.PLAYER_OK_STATES:
            self._cancel_operation = True
            return "Aborted operation."
        else:
            raise IsNotPlayingError(constants.IS_NOT_PLAYING_ERROR + "abort().")

    # External queue actions
    def add_song(self, song_data: dict()) -> None:
        """
        Adds a song to the music player queue.

        Parameters:
        url (str): Either the URL for the full youtube video or just the video id.
        """
        self._queue.append(song_data)

    def change_song(self, queue_id: int) -> None:
        """
        Changes the song to a previous or coming song in the queue.
        """
        if not self._queue:
            raise QueueEmptyError(constants.QUEUE_EMPTY_ERROR + "change_song().")
        if not isinstance(queue_id, int):
            raise TypeError(f"Queue ID '{queue_id}' must be an integer")
        if queue_id < 0:
            raise ValueError(f"Queue ID '{queue_id}' must be a positive integer")

        full_queue = self._old_queue + self._queue
        if queue_id > len(full_queue):
            raise IndexError(f"Queue ID '{queue_id}' is larger than the queue size {len(full_queue)}.")

        current_id = len(self._old_queue)
        if queue_id == current_id:
            raise ValueError(f"Queue ID '{queue_id}' is the current song.")
        else:
            self._old_queue = full_queue[:queue_id]
            self._queue = full_queue[queue_id:]
            self._skip = True

        return "Changed to song no. " + str(queue_id) + " in the queue."

    def remove_song(self, queue_id: int) -> None:
        """
        Removes a song from the music player queue.

        Parameters:
        queue_id (str): The actual queue id of the song (starts as 1, aka. one-indexed counting).
        """
        if not self._queue:
            raise QueueEmptyError(constants.QUEUE_EMPTY_ERROR + "change_song().")
        if not isinstance(queue_id, int):
            raise TypeError(f"Queue ID '{queue_id}' must be an integer")
        if queue_id < 0:
            raise ValueError(f"Queue ID '{queue_id}' must be a positive integer")

        full_queue = self._old_queue + self._queue
        if queue_id > len(full_queue):
            raise IndexError(f"Queue ID '{queue_id}' is larger than the queue size {len(full_queue)}.")

        current_id = len(self._old_queue)
        if queue_id == current_id:
            self._queue.pop(0)
            self._skip = True
        elif queue_id < current_id:
            self._old_queue.pop(queue_id)
        elif queue_id > current_id:
            actual_id = queue_id - current_id
            self._queue.pop(actual_id)
        return f"Removed {queue_id} from the queue."

    def next_song(self):
        """
        Plays the next song in the queue. It functions both for skipping and to play the next
        song. A skip is defined as performing 'next_song()' while the player is playing or is
        paused. Otherwise, the player handles it as a song change.
        """
        if not self._queue:
            raise QueueEmptyError(constants.QUEUE_EMPTY_ERROR + "next_song().")
        else:
            old_song = self._queue.pop(0)
            print(f"Done playing '{old_song}'")
            if self.get_state() in ["opening", "buffering", "playing", "paused"]:
                state = "skipped"
                self._skip = True
            else:
                state = "ok"

            # Remove song and add to the old queue
            self._old_queue.append(old_song)

    def previous_song(self):
        """
        Plays the previous song in the queue.
        """

        # check if we are playing music
        # Make sure that the song has been playing for at least 10 seconds
        if (self.get_state() in ["opening", "buffering", "playing", "paused"] and
                self._player.get_time() > 10000):
            # If we are, we want to restart the song
            self._player.set_time(0)
        else:
            # If not we can try to skip to previous
            if not self._old_queue:
                if self._queue:
                    self._player.set_time(0)
                else:
                    # No current song and no previous songs
                    raise QueueEmptyError(constants.OLD_QUEUE_EMPTY_ERROR + "previous_song().")
            else:
                # We have a previous song, so we can play that
                old_song = self._old_queue.pop()
                self._queue.insert(0, old_song)
                self._skip = True

    def get_playtime(self) -> dict:
        """
        Gets the current playtime of the song in milliseconds.
        """
        playtime = {"max": self._player.get_length(),
                    "current": self._player.get_time()}
        return playtime

    # API: Gettable data
    def get_state(self) -> str:
        """ Gets current run state of the system.
        Possible states are:
        - nothingspecial
        - opening
        - buffering
        - playing
        - paused
        - stopped
        - ended
        - error
        """
        state_full = str(self._player.get_state()).casefold()
        state_only = state_full.replace("state.", "")
        return state_only

    def get_volume(self) -> int:
        """ Gets current volume of the system as an integer. """
        return self._current_volume

    def get_queue(self) -> list:
        return self._queue

    def get_full_queue(self) -> dict:
        return {"songs": self._old_queue + self._queue, "current_id": len(self._old_queue)}

    def get_old_queue(self) -> dict:
        return self._old_queue

    def get_current_song(self) -> str:
        """ Returns the current song dictionary. """
        song = self._queue[0] if len(self._queue) > 0 else {}
        return song

    # API: Settable data
    def set_volume(self, vol: int) -> None:
        """ Sets the current volume of the player to an integer between 0 and 100,
        representing 0-100% volume.
        """
        if not isinstance(vol, int):
            raise TypeError(f"Volume must be an integer, not {type(vol)}")
        if not 0 <= vol <= 100:
            raise ValueError(f"Volume must be an integer between 0 and 100")
        self._current_volume = vol
        self._player.audio_set_volume(vol)

    def set_mute(self) -> None:
        if self._current_volume > 0:
            self._volume_before_mute = self._current_volume
            self.set_volume(0)
        else:
            self.set_volume(self._volume_before_mute)

    def clear_queue(self) -> None:
        """ Remove all data from the queue"""
        if len(self._queue) < 1 and len(self._old_queue) < 1:
            raise QueueEmptyError(constants.QUEUE_EMPTY_ERROR + "reset_queue().")
        else:
            self._queue = []
            self._old_queue = []
            return "Queue cleared."

    def set_playtime(self, time: int) -> None:
        """ Sets the current playtime of the song in milliseconds. """
        if not isinstance(time, int):
            raise TypeError(f"Time must be an integer, not {type(time)}")
        if not 0 <= time <= self._player.get_length():
            raise ValueError(f"Time must be an integer between 0 and {self._player.get_length()}")
        self._player.set_time(time)
