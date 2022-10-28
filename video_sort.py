#!/usr/bin/env python
from ast import Pass
import os
from pathlib import Path
import subprocess
import datetime
import argparse
import json
from shutil import which, move


OUTPUT_DIRS = [ "Landscape", "Portrait"]
ACCEPTED_FORMATS = ('.avi', '.mp4', '.mxf', '.mov', '.webm', '.m4v', '.h264', '.mkv')


def process_object(video_object, attribute_requested: str):
    for stream in video_object['streams']:
        if stream['codec_type'] == "video":
            attribute = stream[attribute_requested]
            break
    return attribute


class VideoProcessor():
    def __init__(self, source_file: Path):
        self.video_file = source_file
        self.video_object = None

    def get_video_stream_duration(self) -> str:
        stream_duration = None
        stream_duration = process_object(self.video_object, 'duration')
        formated_duration =  datetime.datetime.strftime(datetime.datetime.strptime(stream_duration.strip(), "%H:%M:%S.%f"), "%H:%M:%S:%f")
        return formated_duration

    def get_video_aspect_ratio(self) -> int:

        video_width = int(process_object(self.video_object, 'width'))
        video_height = int(process_object(self.video_object, 'height'))
        
        video_aspect_ratio = video_width/video_height
        return video_aspect_ratio

    def get_rotation(self) -> int:
        try:
            rotation = int(self.video_object['streams'][0]
            ['side_data_list'][0]
            ['rotation'])
            return rotation
        except KeyError:
            return None

    def parse_video_data(self) -> (tuple):
        '''Returns JSON of video attributes requested from ffprobe
            video_dict >> duration
            video_dict >> video_width
        '''

        attributes_request = "stream=codec_type,codec_name,duration,sample_rate,bit_rate,width,height"
        if which("ffprobe") is not None:
            stdout, stderr = subprocess.Popen(
                [
                    "ffprobe", "-sexagesimal", "-print_format", "json",
                    "-show_entries", attributes_request,
                    self.video_file, "-sexagesimal"] , 
                    universal_newlines=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                    ).communicate() 
            self.video_object = json.loads(stdout)
            if self.video_object is not None:
                video_duration = self.get_video_stream_duration()
                videoAspectRatio = self.get_video_aspect_ratio()
                if video_duration and videoAspectRatio:
                    return video_duration,videoAspectRatio
                else:
                    print("No attributes found")
                    return None
            else:
                print("No attributes found")
                return None
        else:
            print(f'Ffprobe not installed. Please install')

def get_video_orientation(videoAspectRatio) -> str:
    if videoAspectRatio == 0.5625:
        return "Portrait"
    else:
        return "Landscape"

        
def video_length_is_valid(video_duration):
    '''Ignores movies shorter than 1 second. These should be ignored and sorted on their own.'''
    (h, m, s, ms) = video_duration.split(':')
    if int(s) > 1:
        return True
    else:
        print(f'Video is Shorter than 1 second:{video_duration}. Skipped')
        return False

def sort_by_attributes(video_file, video_metadata):
    input_path = os.path.dirname(os.path.abspath(video_file))
    DIR_NAMES = [ "Portrait", "Landscape"]
    OUTPUT_DIRS =[]
    for output_dir in DIR_NAMES:
        output_path = os.path.join(input_path, output_dir)
        OUTPUT_DIRS.append(output_path)
        if not os.path.exists(output_path):
                os.makedirs(output_path)
   
    video_duration, videoAspect = video_metadata

    if video_length_is_valid(video_duration):
        orientation_type = get_video_orientation(videoAspect)
        if orientation_type == "Portrait":
            print("Moved to Portrait")
            move(video_file, OUTPUT_DIRS[0])
        elif orientation_type == "Landscape":
            print("Moved to Landscape")
            move(video_file, OUTPUT_DIRS[1])
        else:
            print("Error: Orientation Cannot be determine")
    return Pass
        

def build_video_list(source_file) -> list:
    video_list = []
    for files in source_file:
        if os.path.isdir(files):
            directoryFiles = sorted(os.listdir(files))
            for file in directoryFiles:
                if file.lower().endswith(ACCEPTED_FORMATS):
                    video_list.append(os.path.join(files, file))
        if files.lower().endswith(ACCEPTED_FORMATS):
            video_list.append(os.path.abspath(files))

    return video_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A program that generates metadata summaries and can extract audio from video files")
    parser.add_argument(
        "-f",
        "--files",
        nargs="*",
        help="Indivudal files or directories to process")
    args = parser.parse_args()

    sorted_video_file_list = sorted(build_video_list(args.files))
    if not sorted_video_file_list or len(sorted_video_file_list) == 0:
        print('No accepted files found. Drag files or folders or both.')
    else:
        for video_file in sorted_video_file_list:
            print(f'Processing: {video_file}')
            videoObject = VideoProcessor(video_file)
            video_attributes = videoObject.parse_video_data()
            sort_by_attributes(video_file,video_attributes)
