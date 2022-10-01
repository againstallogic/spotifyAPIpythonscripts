__author__ = 'bdm4, James Allsup'

import requests
import json
from flask import Flask, redirect, url_for, session, request
from flask_oauthlib.client import OAuth, OAuthException

import subprocess
import sys
import os
import urllib3
from datetime import datetime
from requests_oauthlib import OAuth2Session
import webbrowser
from threading import Timer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



#Timer(2, webbrowser.open('http://127.0.0.1:5000/')).start();

SPOTIFY_APP_ID = '329e310f27a64fe6b6498877b76d3732'
SPOTIFY_APP_SECRET = '655a33bed21e4c25971346944f8a1220'

webbrowser.open('http://127.0.0.1:5000/')

app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

spotify = oauth.remote_app(
    'spotify',
    consumer_key=SPOTIFY_APP_ID,
    consumer_secret=SPOTIFY_APP_SECRET,
    # Change the scope to match whatever it us you need
    # list of scopes can be found in the url below
    # https://developer.spotify.com/web-api/using-scopes/
    request_token_params={'scope': 'user-top-read user-read-currently-playing user-library-read playlist-modify-private'},
    base_url='https://accounts.spotify.com',
    request_token_url=None,
    access_token_url='/api/token',
    authorize_url='https://accounts.spotify.com/authorize'
)




@app.route('/')
def index():
    return redirect(url_for('login'))




@app.route('/login')
def login():
    callback = url_for(
        'spotify_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return spotify.authorize(callback=callback)

@app.route('/login/authorized')
def spotify_authorized():
    resp = spotify.authorized_response()
    if resp is None:
        return 'Access denied: reason={0} error={1}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: {0}'.format(resp.message)

    session['oauth_token'] = (resp['access_token'], '')

    me = spotify.get('/me')
    print(resp['access_token'])
    access_token=resp['access_token']
    return getartistdiscog(access_token)


@spotify.tokengetter
def get_spotify_oauth_token():
    return session.get('oauth_token')

def getartistdiscog(access_token):
    access_token = access_token

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
    return 'playlist updated'



if __name__ == '__main__':

    app.run(debug=True, use_reloader=False)
