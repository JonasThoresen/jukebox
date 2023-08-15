# Music player errors
class PlayerException(Exception):
    """ Custom exception for the Music Player class, this specifically references the music player."""


class IsSpawned(PlayerException):
    """Custom exception raised when attempting to spawn the player when it is already spawned. """
    pass

class IsPlayingError(PlayerException):
    """Custom exception raised when attempting to play music while music is already playing. """
    pass


class IsNotPlayingError(PlayerException):
    """Custom exception raised when attempting to perform an action where the player must be running. """
    pass


# Music queue errors
class QueueException(Exception):
    """ Custom exception for the Music Player class, this specifically references the queueing part. """


class QueueEmptyError(QueueException):
    """Custom exception raised when attempting to perform an action with an empty queue """
    pass
