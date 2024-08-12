import spotipy
# import json
from spotipy.oauth2 import SpotifyOAuth

print("starting")

scopes = ["user-library-read", "user-read-currently-playing", "user-follow-read",
          "user-read-playback-state", "user-modify-playback-state"]

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="121582b08b3f42919543e5c7461e698d",
                                               client_secret="3bdf3be45b034a2e82c7bb656c2864b5",
                                               redirect_uri="http://localhost:8080",
                                               scope=scopes))

currentlyPlayingSong = sp.currently_playing()

if currentlyPlayingSong != None:

    albumOrPlaylist = currentlyPlayingSong["context"]["type"]

    currentlyPlayingSongURI = currentlyPlayingSong["item"]["uri"]

    artists = currentlyPlayingSong["item"]["album"]["artists"]
    artistURIs = [artist["uri"] for artist in artists]

    recommendations = sp.recommendations(seed_artists=artistURIs, seed_tracks=[currentlyPlayingSongURI], limit=100)["tracks"]

    recommendationTracksURIs = [track["uri"] for track in recommendations]

  
    first50Tracks = sp.current_user_saved_tracks_contains(recommendationTracksURIs[0:50])
    recTrackLimit = 15
    uniqueTrackRecs = []
    for i in range(len(first50Tracks)):
        if len(uniqueTrackRecs) == recTrackLimit: 
            break
        if first50Tracks[i] == False:
            uniqueTrackRecs.append(recommendationTracksURIs[i])
        
    if len(uniqueTrackRecs) < recTrackLimit:
        second50Tracks = sp.current_user_saved_tracks_contains(recommendationTracksURIs[50:])
        for i in range(len(second50Tracks)):
            if len(uniqueTrackRecs) == recTrackLimit: 
                break
            if second50Tracks[i] == False:
                uniqueTrackRecs.append(recommendationTracksURIs[i+50])

            
    print("found " + str(len(uniqueTrackRecs))  + " new songs and adding them to the queue")

    print("Track URIs")
    print(uniqueTrackRecs)
    for uniqueTrack in uniqueTrackRecs:
        sp.add_to_queue(uniqueTrack)
else:
    print("no song playing")