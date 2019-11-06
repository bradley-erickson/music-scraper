"""
Created on Sat Mar  9 20:50:19 2019

Brad Erickson

Music Webscraper
"""
#Imports
import requests
import bs4
import spotipy
import spotipy.util as util
import csv
import datetime
import re
import logging


# Genius API token information
genius_access_token = 
genius_token = 'Bearer {}'.format(genius_access_token)
genius_headers = {'Authorization': genius_token}

# Spotipy API token information 
spotify_username = 
spotify_client_id = 
spotify_client_secret = 
spotify_redirect_uri = "http://localhost/"
spotify_user_top_read_scope = "user-top-read"
spotify_user_library_read_scope = "user-library-read"

#top_read_token = util.prompt_for_user_token(spotify_username, spotify_user_top_read_scope, spotify_client_id, spotify_client_secret, spotify_redirect_uri)  
#library_read_token = util.prompt_for_user_token(spotify_username, spotify_user_library_read_scope, spotify_client_id, spotify_client_secret, spotify_redirect_uri)

# Glabal variables
genre_set = set([])
artist_set = set([])
track_set = set([])
artist_id_dictionary = {}
album_id_dictionary = {}
song_id_dictionary = {}

artist_headers = ["ID", "NAME", "FOLLOWERS", "GENRES", "POPULARITY", "DISCOGRAPHY"]
album_headers = ["ID", "NAME", "PRIMARY_ARTISTS", "TYPE", "RELEASE_DATE", "TRACK_LIST"]
track_headers = ["ID", "NAME", "PRIMARY_ARTISTS", "ALBUM", "DISC_NUMBER", "TRACK_NUMBER", "DURATION", "EXPLICIT", "LYRICS"]

date_time = str(datetime.date.today())
date_time = date_time.replace(' ', '_').replace(':', '-')
log_name = date_time + "_music_webscraper.log"
logging.basicConfig(filename=log_name, level=logging.INFO)


def get_top_artists(time_frame, count):
    """ Return Spotipy user's top artists """
    
    top_artists = []
      
    sp = spotipy.Spotify(auth=top_read_token)
    
    results = sp.current_user_top_artists(time_range=time_frame, limit=count)
    
    for artist in results['items']:
        top_artists.append(artist['name'])
        
        if artist['name'] in artist_id_dictionary:
            pass
        else:
            logging.info(" Added top artist: " + artist['name'])
            artist_id_dictionary[artist['name']] = artist['id']
        
    return top_artists


def get_weighted_artist_dictionary():
    """ Return a dictionary of artists and counts  """
    
    artist_dictionary = {}
    
    term = ["short_term", "medium_term", "long_term"]
    
    for item in term:
        artist_json_list = get_top_artists(item)
        for artist in artist_json_list:
            if artist in artist_dictionary:
                artist_dictionary[artist] += 1
            else:
                artist_dictionary[artist] = 1
    
    return artist_dictionary


def get_weighted_genre_dictionary(artist_list):
    """ Return a dictionary for genres and counts """
    
    genre_dictionary = {}
    
    for artist in artist_list:
        artist_json = sp.artist(artist_id_dictionary[artist])
        for genre in artist_json['genres']:
            if genre in genre_dictionary:
                genre_dictionary[genre] += 1
            else:
                genre_dictionary[genre] = 1
    
    return genre_dictionary


def get_artist_json(artist_name):
    """ Return Spotipy artist json """
    
    try:
        results = sp.search(q='artist:' + artist_name, type='artist')
    except:
        logging.error(" Bad request searching for " + artist_name)
        return None
    
    items = results['artists']['items']
    
    return items[0]
    

def get_related_artist_json(artist_id):
    """ Return Spotipy artists related to given artist """
    
    try:
        results = sp.artist_related_artists(artist_id)
        return results
    except:
        logging.error(" Bad request finding related artists for " + artist_id)
        return None

    
def get_artist_info_list(artist_json):
    """ Return information about artist """
    
    csv_data = []
    
    csv_data.append(artist_json['id'])
    csv_data.append(artist_json['name'].replace(',',''))
    csv_data.append(artist_json['followers']['total'])
    
    genre_string = ''
    for genre in artist_json['genres']:
        genre_string += (genre.replace(',','') + " | ")
    genre_string = genre_string[:-3]
    csv_data.append(genre_string)
    
    csv_data.append(artist_json['popularity'])
    
    discography_string = ''
    disc_list_json = get_artist_discography_list_json(artist_json['name'])
    try:
        for disc in disc_list_json:
            discography_string += (disc['name'].replace(',','') + " | ")
        discography_string = discography_string[:-3]
    except:
        logging.info(" Empty discography list for " + artist_json['name'])
        discography_string += ("?")
    csv_data.append(discography_string)
    
    return csv_data


