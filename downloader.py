import os
import sys
import math
import requests
from lxml import html
from pytube import YouTube

def file_path():
    home = os.path.expanduser('~')
    download_path = os.path.join(home, 'Downloads')
    return download_path

class DownLoader():
    def __init__(self, yt_url):
        self.url = yt_url
        self.filesize = None
        self.old_percent = 0

    def progress_Check(self, stream = None, chunk = None, bytes_remaining = None):
        if self.filesize is None:
            return
        percent = (100*(self.filesize-bytes_remaining))/self.filesize
        if percent != self.old_percent:
            print("{:00.0f}% downloaded".format(percent) + '\r', sep='', end ='', file = sys.stdout , flush = False)
            self.old_percent = percent

    def get_max_resolution_stream(self, streams):
        available_resolutions = [int(stream.resolution[:-1]) for stream in streams if stream.resolution is not None]
        return streams[available_resolutions.index(max(available_resolutions))]
     
    def download(self, download_path):
        print ("Accessing YouTube URL...") 
        try:
            video = YouTube(self.url, on_progress_callback=self.progress_Check)
        except:
            print("ERROR. Check your:\n  -connection\n  -url is a YouTube url\n\nTry again.")
            redo = self.start()

        video_type = self.get_max_resolution_stream(video.streams)
        title = video.title
        self.filesize = video_type.filesize
        print ("Fetching: {0}... filesize={1} MB".format(title, math.ceil(self.filesize*1e-6)))
        video_type.download(download_path)
 
 
class PlaylistDownloader():
    def __init__(self, yt_url):
        r = requests.get(yt_url)
        webpage = html.fromstring(r.content) 
        page_urls = webpage.xpath('//a/@href')
        self.base_url = "https://www.youtube.com"
        self.url_lists = [url for url in page_urls if url.startswith("/watch?v=") and "&index=" in url]

    def download(self, path):
        for url in self.url_lists:
            DownLoader(self.base_url+url).download(path)

def main():
    download_path=file_path()
    print("Your video will be saved to: {}".format(download_path))
    print("To change (y/n)")
    choice = input("Choice: ")
    if choice == 'y':
        download_path=input("Enter new path....:")

    print("Choose option \n 1) Playlist \n 2) Single Video")
    choice = input("Option 1/2 ...")
    if choice == '1':
        yt_url = input("Copy and paste your YouTube Playlist URL here: ")
        PlaylistDownloader(yt_url).download(download_path)
    elif choice == '2':
        yt_url = input("Copy and paste your YouTube URL here: ")
        DownLoader(yt_url).download(download_path)
    else:
        print("incorrect choice...")

if __name__ == '__main__':
    main()