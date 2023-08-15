// global variable for hidden
var open_prompt = false;
var base_url = "http://localhost:8080/"
var default_yt_image = "https://i.ytimg.com/vi/7q1QC8SbmxI/hqdefault.jpg";
var youtube_api_key = "AIzaSyAg0bVAEKFx5Nm29Agc1VKnaTVQaGm0QPg";


// Event listener for a range slider
var volume_slider = document.getElementById("VolumeSlider");
var volume_text = document.getElementById("VolumeText");
var mouse_down_slider_timer;
volume_slider.addEventListener("mousedown", function(){
     mouse_down_slider_timer=setInterval(function(){
        volume_text.innerHTML = "Volume: " + volume_slider.value;
     }, 100); // the above code is executed every 100 ms
     volume_text.innerHTML = "Volume: " + volume_slider.value;
});

volume_slider.addEventListener("mouseup", function(){
    if (mouse_down_slider_timer) clearInterval(mouse_down_slider_timer)
});

volume_slider.addEventListener("wheel", function(){
    volume_text.innerHTML = "Volume: " + volume_slider.value;
});


// Code that sets a timer on the ADD input field
// so that the user does not have to press enter
let typingTimer;                //timer identifier
let typingWaitTime = 500;  //time in ms (5 seconds)
let addSongInput = document.getElementById('AddSongInput');

//on keyup, start the countdown
addSongInput.addEventListener('keyup', event => {
    clearTimeout(typingTimer);

    typingTimer = setTimeout(() => {
      add_song_done_typing(event.target.value);
    }, typingWaitTime);
  });

var youtube_id = "";
var youtube_list_id = "";
var youtube_index = "";
function add_song_done_typing (input) {
    var warning_field = document.getElementById("AddModalWarningText");
    var add_song_button = document.getElementById("AddSongButton");
    console.log("Done typing: ", input);
    youtube_id = "";
    youtube_list_id = "";
    youtube_index = "";

    if (input == "") {
        if (warning_field.style.display == "none" || !warning_field.style.display) {
            warning_field.style.display = "block";}
        warning_field.innerHTML = "Please fill in the field";
        add_song_button.disabled = true;
        return;
    }

    var youtube_regex = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;
    if (!input.match(youtube_regex)) {
        if (warning_field.style.display == "none" || !warning_field.style.display) {
            warning_field.style.display = "block";}
        warning_field.innerHTML = "Input is not a valid youtube link";
        add_song_button.disabled = true;
        return;
    }

    warning_field.style.display = "none";

    if (input.indexOf("v=") != -1) {
        youtube_id = input.split("v=")[1];
        if (youtube_id.indexOf("&") != -1) {
            youtube_id = youtube_id.split("&")[0];
        }
        console.log("youtube_id=", youtube_id);
    }
    else {
        console.log("No video id found");
    }


    // Check if the input contains the word list=
    if (input.indexOf("list=") != -1) {
        youtube_list_id = input.split("list=")[1];
        if (youtube_list_id.indexOf("&") != -1) {
            youtube_list_id = youtube_list_id.split("&")[0];
        }
        console.log("youtube_list_id=", youtube_list_id);
    } else {
        console.log("No list id found");
    }

    if (input.indexOf("index=") != -1) {
        youtube_index = input.split("index=")[1];
        if (youtube_index.indexOf("&") != -1) {
            youtube_index = youtube_index.split("&")[0];
        }
        console.log("youtube_index=", youtube_index);
    }
    else {
        console.log("No playlist index found");
    }

    var video_radio = document.getElementById("AddSongVideo");
    var video_list = document.getElementById("AddSongList");
    if (youtube_id != "" && youtube_list_id == "") {
        video_radio.disabled = true;
        video_list.disabled = true;
        video_radio.checked = true;
        add_song_button.innerHTML = "Add Video";
        add_song_button.disabled = false;
    }    
    else if (youtube_id == "" && youtube_list_id != "") {
        video_radio.disabled = true;
        video_list.disabled = true;
        video_list.checked = true;
        add_song_button.innerHTML = "Add List";
        add_song_button.disabled = false;
    }
    else if (youtube_id != "" && youtube_list_id != "") {
        video_radio.disabled = false;
        video_list.disabled = false;
        video_list.checked = true;
        add_song_button.disabled = false;
    }
    else {
        console.log("No valid input found");
        video_radio.disabled = true;
        video_list.disabled = true;
        video_radio.checked = true;
        add_song_button.disabled = true;
    }
}