def get_artist_discography_list_json(artist_name):
    """ Return combination of albums and singles by artist """
    
    logging.info(" Obtaining discography list for " + artist_name)
    
    discography_list = []
    
    album_list = get_artist_album_list_json(artist_name)
    single_list = get_artist_singles_list_json(artist_name)
    
    discography_list = album_list + single_list
    
    return discography_list
    
    
def get_artist_album_list_json(artist_name):
    """ Return Spotipy list of album jsons from artist_name """
    
    album_list_json = []
    
    try:
        results = sp.artist_albums(artist_id_dictionary[artist_name], album_type='album')
    except:
        logging.error(" Bad request getting album list for " + artist_name)
        return None
    
    album_list_json.extend(results['items'])
    
    while results['next']:
        results = sp.next(results)
        album_list_json.extend(results['items'])
    
    return album_list_json


def get_artist_singles_list_json(artist_name):
    """ Return Spotipy list of single jsons from artist_name """
    
    single_list_json = []
    
    try:
        results = sp.artist_albums(artist_id_dictionary[artist_name], album_type='single')
    except:
        logging.error(" Bad request getting singles list for " + artist_name)
        return None
    
    single_list_json.extend(results['items'])
    
    while results['next']:
        results = sp.next(results)
        single_list_json.extend(results['items'])
        
    return single_list_json


def get_album_info_list(album_json):
    """ Return information about album """
    
    csv_data = []
    
    csv_data.append(album_json['id'])
    csv_data.append(album_json['name'])
    csv_data.append(album_json['artists'][0]['name'])
    csv_data.append(album_json['album_type'])
    csv_data.append(album_json['release_date'])
    
    tracks = get_album_tracks_json(album_json)
    track_string = ''
    if tracks is not None:
        for track in tracks:
            track_string += (track['name'].replace(',', '') + " | ")
        track_string = track_string[:-3]
    csv_data.append(track_string)
    
    return csv_data


def get_album_tracks_json(album_json):
    """ Return Spotipy track titles for album_name"""
    
    track_list_json = []
    
    try:
        results = sp.album_tracks(album_json['id'])
    except:
        logging.error(" Bad request getting tracks for " + album_json['name'] + " by " + album_json['artists'][0]['name'])
        return None
        
    track_list_json.extend(results['items'])
    
    while results['next']:
        results = sp.next(results)
        track_list_json.extend(results['items'])
        
    return track_list_json


def get_track_info_list(track_json, album_name):
    """ Return information about track """
    
    csv_data = []
    
    csv_data.append(track_json['id'])
    
    track_title = track_json['name']
    track_title_lower = track_title.lower()
    if (('remaster' in track_title_lower) or ('bonus track' in track_title_lower) or ('live' in track_title_lower)):
        index = track_title.rfind("-") - 1
        track_title_final = track_title[:index]
    else:
        track_title_final = track_title
    csv_data.append(track_title_final)
    
    csv_data.append(track_json['artists'][0]['name'])
    csv_data.append(album_name)           
    csv_data.append(track_json['disc_number'])
    csv_data.append(track_json['track_number'])
    csv_data.append(track_json['duration_ms'])
    csv_data.append(track_json['explicit'])
    
    lyric_api_path = get_track_api_path(track_title_final, track_json['artists'][0]['name'])
    if lyric_api_path is not None:
        lyrics = get_track_lyrics(lyric_api_path)
        csv_data.append(lyrics)
    else:
        csv_data.append("?")
    
    return csv_data


def get_track_api_path(track_title, artist_name):
    """ Return Genius track api path """
    
    track_title_formatted = track_title.replace(' ', '-')
    artist_name_formatted = artist_name.replace(' ', '-')
    formatted_search = track_title_formatted + '-' + artist_name_formatted
    
    request_url = 'http://api.genius.com/search/'
    params = {'q': formatted_search}
    
    try:
        r = requests.get(request_url, params=params, headers=genius_headers)
    except:
        logging.error(" Bad request to retrieve api_path for " + track_title + " by " + artist_name)
        return None
    
    json = r.json()
    results = json['response']['hits']
    
    if (len(results) > 0):
        first_result = results[0]
    else:
        logging.error(" No api_path found for " + track_title + " by " + artist_name)
        return None
    
    track_api_path = first_result['result']['api_path']
    
    return track_api_path
    

