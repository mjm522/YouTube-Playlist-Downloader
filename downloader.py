import os
import sys
import math
import requests
import ffmpeg
from lxml import html
from pytube import YouTube
import concurrent.futures as cp
from functools import partial

temp_folder = './temp'

def file_path():
    home = os.path.expanduser('~')
    download_path = os.path.join(home, 'Downloads')
    return download_path

def create_temp_folder():
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

def get_max_resolution_stream(streams):
    available_video_resolutions = [int(stream.resolution[:-1]) for stream in streams if stream.resolution is not None]
    max_resolution = max(available_video_resolutions)
    v_stream = streams[available_video_resolutions.index(max_resolution)]
    a_stream = None
    if not v_stream.is_progressive:
        v_stream = streams.filter(res=str(max_resolution)+'p', mime_type='video/webm').first()
        available_audio_resolutions = [int(stream.abr[:-4]) for stream in streams if (stream.abr is not None) and (stream.type=='audio')]
        max_audio_rate = max(available_audio_resolutions)
        a_stream = streams.filter(abr=str(max_audio_rate)+'kbps', mime_type='audio/webm').first()
    return v_stream, a_stream

create_temp_folder()

class DownLoader():
    def __init__(self, yt_url, max_tries=5):
        self.url = yt_url
        self.filesize = None
        self.old_percent = 0
        self.max_tries = max_tries
        self.try_no = 0

    def progress_Check(self, stream=None, chunk=None, bytes_remaining=None):
        if self.filesize is None:
            return
        percent = (100*(self.filesize-bytes_remaining))/self.filesize
        if percent != self.old_percent:
            print("{:00.0f}% downloaded".format(percent) + '\r', sep='',
                  end='', file=sys.stdout , flush=False)
            self.old_percent = percent

    def download(self, download_path, idx=0):
        print ("Accessing YouTube URL...") 
        try:
            video = YouTube(self.url, on_progress_callback=self.progress_Check)
        except:
            print("ERROR. Check your:\n  -connection\n  -url is a YouTube url\n\nTry again.")
            self.try_no += 1
            if self.try_no <= self.max_tries:
                self.download(download_path)
            else:
                print(f'Unable to access {self.url} even after {self.max_tries}, quitting')
                return

        self.try_no = 0
        title = video.title
        v_stream, a_stream = get_max_resolution_stream(video.streams)
        self.filesize = v_stream.filesize
        print ("Fetching: {0}... filesize={1} MB".format(title, math.ceil(self.filesize*1e-6)))

        if a_stream is None:
            v_stream.download(download_path)
        else:
            v_name = 'video%d'%(idx)
            a_name = 'audio%d'%(idx)
            v_file = temp_folder+'/{}.webm'.format(v_name)
            a_file = temp_folder+'/{}.webm'.format(a_name)
            save_name = download_path + '/{}.mp4'.format(self.title)
            v_stream.download(temp_folder, v_name)
            a_stream.download(temp_folder, a_name)
            ffmpeg.concat(ffmpeg.input(v_file), ffmpeg.input(a_file),
                          v=1, a=1).output(save_name).run()
            os.remove(v_file)
            os.remove(a_file)

        
class PlaylistDownloader():
    def __init__(self, yt_url):
        r = requests.get(yt_url)
        webpage = html.fromstring(r.content) 
        page_urls = webpage.xpath('//a/@href')
        self.base_url = "https://www.youtube.com"
        self.url_lists = set([url for url in page_urls if url.startswith("/watch?v=") and "&index=" in url])
        print("Total videos to be downloaded", len(self.url_lists))

    def download(self, path):
        with cp.ProcessPoolExecutor() as executor:
            for idx, url in enumerate(self.url_lists):
                executor.submit(partial(DownLoader(self.base_url+url).download, path), idx)

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