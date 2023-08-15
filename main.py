from flask import Flask, request, abort, jsonify, make_response, render_template
from flask_restful import Resource, Api
from lib.player import MusicPlayer
from lib.exceptions import IsSpawned, IsNotPlayingError, QueueEmptyError
import lib.constants as constants
import os
import configparser
from googleapiclient.discovery import build as yt_build
from dotenv import load_dotenv


# API
app = Flask("VideoAPI")
api = Api(app)

# Youtube
load_dotenv()
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
youtube = yt_build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


# Pages
@app.route('/')
def home():
    return render_template('index.html')


# API
@app.route('/add_song', methods=['POST'])
def add_song():
    request_keys = request.form.keys()
    if 'video' in request_keys:
        # Connect to youtube api
        yt_request = youtube.videos().list(
            part="snippet",
            id=request.form['video']
        )
        yt_response = yt_request.execute()
        print(yt_response)
        if yt_response:
            if "items" in yt_response.keys():
                items = yt_response["items"]
                content = [item["snippet"] for item in items if "snippet" in item.keys()]
                titles = [snippet["title"] for snippet in content if "title" in snippet.keys()]
                artists = [snippet["channelTitle"] for snippet in content if "channelTitle" in snippet.keys()]
                artist_link = [snippet["channelId"] for snippet in content if "channelId" in snippet.keys()]
                thumbnails = [snippet["thumbnails"]["default"]["url"] for snippet in content if "thumbnails" in snippet.keys()]
                print(f"Added song '{titles[0]}' by '{artists[0]}' with thumbnails '{thumbnails[0]}'")
                music_player.add_song({"title": titles[0], "artist": artists[0], "artist_id": artist_link[0], "thumbnail": thumbnails[0], "video_id": request.form['video']})
            else:
                abort(400, f"Bad response from youtube server -> {yt_response}")
        else:
            abort(400, f"Bad response from youtube server -> {yt_response}")

        # music_player.add_song(request.form['video'])
        r = "Added song"

    elif 'list' in request_keys:
        print("Attempting to add playlist instead of videos")
        yt_request = youtube.playlistItems().list(
            part="contentDetails",
            maxResults=100,
            playlistId=request.form['list']
        )
        yt_response = yt_request.execute()
        if yt_response:
            if "items" in yt_response.keys():
                items = yt_response["items"]
                content = [item["contentDetails"] for item in items if "contentDetails" in item.keys()]
                video_ids = [video["videoId"] for video in content if "videoId" in video.keys()]

                for video_id in video_ids:
                    # Get youtube video info
                    yt_request = youtube.videos().list(
                        part="snippet",
                        id=video_id
                    )
                    yt_response = yt_request.execute()
                    if yt_response:
                        if "items" in yt_response.keys():
                            items = yt_response["items"]
                            content = [item["snippet"] for item in items if "snippet" in item.keys()]
                            titles = [snippet["title"] for snippet in content if "title" in snippet.keys()]
                            artists = [snippet["channelTitle"] for snippet in content if "channelTitle" in snippet.keys()]
                            artist_link = [snippet["channelId"] for snippet in content if "channelId" in snippet.keys()]
                            thumbnails = [snippet["thumbnails"]["default"]["url"] for snippet in content if "thumbnails" in snippet.keys()]
                            print(f"Added songs '{titles}' by '{artists}' with thumbnails '{thumbnails}'")
                            music_player.add_song({"title": titles[0], "artist": artists[0], "artist_id": artist_link[0], "thumbnail": thumbnails[0], "video_id": video_id})
                        else:
                            abort(400, f"Bad response from youtube server -> {yt_response}")

                r = "Added songs"

            else:
                abort(400, f"Bad response from youtube server -> {yt_response}")
    else:
        abort(400, "No value in request")

    return r


@app.route('/play', methods=['GET'])
def play():
    try:
        music_player.start()
        return "Spawned player"
    except IsSpawned:
        print("Player is already spawned")
        try:
            music_player.play()
            return "Toggled playstate"
        except IsNotPlayingError:
            abort(500, "Player is not playing, even though it should be")


@app.route('/next', methods=['GET'])
def next():
    try:
        music_player.next_song()
        return "Skipped song"
    except QueueEmptyError:
        abort(500, "Queue is empty")


@app.route('/previous', methods=['GET'])
def previous():
    try:
        music_player.previous_song()
        return "Wound back 1 song"
    except QueueEmptyError:
        abort(500, "Queue is empty")


@app.route('/stop', methods=['GET'])
def stop():
    return music_player.abort()


@app.route('/changesong', methods=['POST'])
def change_song():
    try:
        if "queue_id" in request.form.keys():
            try:
                input_int = int(request.form["queue_id"])
                return music_player.change_song(input_int)
            except ValueError:
                abort(400, "queue_id is not an integer")
        else:
            abort(400, "No queue_id in request")
    except QueueEmptyError:
        abort(500, "Queue is empty")
    except Exception as e:
        abort(500, "Got an error -> " + str(e))


@app.route('/removesong', methods=['POST'])
def remove_song():
    try:
        if "queue_id" in request.form.keys():
            try:
                input_int = int(request.form["queue_id"])
                return music_player.remove_song(input_int)
            except ValueError:
                abort(400, "queue_id is not an integer")
    except QueueEmptyError:
        abort(500, "Queue is empty")
    except Exception as e:
        abort(500, "Got an error -> " + str(e))


@app.route('/queue', methods=['GET'])
def get_queue():
    if "upcoming" in request.form.keys():
        print("Returning", music_player.get_queue())
        return jsonify(music_player.get_queue())
    else:
        print("Returning", music_player.get_full_queue())
        return jsonify(music_player.get_full_queue())


@app.route('/clearqueue', methods=['GET'])
def clear_queue():
    return music_player.clear_queue()


@app.route('/playtime', methods=['GET'])
def playtime():
    return jsonify(music_player.get_playtime())


@app.route('/volume', methods=['GET', 'POST'])
def volume():
    if request.method == 'GET':
        return str(music_player.get_volume())
    elif request.method == 'POST':
        print(request.form.keys())
        try:
            if "volume" in request.form.keys():
                vol = int(request.form['volume'])
                music_player.set_volume(vol)
                return "Set volume"
            elif "mute" in request.form.keys():
                music_player.set_mute()
                return str(music_player.get_volume())
            else:
                print(request.form.keys())
                return "kek"
        except Exception as e:
            abort(400, f"Could not set volume since it is not an integer -> {e}")


if __name__ == '__main__':
    # Load config first
    # Create config data if it does not exist
    if not os.path.exists(constants.FILE_CONFIG):
        with open(constants.FILE_CONFIG, "w") as config_file:
            config_file.writelines("\n".join(constants.DEFAULT_CONFIG))

    # Load config data
    config = configparser.ConfigParser()
    config.read(constants.FILE_CONFIG)
    vol = constants.DEFAULT_VOLUME
    try:
        tmp_vol = int(config["SETTINGS"]["volume"])
        print(f"Got volume '{tmp_vol}' from config")
        vol = tmp_vol
    except Exception as e:
        print(f"Could not set volume due to -> {e}")

    # Start music player
    music_player = MusicPlayer(start_volume=vol)

    # Start application
    app.run(port=8080, debug=True)
