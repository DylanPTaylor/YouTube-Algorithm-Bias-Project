"""
Author: Dylan Taylor
UCID: 30078900
Date: 08/12/2021


Youtube API documentation: https://developers.google.com/youtube/v3/docs/?hl=en_US
I Created a google cloud project to store the API Key which is needed to authenticate with Youtubes DATA Api V3

need 3 libraries to run this: 
pip install requests
pip install --upgrade google-api-python-client
pip install --upgrade google-auth-oauthlib google-auth-httplib2 <- unsure if this is actually needed but kepy here incase everything blows up


must use "part" paramter in all get requests to the API
default of 10,000 quota, or requests, per day for api calls
our api calls should cost 1 each

NOTICE:
After enough GET requests to youtube.com (in my experience it was a few thousand), the function will begin to fail
as youtube begins to block the crawler. 
You can watch Youtube on your own without getting blocked even if the crawler is getting block,
however youtube probably notices the mass amounts of request form your IP and probably begins to inquire about you
"""

import requests
import json
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

HOME = "C:\\Users\\dylan\\OneDrive\\Desktop\\School\\Code\\Python\\572"
YOUTUBE_URI_BASE = 'https://youtube.com'
YOUTUBE_WATCH_ARG = '/watch?v='
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
KEY = "AIzaSyDqr_J5Aa8VXQdGRYCT2Kn6uRoCcKYoWMI"

# Get the genres names from youtube, give a set of IDS.
# Should only be ran at the beginning of the project as it stores everything
# it gets in a json


def get_genre_names(Ids):
    youtube = get_authenticated_service()

    # Get API data for this video
    request = youtube.videoCategories().list(
        part="snippet",
        id=Ids,
        key=KEY
    )

    response = request.execute()

    items = response["items"]

    genres = []
    for item in items:
        genreId = item["id"]
        title = item["snippet"]["title"]
        genre = {}
        genre["genreId"] = genreId
        genre["title"] = title
        genres.append(genre)

    with open(HOME+"\\VideoData\\genres.json", "r") as file:
        json_data = json.load(file)
        file.close()

    for genre in genres:
        if all((g["genreId"] != genre["genreId"]) for g in json_data):
            json_data.append(genre)

    with open(HOME+"\\VideoData\\genres.json", "w") as file:
        json.dump(json_data, file)


# Translate the integer representation of a give genre to its string value
def translate_genre_id_to_name(id):
    # Check if we have this genre
    with open(HOME+"\\VideoData\\genres.json", "r") as file:
        genres = json.load(file)
        file.close()

    for genre in genres:
        if id == genre["genreId"]:
            return genre["title"]

    # if not, get it and return it
    get_genre_names([id])
    return translate_genre_id_to_name(id)

# For authentication to the google platform, see the link in the header


def get_authenticated_service():
    return build(API_SERVICE_NAME, API_VERSION, developerKey=KEY)

# Look for content is the returned JSON object


def parse_content(dataset, content):
    for result in dataset:
        if 'name' in result.attrs.keys():
            if result.attrs['name'] == content:
                return result.attrs['content']
        elif 'itemprop' in result.attrs.keys():
            if result.attrs['itemprop'] == content:
                return result.attrs['content']

# Extract the Json object from the HTML


def get_yt_data(scripts):
    for script in scripts:
        if script.name == 'script' and isinstance(script.next, str) and script.next.startswith("var ytInitialData"):
            return script.next[script.next.find('{'):len(script.next)-1]

# Get watch ids of suggested video from the json object


def extract_ids(dataset):
    ids = []
    for item in dataset:
        if 'compactVideoRenderer' in item.keys():
            ids.append(item['compactVideoRenderer']['videoId'])
    return ids


# get a youtube videos HTML page given its watch ID
# And extract the needed data, which is then returned
def fetch_data(video):
    # Get the videos HTML page
    raw_html = requests.get(
        YOUTUBE_URI_BASE+YOUTUBE_WATCH_ARG+video)

    # Mmmmmmmm good soup
    parser = BeautifulSoup(raw_html.text, 'html.parser')
    formatted_html = list(parser.children)[1]

    # YouTube divides pages into 2 main sections
    meta_data = formatted_html.head.find_all_next("meta")
    scripts = formatted_html.body.contents

    # This was annoying to find -> see VideoData example_of_get_Req.json
    ytInitialData = get_yt_data(scripts)

    # Load the JSON object that has this videos data and its suggested videos
    json_data = json.loads(ytInitialData)

    try:
        suggested_videos = json_data['contents']['twoColumnWatchNextResults'][
            'secondaryResults']['secondaryResults']['results'][1:]
    except Exception:
        # Happens if YouTube is annoyed with the number of GET reqs.
        print("Didnt see any suggestions for "+video)
        return 0
    suggested_videos = extract_ids(suggested_videos)

    genre = parse_content(meta_data, 'genre')

    data = {"videoId": video, "genre": genre,
            "candidate videos": suggested_videos}

    return data