function add_song_clear_warning() {
    var warning_field = document.getElementById("AddModalWarningText");
    warning_field.style.display = "none";
    warning_field.innerHTML = "No warning";
}

function add_song() {
    var isVideo = document.getElementById("AddSongVideo").checked;
    var isList = document.getElementById("AddSongList").checked;

    var request = new XMLHttpRequest();
    request.open("POST", base_url + "add_song", true);
    var output = "";
    if (isVideo) {
        console.log("Adding video");
        output = "video=" + youtube_id;
    }
    else if (isList) {
        console.log("Adding list");
        output = "list=" + youtube_list_id;
        if (youtube_index != "") {
            output += "&index=" + youtube_index;
        }
    }
    else {
        console.log("Error: No valid input found");
        return;
    }

    addSongInput.value = "";
    request.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

    // Set up a callback function to handle the response
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    console.log("Sending request with payload:", output);
    request.send(output);
}

function getPlaylist() {
    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/queue", true);
    request.onreadystatechange = function() {
        if (request.readyState == 4 && request.status == 200) {
            // Remove all queue items
            var queue = document.getElementById("queue");
            while (queue.firstChild) {
                queue.removeChild(queue.lastChild);
            }
            
            // Add new queue items
            // var playlist = request.responseText.slice(1, -1).split(", ");
            var playlist = JSON.parse(request.responseText);
            console.log("playlist=", playlist);
            
            // for each element in the json array
            var song_curr_id = playlist["current_id"];
            for (var song_id in playlist["songs"]) {
                // Create all necessary song divs
                var new_song_div = document.createElement("div");
                var new_song_thumbnail = document.createElement("img");
                var new_song_row = document.createElement("div");
                var new_song_name = document.createElement("span");
                var new_song_artist = document.createElement("span");
                var new_song_urls = document.createElement("div");
                var new_song_name_url = document.createElement("span");
                var new_song_artist_url = document.createElement("span");
                var new_song_queue_id = document.createElement("span");
                
                if (song_curr_id == song_id) {
                    new_song_div.className = "current-song";
                }
                else {
                    new_song_div.className = "song";
                }
                new_song_thumbnail.className = "thumbnail";
                new_song_row.className = "row";
                new_song_name.className = "song-name fs-5";
                new_song_artist.className = "song-artist fs-6";
                new_song_name_url.className = "song-url hidden";
                new_song_artist_url.className = "artist-url hidden";
                new_song_queue_id.className = "song-queue-id hidden";
                
                new_song_div.id = "song-" + song_id;
                new_song_div.setAttribute("data-bs-toggle", "modal");
                new_song_div.setAttribute("data-bs-target", "#SongModal");
                new_song_div.onclick = function() { loadSongDetails() };

                new_song_thumbnail.src = playlist["songs"][song_id]["thumbnail"];
                new_song_name.innerHTML = playlist["songs"][song_id]["title"];
                new_song_artist.innerHTML = playlist["songs"][song_id]["artist"];
                new_song_name_url.innerHTML = "https://youtube.com/watch?v=" + playlist["songs"][song_id]["video_id"];
                new_song_artist_url.innerHTML = "https://youtube.com/channel/" + playlist["songs"][song_id]["artist_id"];
                new_song_queue_id.innerHTML = song_id;

                // Create expected output
                new_song_div.appendChild(new_song_thumbnail);
                new_song_row.appendChild(new_song_name);
                new_song_row.appendChild(new_song_artist);
                new_song_row.appendChild(new_song_name_url);
                new_song_row.appendChild(new_song_artist_url);
                new_song_row.appendChild(new_song_queue_id);
                new_song_div.appendChild(new_song_row);
                new_song_div.appendChild(new_song_urls);
                queue.appendChild(new_song_div);
            }
        }
    }
    request.send();
}

// A function starts playing the song through the api
function playSong() {
    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/play", true);
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send();
}

// A function that plays the next song in the queue
function nextSong() {
    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/next", true);
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send();
}

// A function that plays the previous song in the queue
function previousSong() {
    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/previous", true);
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send();
}


