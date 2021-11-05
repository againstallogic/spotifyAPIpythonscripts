__author__ = 'bdm4, James Allsup'


import requests, json
import subprocess
import sys
import csv
import urllib3
import sys
from time import sleep
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#This script:
# 1) Retrieves tracks and associated genres from a playlist
# 2) Filters out tracks by genre
# 3) Adds the remaining tracks to a new playlist

# INSTRUCTIONS:
# 1) Add valid access_token
# 2) Add search playlist and target playlist fields
# 3) Add genre to filter on
access_token = 'BQBjqTGQz4aeJKu05TiFcCxw5neKqCJiA3B-cm78InEtO8grSzedd9DSud9gxgn03jvzfyc5fDeLUvDFY0BDDDuhf1-K0DFCe8d513OlBcMtN_Z1d51XoEoQtRj8_kNUhwKE-61gWFFEFhhx5a3FMIoNWoxeMT77vtbsSIFrrNiCLCH9Ufe9yFjFPIwayW0Jv4A'

search_playlist_id = '4wYwzTatuFG1G5Mm6QxDf6'
populate_playlist_id = '67tq6cEqQ2zBdt1Y2HkHUO'

api_call_headers = {'Authorization': 'Bearer ' + access_token}

#get track info and artist ids
total_tracks = 2708
track_it = 0
data = {}
data['tracks'] = []
x=0
#max is 100
limit=100
while x<30:
    offset=str(x*limit)
    getPlaylistItems = "https://api.spotify.com/v1/playlists/" + search_playlist_id + "/tracks?fields=items(track.artists(id),track.name,track.id)&limit=" + str(limit) + "&offset=" + offset

    api_call_response = requests.get(getPlaylistItems, headers=api_call_headers, verify=False)
    if api_call_response.status_code != 200:
        sys.exit("API Request Error")
    json_data = json.loads(api_call_response.text)


    for item in json_data['items']:
        trackName=item['track']['name']
        trackID=item['track']['id']
        artistID=item['track']['artists'][0]['id']
        data['tracks'].append({
            'trackName': trackName,
            'trackID': trackID,
            'artistID': artistID
        })
        print("Track " + str(track_it) + "/" + str(total_tracks))
        track_it+=1
    x+=1

#build track feature dataset
#artist limit max is 50
track_limit=100
track_count=0
progress_count=0
track_data = {}
track_data['tracks'] = []
getPlaylistItems="https://api.spotify.com/v1/audio-features?ids="

for track in data['tracks']:
    if track_count==0:
        getPlaylistItems += track['trackID']
        track_count+=1
        progress_count+=1
        print("Genre " + str(progress_count) + "/" + str(total_tracks))

    elif track_count<track_limit:
        getPlaylistItems = getPlaylistItems + "," + track['trackID']
        track_count+=1
        progress_count+=1
        print("Genre " + str(progress_count) + "/" + str(total_tracks))
    else:
        api_call_response = requests.get(getPlaylistItems, headers=api_call_headers, verify=False)
        if api_call_response.status_code != 200:
            print("API Request Error")
        json_data = json.loads(api_call_response.text)
        print(json_data)
        for track_feature in json_data['audio_features']:
            track_data['tracks'].append({
                'track_id': track_feature['id'],
                'loudness': track_feature['loudness'],
                'tempo': track_feature['tempo'],
                'energy': track_feature['energy'],
                'acousticness': track_feature['acousticness']
            })
        print("Genre " + str(progress_count) + "/" + str(total_tracks))
        getPlaylistItems = "https://api.spotify.com/v1/audio-features?ids="
        getPlaylistItems += track['trackID']
        track_count=1
        progress_count+=1
api_call_response = requests.get(getPlaylistItems, headers=api_call_headers, verify=False)
if api_call_response.status_code != 200:
    print("API Request Error")
json_data = json.loads(api_call_response.text)
for track_feature in json_data['audio_features']:
    track_data['tracks'].append({
        'track_id': track_feature['id'],
        'loudness': track_feature['loudness'],
        'tempo': track_feature['tempo'],
        'energy': track_feature['energy'],
        'acousticness': track_feature['acousticness']
    })

#join audio featurre dataset to data
for track in data['tracks']:
    for track_feature in track_data['tracks']:
        if track['trackID'] == track_feature['track_id']:
            track['loudness'] = track_feature['loudness']
            track['tempo'] = track_feature['tempo']
            track['energy'] = track_feature['energy']
            track['acousticness'] = track_feature['acousticness']

#filter on feature
filteredData = {}
filteredData['tracks'] = []
for track in data['tracks']:
    if track['acousticness']<0.01:
        filteredData['tracks'].append({
            'trackID': track['trackID']
        })
if len(filteredData['tracks'])==0:
    sys.exit("No Tracks Found")
else:
    print(str(len(filteredData['tracks'])) + " tracks found" )

#create playlist
countlimit=0
tracklist={}
tracklist['uris'] = []
uristring=""
for track in filteredData['tracks']:
    ##limit is 100
    if countlimit <90:
        uristring+= "spotify:track:" + track['trackID']
        tracklist['uris'].append(uristring)
        uristring=""
        countlimit+=1
    else:
        getPlaylistItems = "https://api.spotify.com/v1/playlists/" + populate_playlist_id + "/tracks"
        api_call_response = requests.post(getPlaylistItems, data=json.dumps(tracklist), headers=api_call_headers, verify=False)
        if api_call_response.status_code != 201:
            print("API Request Error")
        tracklist={}
        tracklist['uris'] = []
        uristring+= "spotify:track:" + track['trackID']
        tracklist['uris'].append(uristring)
        uristring=""
        countlimit=1
        continue

getPlaylistItems = "https://api.spotify.com/v1/playlists/" + populate_playlist_id + "/tracks"
api_call_response = requests.post(getPlaylistItems, data=json.dumps(tracklist), headers=api_call_headers, verify=False)
if api_call_response.status_code != 201:
    print("API Request Error")
