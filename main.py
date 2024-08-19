import spotipy
import json
from spotipy.oauth2 import SpotifyOAuth
import sys
import random

from PyQt6.QtWidgets import QApplication, QSlider, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout
from PyQt6.QtGui import QIcon, QIntValidator
from PyQt6.QtCore import Qt

class BetterRadioApp(QWidget):
    def __init__(self):
        super().__init__()

        scopes = ["user-library-read", "user-read-currently-playing", "user-follow-read",
          "user-read-playback-state", "user-modify-playback-state"]

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="121582b08b3f42919543e5c7461e698d",
                                                    client_secret="3bdf3be45b034a2e82c7bb656c2864b5",
                                                    redirect_uri="http://localhost:8080",
                                                    scope=scopes))

        self.setWindowTitle("BetterSpotifyRadio")
        self.setWindowIcon(QIcon('BetterSpotifyRadio.ico'))
        self.resize(700, 500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.radioSongNewnessSlider = QSlider(Qt.Orientation.Horizontal, self)
        self.radioSongNewnessSlider.setMinimum(0)
        self.radioSongNewnessSlider.setMaximum(100)
        self.radioSongNewnessSlider.setValue(50)
        self.radioSongNewnessSlider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.radioSongNewnessSlider.setTickInterval(1)

        numberOfRadioTrackLabel = QLabel("Amount of songs to recommend", self)
        self.numberOfRadioTracks = QLineEdit(self)
        self.numberOfRadioTracks.setPlaceholderText("Enter number from 1-50")
        self.numberOfRadioTracks.setValidator(QIntValidator(1, 50, self))
        layout.addWidget(numberOfRadioTrackLabel)
        layout.addWidget(self.numberOfRadioTracks)

        similarToTrackButton = QPushButton("GET SIMILAR SONGS BASED ON TRACK PLAYING", self)
        similarToAlbumButton = QPushButton("GET SIMILAR SONGS BASED ON ALBUM OF TRACK PLAYING", self)
        similarToPlaylistButton = QPushButton("GET SIMILAR SONGS BASED ON PLAYLIST PLAYING", self)
        layout.addWidget(similarToTrackButton)
        layout.addWidget(similarToAlbumButton)
        layout.addWidget(similarToPlaylistButton)
        similarToTrackButton.clicked.connect(self.get_similar_to_track_songs)
        similarToAlbumButton.clicked.connect(self.get_similar_to_album_songs)
        similarToPlaylistButton.clicked.connect(self.get_similar_to_playlist_songs)


    def add_tracks(self, fiftyTrackList, recTrackLimit, offset=0):
        for i in range(len(fiftyTrackList)):
            if len(self.uniqueTrackRecs) == recTrackLimit: 
                break
            if fiftyTrackList[i] != self.recUniqueSongs:
                self.uniqueTrackRecs.append(self.recommendationTracksURIs[i+offset])

    def add_collection_rec_tracks(self, trackCollectionTracks, fiftyTrackList, recTrackLimit, offset=0):
        for i in range(len(fiftyTrackList)):
            if len(self.uniqueTrackRecs) == recTrackLimit: 
                break
            if fiftyTrackList[i] != self.recUniqueSongs:
                if self.recommendationTracksURIs[i+offset] not in trackCollectionTracks:
                    self.uniqueTrackRecs.append(self.recommendationTracksURIs[i+offset])
    
    def add_generated_recs_to_queue_from_tracks(self, seed_tracks, artistURIs):
        recommendations = self.sp.recommendations(seed_artists=artistURIs, seed_tracks=seed_tracks, limit=100)["tracks"]

        self.recommendationTracksURIs = [track["uri"] for track in recommendations]
        recTrackLimit = (int)(self.numberOfRadioTracks.text())
        self.uniqueTrackRecs = []
        self.recUniqueSongs = True

        first50Tracks = self.sp.current_user_saved_tracks_contains(self.recommendationTracksURIs[0:50])
        self.add_tracks(first50Tracks, recTrackLimit)
            
        if len(self.uniqueTrackRecs) < recTrackLimit:
            second50Tracks = self.sp.current_user_saved_tracks_contains(self.recommendationTracksURIs[50:])
            self.add_tracks(second50Tracks, recTrackLimit, 50)
                
        for uniqueTrack in self.uniqueTrackRecs:
            self.sp.add_to_queue(uniqueTrack)

    def add_generated_recs_to_queue_from_track_collection(self, trackCollectionTracks, seed_tracks, artistURIs):
        recommendations = self.sp.recommendations(seed_artists=artistURIs, seed_tracks=seed_tracks, limit=100)["tracks"]

        self.recommendationTracksURIs = [track["uri"] for track in recommendations]
        recTrackLimit = (int)(self.numberOfRadioTracks.text())
        self.uniqueTrackRecs = []
        self.recUniqueSongs = True

        first50Tracks = self.sp.current_user_saved_tracks_contains(self.recommendationTracksURIs[0:50])
        self.add_collection_rec_tracks(trackCollectionTracks, first50Tracks, recTrackLimit)
            
        if len(self.uniqueTrackRecs) < recTrackLimit:
            second50Tracks = self.sp.current_user_saved_tracks_contains(self.recommendationTracksURIs[50:])
            self.add_collection_rec_tracks(trackCollectionTracks, second50Tracks, recTrackLimit, 50)
                
        for uniqueTrack in self.uniqueTrackRecs:
            self.sp.add_to_queue(uniqueTrack)

    def get_randomised_list_of_tracks_from_collection(self, playlistOrAlbum, currentlyPlayingSong):
        if playlistOrAlbum == "album": 
            collectionURI = currentlyPlayingSong["item"]["album"]["id"]
            fetchLimit = 50
        else: 
            collectionURI = currentlyPlayingSong["context"]["uri"]
            fetchLimit = 100
        collectionTracks = []
        collectionTrackGatherIterations = 0
        while collectionTrackGatherIterations*fetchLimit == len(collectionTracks): #for albums >50 tracks and playlists >100 tracks
            if playlistOrAlbum == "album": collectionTracks.extend(self.sp.album_tracks(collectionURI, fetchLimit, collectionTrackGatherIterations*fetchLimit)['items'])
            else: collectionTracks.extend(self.sp.playlist_tracks(collectionURI, limit=fetchLimit, offset=collectionTrackGatherIterations*fetchLimit)['items'])
            collectionTrackGatherIterations += 1
        if playlistOrAlbum == "album": trackURIs = [track["uri"] for track in collectionTracks]
        else: trackURIs = [track["track"]["uri"] for track in collectionTracks]
        random.shuffle(trackURIs)
        return trackURIs

    def get_recs(self, mode):
        if self.numberOfRadioTracks.text() == "": print("nothing")

        else:
            currentlyPlayingSong = self.sp.currently_playing()
            artists = currentlyPlayingSong["item"]["album"]["artists"]
            artistURIs = [artist["uri"] for artist in artists]

            if currentlyPlayingSong != None:

                if mode == "track":
                    currentlyPlayingSongURI = currentlyPlayingSong["item"]["uri"]
                    self.add_generated_recs_to_queue_from_tracks([currentlyPlayingSongURI], artistURIs)

                elif mode == "album":
                    albumTrackURIs = self.get_randomised_list_of_tracks_from_collection("album", currentlyPlayingSong)
                    self.add_generated_recs_to_queue_from_track_collection(albumTrackURIs, albumTrackURIs[0:4], artistURIs)

                elif mode == "playlist":
                    if currentlyPlayingSong["context"]["type"] == "playlist": 
                        playlistTrackURIs = self.get_randomised_list_of_tracks_from_collection("playlist", currentlyPlayingSong)
                        self.add_generated_recs_to_queue_from_track_collection(playlistTrackURIs, playlistTrackURIs[0:4], artistURIs)

                    else: pass

            else: print("no song playing")

    def get_similar_to_track_songs(self):
        self.get_recs(mode="track")

    def get_similar_to_album_songs(self):
        self.get_recs(mode="album")

    def get_similar_to_playlist_songs(self):
        self.get_recs(mode="playlist")

app = QApplication(sys.argv)
window = BetterRadioApp()
window.show()
sys.exit(app.exec())