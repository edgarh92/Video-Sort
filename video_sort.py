#!/usr/bin/env python
from ast import Pass
import os
import subprocess
import datetime
import argparse
import json
from shutil import which, move
from platform import system


OUTPUT_DIRS = [ "Landscape", "Portrait"]

class VideoProcessor():
    def __init__(self, source_file):
        self.video_file = source_file
        self.video_object = None

    def getVideoStreamDuration (self) -> str:
        streamDuration = None
        for i in range(len(self.video_object)):
            
            if self.video_object['streams'][i]["codec_type"] == "video":
                streamDuration = str(self.video_object['streams'][i]["duration"])
                break
            elif self.video_object['streams'][i]["codec_type"] == "audio":
                streamDuration = str(self.video_object['streams'][i]["duration"])
                break
        formatedDuration =  datetime.datetime.strftime(datetime.datetime.strptime(streamDuration.strip(), "%H:%M:%S.%f"), "%H:%M:%S:%f")
        return formatedDuration

    def getVideoAspectRatio(self) -> int:

        for i in range(len(self.video_object)):
            
            if self.video_object['streams'][i]["codec_type"] == "video":
                videoWidth = int(self.video_object['streams'][i]["width"])
                videoHeight = int(self.video_object['streams'][i]["height"])
                videoAspectRatio = videoWidth/videoHeight
                break
        return videoAspectRatio

    def parseVideoData(self) -> (tuple):
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
                videoDuration = self.getVideoStreamDuration()
                videoAspectRatio = self.getVideoAspectRatio()
                if videoDuration and videoAspectRatio:
                    return videoDuration,videoAspectRatio
                else:
                    print("No attributes found")
                    return None
            else:
                print("No attributes found")
                return None
        else:
            print(f'Ffprobe not installed. Please install')

def getVideoOrientation (videoAspectRatio) -> str:
    if videoAspectRatio == 0.5625:
        return "Portrait"
    else:
        return "Landscape"

        
        
def videoLengthIsValid(videoDuration):
    '''Ignores movies shorter than 1 second. These should be ignored and sorted on their own.'''
    (h, m, s, ms) = videoDuration.split(':')
    if int(s) > 1:
        return True
    else:
        print(f'Video is Shorter than 1 second:{videoDuration}. Skipped')
        return False

def sortByAttributes(video_file,video_metadata):
    input_path = os.path.dirname(os.path.abspath(video_file))
    DIR_NAMES = [ "Portrait", "Landscape"]
    OUTPUT_DIRS =[]
    for output_dir in DIR_NAMES:
        output_path = os.path.join(input_path,output_dir)
        OUTPUT_DIRS.append(output_path)
        if not os.path.exists(output_path):
                os.makedirs(output_path)
                

    videoDuration, videoAspect = video_metadata

    if videoLengthIsValid(videoDuration):
        orientation_type = getVideoOrientation(videoAspect)
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
                if file.lower().endswith(acceptedFormats):
                    video_list.append(os.path.join(files, file))
        elif os.path.isfile(files):
            if files.lower().endswith(acceptedFormats):
                video_list.append(os.path.abspath(files))

    return video_list



acceptedFormats = ('.avi', '.mp4', '.mxf', '.mov', '.webm', '.m4v', '.h264', '.mkv')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A program that generates metadata summaries and can extract audio from video files")
    parser.add_argument("-f", "--files", nargs="*", help="Indivudal files or directories to process")
    args = parser.parse_args()

    sortedVideoFileList = sorted(build_video_list(args.files))
    if not sortedVideoFileList or len(sortedVideoFileList) == 0:
        print('No accepted files found. Drag files or folders or both.')
    else:
        for videoFile in sortedVideoFileList:
            print(f'Processing: {videoFile}')
            videoObject = VideoProcessor(videoFile)
            video_attributes = videoObject.parseVideoData()

            sortByAttributes(videoFile,video_attributes)
