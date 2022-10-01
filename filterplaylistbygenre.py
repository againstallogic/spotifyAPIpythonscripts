__author__ = 'bdm4, James Allsup'


import requests, json
import subprocess
import sys
import csv
import urllib3
import sys
from time import sleep
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#This script:
# 1) Retrieves tracks and associated genres from a playlist
# 2) Filters out tracks by genre
# 3) Sorts the tracks by release date ascending
# 4) Adds the remaining tracks to a new playlist

# INSTRUCTIONS:
# 1) Add valid access_token
# 2) Add search playlist and target playlist fields
# 3) Add genre to filter on
access_token = 'BQBh7HBE8w5zSpJQjLCQnxOS1zbqD5BvyTYCoTzd0XvZcYnjK6_JPBXeopVyufb7koE_kfV9vxAqarZ3IT_KwrnQZldPwLDbz-3rwWlReaSnaePxncJAJ_S0SsW4rE4rD9-kbkcfl8xau3F_e-HQy5UgmEmWyu9bMZrCsXQfMLCVYYrjfYrp2kMKyvddpmDWhY1OzZhMg5pIEuakN3_jLnsjbJefTgH1eJwV'

search_playlist_id = '4wYwzTatuFG1G5Mm6QxDf6'
populate_playlist_id = '67tq6cEqQ2zBdt1Y2HkHUO'
search = 'latin'

api_call_headers = {'Authorization': 'Bearer ' + access_token}

#get track info and artist ids
total_tracks = 3880
track_it = 0
data = {}
data['tracks'] = []
x=0
#max results per request is 100
limit=100
while x<50:
    offset=str(x*limit)
    getPlaylistItems = "https://api.spotify.com/v1/playlists/" + search_playlist_id + "/tracks?fields=items(track.artists(id),track.name,track.id,track.album.release_date)&limit=" + str(limit) + "&offset=" + offset

    api_call_response = requests.get(getPlaylistItems, headers=api_call_headers, verify=False)
    if api_call_response.status_code != 200:
        print(api_call_response)
        sys.exit("API Request Error")
    json_data = json.loads(api_call_response.text)

    for item in json_data['items']:
        trackName=item['track']['name']
        trackID=item['track']['id']
        artistID=item['track']['artists'][0]['id']
        #standardize release date formats
        if len(item['track']['album']['release_date'])==4:
            release_date = int(item['track']['album']['release_date'] + "0101")
        if len(item['track']['album']['release_date'])==7:
            release_date = int(item['track']['album']['release_date'][:4] + "0101")
        if len(item['track']['album']['release_date'])>7:
            release_date = int(item['track']['album']['release_date'][:4] + item['track']['album']['release_date'][5:7] + item['track']['album']['release_date'][8:10])
        #releaseDate=item['track']['album']['release_date']
        data['tracks'].append({
            'trackName': trackName,
            'trackID': trackID,
            'artistID': artistID,
            'releaseDate': release_date
        })
        print("Track " + str(track_it) + "/" + str(total_tracks))
        track_it+=1
    x+=1

#build artist/genre dataset
#artist limit max is 50
artist_limit=50
artist_count=0
progress_count=0
artist_data = {}
artist_data['artists'] = []
getPlaylistItems="https://api.spotify.com/v1/artists?ids="

for track in data['tracks']:
    if artist_count==0:
        getPlaylistItems += track['artistID']
        artist_count+=1
        progress_count+=1
        print("Genre " + str(progress_count) + "/" + str(total_tracks))

    elif artist_count<artist_limit:
        getPlaylistItems = getPlaylistItems + "," + track['artistID']
        artist_count+=1
        progress_count+=1
        print("Genre " + str(progress_count) + "/" + str(total_tracks))
    else:
        api_call_response = requests.get(getPlaylistItems, headers=api_call_headers, verify=False)
        if api_call_response.status_code != 200:
            print("API Request Error")
        json_data = json.loads(api_call_response.text)
        for artist in json_data['artists']:
            artist_data['artists'].append({
                'artist_id': artist['id'],
                'genres': artist['genres']
            })
        print("Genre " + str(progress_count) + "/" + str(total_tracks))
        getPlaylistItems = "https://api.spotify.com/v1/artists?ids="
        getPlaylistItems += track['artistID']
        artist_count=1
        progress_count+=1
api_call_response = requests.get(getPlaylistItems, headers=api_call_headers, verify=False)
if api_call_response.status_code != 200:
    print("API Request Error")
json_data = json.loads(api_call_response.text)
for artist in json_data['artists']:
    artist_data['artists'].append({
        'artist_id': artist['id'],
        'genres': artist['genres']
    })

#join genre dataset to data
for track in data['tracks']:
    for artist in artist_data['artists']:
        if track['artistID'] == artist['artist_id']:
            track['genres'] = artist['genres']

#filter on genre
filteredData = {}
filteredData['tracks'] = []
for track in data['tracks']:
    genrecontainskeyword=0
    for genre in track['genres']:
        if search in genre :
            genrecontainskeyword+=1
    if genrecontainskeyword>0:
        filteredData['tracks'].append({
            'trackID': track['trackID'],
            'releaseDate': track['releaseDate']
        })
if len(filteredData['tracks'])==0:
    sys.exit("No Tracks Found")
else:
    print(str(len(filteredData['tracks'])) + " tracks found" )



#sort by release datetime
#sortedFilteredData = sorted(filteredData['tracks'], key=lambda x: datetime.strptime(x['releaseDate'], '%Y-%m-%d'))
sortedFilteredData = sorted(filteredData['tracks'], key = lambda x:x["releaseDate"])
print(sortedFilteredData)

#create playlist
countlimit=0
tracklist={}
tracklist['uris'] = []
uristring=""
for track in sortedFilteredData:
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