function getVolume() {
    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/volume", true);
    request.onreadystatechange = function() {
        if (request.readyState == 4 && request.status == 200) {
            var volume = document.getElementById("VolumeSlider");
            var volume_text = document.getElementById("VolumeText");
            volume.value = request.responseText;
            volume_text.innerHTML = "Volume: " + volume.value;
            console.log("Volume set to", request.responseText);
        }
    }
    request.send();
}


function setVolume() {
    var request = new XMLHttpRequest();
    request.open("POST", "http://localhost:8080/volume", true);
    request.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    // Set up a callback function to handle the response
    var volume = document.getElementById("VolumeSlider");
    var volume_text = document.getElementById("VolumeText");
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                volume_text.innerHTML = "Volume: " + volume.value;
                var mute_button = document.getElementById("MuteButton");
                mute_button.innerHTML = "Mute";
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send("volume=" + volume.value);
}


function toggleMute() {
    var request = new XMLHttpRequest();
    request.open("POST", "http://localhost:8080/volume", true);
    request.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                var volume = document.getElementById("VolumeSlider");
                var volume_text = document.getElementById("VolumeText");
                var mute_button = document.getElementById("MuteButton");
                var set_volume = parseInt(request.responseText);
                console.log("Request successful:", set_volume);
                volume.value = set_volume;
                volume_text.innerHTML = "Volume: " + set_volume;
                if (set_volume > 0){
                    mute_button.innerHTML = "Mute";
                }
                else {
                    mute_button.innerHTML = "Unmute";
                }
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send("mute=toggle");
}

function loadSongDetails(event) {
    if (!event) {
        event = window.event;
    }

    var target = event.target || event.srcElement;
    if (target.id == "") {
        target = target.parentNode;
    }

    var queueId = document.getElementById("songModalQueuePosition");
    var queueIdChildNode = target.querySelector(".song-queue-id");
    if (queueIdChildNode != null) {
        queueId.innerHTML = parseInt(queueIdChildNode.innerHTML) + 1;
    } else {
        queueId.innerHTML = "X"; 
    }

    var song = document.getElementById("songModalSong");
    var songChildNode = target.querySelector(".song-name");
    if (songChildNode != null) {
        song.innerHTML = songChildNode.innerHTML;
    } else {
        song.innerHTML = "Unknown"; 
    }
    
    var artist = document.getElementById("songModalArtist");
    var artistChildNode = target.querySelector(".song-artist");
    if (artistChildNode != null) {
        artist.innerHTML = artistChildNode.innerHTML;
    } else {
        artist.innerHTML = "Unknown"; 
    }

    var songURL = document.getElementById("songModalSongURL");
    var songURLChildNode = target.querySelector(".song-url");
    if (songURLChildNode != null) {
        songURL.innerHTML = "Link to song";
        songURL.href = songURLChildNode.innerHTML;
    } else {
        songURL.innerHTML = "Unknown"; 
        songURL.href = "#";
    }

    var artistURL = document.getElementById("songModalArtistURL");
    var artistURLChildNode = target.querySelector(".artist-url");
    if (artistURLChildNode != null) {
        artistURL.innerHTML = "Link to artist";
        artistURL.href = artistURLChildNode.innerHTML;
    } else {
        artistURL.innerHTML = "Unknown"; 
        artistURL.href = "#";
    }
}

function playSpecificSong() {
    var queueParent = document.getElementById("songModalQueuePosition");
    var queueId = parseInt(queueParent.innerHTML)-1;
    console.log("Attempting to change to song id", queueId);
    
    var request = new XMLHttpRequest();
    
    request.open("POST", "http://localhost:8080/changesong", true);
    request.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send("queue_id=" + queueId);
}


function removeSpecificSong() {
    var queueParent = document.getElementById("songModalQueuePosition");
    var queueId = parseInt(queueParent.innerHTML)-1;
    console.log("Attempting to remove song id", queueId);
    
    var request = new XMLHttpRequest();
    
    request.open("POST", "http://localhost:8080/removesong", true);
    request.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send("queue_id=" + queueId);
}

function stop() {
    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/stop", true);
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send();
}

function clearPlaylist() {
    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/clearqueue", true);
    request.onreadystatechange = function() {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
                console.log("Request successful:", request.responseText);
                getPlaylist();
            } else {
                console.error("Request failed with status:", request.statusText);
            }
        }
    };
    request.send();
}