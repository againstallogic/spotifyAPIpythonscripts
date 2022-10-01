__author__ = 'bdm4, James Allsup'

#install library: pip install requests_oauthlib
import requests, json
import subprocess
import sys
import csv
import urllib3
import sys
from time import sleep
from datetime import datetime

from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from oauthlib.oauth2 import WebApplicationClient

client_id = 'xxxxx'



#This script:
# 1) Retrieves albums of an artist
# 2) sorts them by release date
# 3) gets tracks of each album
# 3) Adds the tracks to a new playlist

# INSTRUCTIONS:
# 1) Use postman Oauth2 to get spotify access_token & add below
# 2) Add artist playlist and target playlist fields
# 3) Add genre to filter on



#set variables
access_token = 'BQCLbh-NSGsOG1SzjjzeWnX-hqDnJ5eUJuEsBWhIUzO67wmhfGMkA8Rmn_HCAcIFolOURmoMLDGC4EVKL0wHV0wVD-7VU89xW07jndIUWiX8C_E92c2ogO_GqtxhvapG_78WhLQRFxL0P_BHkk2gjepT_CUh9cLxA2lFX5V26SvTAZhpJSTGP3vI6N1T6WOKuvA'

artist_id = '1oPRcJUkloHaRLYx0olBLJ'
populate_playlist_id = '67tq6cEqQ2zBdt1Y2HkHUO'

api_call_headers = {'Authorization': 'Bearer ' + access_token}

#get artist items
albumData = {}
albumData['albums'] = []
x=0
#max is 50
limit=50
while x<5:
    offset=str(x*limit)
    getArtistItems = "https://api.spotify.com/v1/artists/" + artist_id + "/albums?limit=" + str(limit) + "&offset=" + offset

    api_call_response = requests.get(getArtistItems, headers=api_call_headers, verify=False)
    if api_call_response.status_code != 200:
        sys.exit("API Request Error")
    json_data = json.loads(api_call_response.text)

    #add albums to json list
    for item in json_data['items']:
        #only include items available in US
        is_us_market=0
        for market in item['available_markets']:
            if market=='US':
                is_us_market+=1
        if is_us_market>0:
            #add albums to json list
            albumID=item['id']
            albumName=item['name']
            #handle different album release date formats
            if len(item['release_date'])<5:
                albumReleaseDate = item['release_date'] + "-01-01"
            else:
                albumReleaseDate=item['release_date']
            albumData['albums'].append({
                'albumID': albumID,
                'albumName': albumName,
                'albumReleaseDate': albumReleaseDate
            })
    x+=1

print(albumData['albums'])
#sort albums by release date asc
sortedAlbums = sorted(albumData['albums'], key=lambda x: datetime.strptime(x['albumReleaseDate'], '%Y-%m-%d'))



trackData = {}
trackData['tracks'] = []

for album in sortedAlbums:
    albumID = album['albumID']
    getAlbumTracks = "https://api.spotify.com/v1/albums/" + albumID

    api_call_response = requests.get(getAlbumTracks, headers=api_call_headers, verify=False)
    if api_call_response.status_code != 200:
        sys.exit("API Request Error")
    json_data = json.loads(api_call_response.text)

    for track in json_data['tracks']['items']:
        track_has_artist = 0
        for artist in track['artists']:
            if artist['id']==artist_id:
                track_has_artist+=1
        if track_has_artist>0:
            trackName = track['name']
            trackID = track['id']
            trackData['tracks'].append({
                'trackName': trackName,
                'trackID': trackID
            })

print("albums sorted")

#create playlist
countlimit=0
tracklist={}
tracklist['uris'] = []
uristring=""
for track in trackData['tracks']:
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
