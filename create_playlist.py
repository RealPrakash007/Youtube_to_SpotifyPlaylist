import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from secrets import spotify_token, spotify_user_id


class CreatePlaylist:
    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    def get_youtube_client(self):
        """ Log Into Youtube, Copied from Youtube Data API """
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def get_liked_videos(self):
        
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like",
            maxResults=45
        )
        response = request.execute()

        
        ydl_opts = {
         'nocheckcertificate': True,
         }
        print(response)
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
                item["id"])

            
            video = youtube_dl.YoutubeDL(ydl_opts).extract_info(
                youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            if song_name is not None and artist is not None:
                
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist": artist,

                    
                    "spotify_uri": self.get_spotify_uri(song_name, artist)

                }

    def create_playlist(self):
        
        request_body = json.dumps({
            "name": "Youtube Liked Vids New",
            "description": "All Liked Youtube Videos",
            "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(
            spotify_user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()

        # playlist id
        return response_json["id"]

    def get_spotify_uri(self, song_name, artist):
        
        query = "https://api.spotify.com/v1/search?q={}&type=track&market=US&offset=0&limit=20".format(
            song_name
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }

        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        
        if not songs:
            return []
        uri = songs[0]["uri"]


        return uri

    def get_current_songs_from_playlist(self,playlist_id):
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        response_json = response.json()
        songs = response_json["items"]


        
        uri = []
        if not songs:
            return []
        
        for i in range(len(songs)):
            uri.append(songs[i]["track"]["uri"])
        

        return uri


    def add_song_to_playlist(self,playlist_id):
        
        self.get_liked_videos()
        

        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]
        
        #if playlist exists, else create new one.
        if playlist_id == "":
            
            playlist_id = self.create_playlist()
            
            request_data = json.dumps(uris)
        else:
            exist = self.get_current_songs_from_playlist(playlist_id)
            res = []
            for song in uris:
                if song not in exist:
                    res.append(song)

            
            
            request_data = json.dumps(res)


        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        

        response_json = response.json()
        return response_json


if __name__ == '__main__':
    txt = input("Input playlist_id (if new, press enter): ")
    cp = CreatePlaylist()
    cp.add_song_to_playlist(txt)

