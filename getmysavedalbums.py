__author__ = 'bdm4, James Allsup'


import requests, json
import subprocess
import sys
import csv
import urllib3
import sys
from time import sleep
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()
    sleep(0.00001)

#use postman Oauth2 to get spotify access_token
# paste here
access_token = 'BQAO_TC7BBOMbeRFQTiokprjSAGaszCvtx3JzKt0ac7iEDbnkWDaOSD4lSMj83MdfV8D852FaoHOEAL4BXeCH5tfrrTMkuymfvhc3mqxwF5HrrOQGgmROlDYjGyLMsGcwOnVypdOp4Zig8pldyA3MoEU_ls2WIoc51rg_0ONC6vAJHliSW1001WBqcXfbYO0hsw'

api_call_headers = {'Authorization': 'Bearer ' + access_token}

x = 0
album_it = 0
album_data = {}
album_data['albums'] = []
#go up to 500 albums
while x < 10:
    offset = str(x * 50)
    getSavedAlbums = "https://api.spotify.com/v1/me/albums" + "?limit=50&offset=" + offset
    api_call_response = requests.get(getSavedAlbums, headers=api_call_headers, verify=False)
    if api_call_response.status_code != 200:
        print(api_call_response)
        sys.exit("API Request Error")
    json_data = json.loads(api_call_response.text)
    count_albums = json_data['total']
    for item in json_data['items']:
        album_length = 0
        for track in item['album']['tracks']['items']:
            album_length+=track['duration_ms']
        album_length = album_length/60000
        #standardize releae date formats
        if len(item['album']['release_date'])==4:
            release_date = "01/01/" + item['album']['release_date']
        if len(item['album']['release_date'])==7:
            release_date = "01/01/" + item['album']['release_date'][:4]
        if len(item['album']['release_date'])>7:
            release_date = item['album']['release_date']
        album_data['albums'].append({
            'album_name': item['album']['name'],
            'artist': item['album']['artists'][0]['name'],
            'artist_id': item['album']['artists'][0]['id'],
            'release_date': release_date,
            'added_at': item['added_at'],
            'album_length': album_length
        })
        album_it+=1
        progress(album_it,count_albums,status='retrieving data')
    x += 1



#build artist/genre dataset
#artist limit max is 50
artist_limit=50
artist_count=0
progress_count=0
artist_data = {}
artist_data['artists'] = []
getPlaylistItems="https://api.spotify.com/v1/artists?ids="

for album in album_data['albums']:
    if artist_count==0:
        getPlaylistItems += album['artist_id']
        artist_count+=1
        progress_count+=1
        print("Genre " + str(progress_count) + "/" + str(count_albums))

    elif artist_count<artist_limit:
        getPlaylistItems = getPlaylistItems + "," + album['artist_id']
        artist_count+=1
        progress_count+=1
        print("Genre " + str(progress_count) + "/" + str(count_albums))
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
        print("Genre " + str(progress_count) + "/" + str(count_albums))
        getPlaylistItems = "https://api.spotify.com/v1/artists?ids="
        getPlaylistItems += album['artist_id']
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
for album in album_data['albums']:
    for artist in artist_data['artists']:
        if album['artist_id'] == artist['artist_id']:
            album['genres'] = artist['genres']

#write to csv
with open('savedalbums.csv', mode='w+') as csv_file:
    fieldnames = ['album_name', 'artist', 'release_date', 'added_at', 'album_length', 'genres']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for album in album_data['albums']:
        writer.writerow({
            'album_name': album['album_name'],
            'artist': album['artist'],
            'release_date': album['release_date'],
            'added_at': album['added_at'],
            'album_length': album['album_length'],
            'genres': album['genres']
        })