def get_track_lyrics(track_api_path):
    """ Return Genius lyrics from track api path """
    
    request_url = 'http://www.genius.com' + track_api_path
    
    try:
        r = requests.get(request_url)
    except:
        logging.error(" Bad request to retrieve lyrics for " + track_api_path)
        return "?"
        
    soup = bs4.BeautifulSoup(r.content, 'lxml')

    try:
        lyrics = soup.find('div', class_='lyrics').get_text()
    except:
        logging.error(" Unable to get lyrics for " + track_api_path)
        return "?"
    
    lyrics_stripped = lyrics.replace(',', '').replace('\n', '//')

    return lyrics_stripped


def diff(first, second):
    """ Return set difference """
    
    second = set(second)
    return [item for item in first if item not in second]
    
    
def import_list_from_csv(csv_list):
    """ Return artist list from a given csv file """
    
    imported_list = []
    
    with open(csv_list, 'r') as f:
        reader = csv.reader(f)
        imported_list = list(reader)
        
    return imported_list


def write_to_csv(file_name, headers, content):
    """ Write a list of information to a csv """
    
    logging.info(" Output to csv for " + file_name)
    
    date_time = str(datetime.date.today())
    date_time = date_time.replace(' ', '_').replace(':', '-')
    
    file_name = date_time + "_" + file_name + ".csv"
    
    with open(file_name, 'w', newline='', errors='ignore') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(content)


def generate_list_from_top_artists():
    """ Get top artists and generate csvs from them """

    terms = ["short_term", "medium_term", "long_term"]
    artist_csv = []
    album_csv = []
    track_csv = []

    for term in terms:
        logging.info(" Artists for term: " + term)
        logging.info(" " + str(get_top_artists(term, 5)))

    for artist in artist_id_dictionary.keys():
        
        artist_json = get_artist_json(artist)
        logging.info(" Processing ARTIST: " + artist_json['name'])
        artist_csv.append(get_artist_info_list(artist_json))
        
        album_json_list = get_artist_discography_list_json(artist_json['name'])
        
        for album in album_json_list:
            
            logging.info( " Processing DISC: " + album['name'] + "\t" + album['artists'][0]['name'])
            album_csv.append(get_album_info_list(album))
            track_json_list = get_album_tracks_json(album)
            
            if track_json_list is not None:
                
                for track in track_json_list:
                    if (track['id'] not in track_set):
                        logging.info(" Processing TRACK: " + track['name'] + "\t" + track['artists'][0]['name'])
                        track_set.add(track['id'])
                        track_csv.append(get_track_info_list(track, album['name']))
                    else:
                        pass
    
    write_to_csv("my_top_artists_artist_info", artist_headers, artist_csv)
    write_to_csv("my_top_artists_album_info", album_headers, album_csv)
    write_to_csv("my_top_artists_track_info", track_headers, track_csv)
    


request_url = 'http://api.genius.com/artists/1460/songs?sort=popularity&per_page=10'
    
try:
    r = requests.get(request_url, headers=genius_headers)
except:
    #logging.error(" Bad request to retrieve api_path for " + track_title + " by " + artist_name)
    print ("error")

json = r.json()
results = json['response']
track_csv = []
for song in results['songs']:
    api_path = song['api_path']
    track_csv.append([song['full_title'].replace(',', '').replace('\n', '//'), get_track_lyrics(api_path)])
    
write_to_csv("red_hot_chili_peppers_top_10_lyrics", ["FULL_TITLE","LYRIC"], track_csv)
    

#date_time = str(datetime.date.today())
#date_time = date_time.replace(' ', '_').replace(':', '-')
#sp = spotipy.Spotify(auth=library_read_token)
#artist_json = {'external_urls': {'spotify': 'https://open.spotify.com/artist/0L8ExT028jH3ddEcZwqJJ5'}, 'followers': {'href': None, 'total': 9884944}, 'genres': ['alternative rock', 'funk metal', 'permanent wave', 'post-grunge', 'rock'], 'href': 'https://api.spotify.com/v1/artists/0L8ExT028jH3ddEcZwqJJ5', 'id': '0L8ExT028jH3ddEcZwqJJ5', 'images': [{'height': 640, 'url': 'https://i.scdn.co/image/5b2072e522bf3324019a8c2dc3db20116dff0b87', 'width': 640}, {'height': 320, 'url': 'https://i.scdn.co/image/9527e700b5c80aa67350d5de0da10a0aa754fcb1', 'width': 320}, {'height': 160, 'url': 'https://i.scdn.co/image/a7af6412632c81ebfb5e39495aa3dacc564cb22b', 'width': 160}], 'name': 'Red Hot Chili Peppers', 'popularity': 85, 'type': 'artist', 'uri': 'spotify:artist:0L8ExT028jH3ddEcZwqJJ5'}

