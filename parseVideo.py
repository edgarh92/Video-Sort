
import os
import sys
import subprocess
import datetime
import argparse
import json


# ffprobe = os.path.join(os.path.dirname(sys.argv[0])  + '/ffprobe')
ffprobe = "/usr/local/bin/ffprobe"
def getVideoStreamDuration (videoObject):
    foundDuration = None
    streamDuration = None
    for i in range(len(videoObject)):
        
        if videoObject['streams'][i]["codec_type"] == "video":
            streamDuration = str(videoObject['streams'][i]["duration"])
            break
        elif videoObject['streams'][i]["codec_type"] == "audio":
            streamDuration = str(videoObject['streams'][i]["duration"])
            break
    formatedDuration =  datetime.datetime.strftime(datetime.datetime.strptime(streamDuration.strip(), "%H:%M:%S.%f"), "%H:%M:%S:%f")
    return formatedDuration

def getVideoAspectRatio (videoObject):
    for i in range(len(videoObject)):
        
        if videoObject['streams'][i]["codec_type"] == "video":
            videoWidth = int(videoObject['streams'][i]["width"])
            videoHeight = int(videoObject['streams'][i]["height"])
            videoAspectRatio = videoWidth/videoHeight
            break
    return videoAspectRatio

def sortByAspect (file ,videoAspectRatio):
    if videoAspectRatio == 0.5625:
        print( "Portrait")
    else:
        print("Landscape")

def sortByDuration(file,videoDuration):
    (h, m, s, ms) = videoDuration.split(':')
    print (h, m, s, ms)
    if int(s) < 10:
        print(s)
        print("Less than 10 seconds")
    else:
        print("Longer than 10 seconds")


def parseVideoData(videoFileList):
    for file in videoFileList:

        stdout, stderr=subprocess.Popen([ffprobe, "-sexagesimal", "-print_format", "json", "-show_entries", "stream=codec_type,codec_name,duration,sample_rate,bit_rate,width,height", file, "-sexagesimal"] , universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate() 
        videoMetaData = json.loads(stdout)
        videoDuration = getVideoStreamDuration(videoMetaData)
        videoAspectRatio = getVideoAspectRatio(videoMetaData)
        sortByDuration(file,videoDuration)
        sortByAspect(file,videoAspectRatio)
        





acceptedFormats = ('.avi', '.mp4', '.mp3', '.mxf', '.mov', '.wav', '.aif')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A program that generates metadata summaries and can extract audio from video files")
    parser.add_argument("-f", "--files", nargs="*", help="Indivudal files or directories to process")

    args = parser.parse_args()

    fileList = []
    for files in args.files:
        if os.path.isdir(files):
            directoryFiles = sorted(os.listdir(files))
            for file in directoryFiles:
                if file.endswith(acceptedFormats):
                    fileList.append(os.path.join(files, file))
        elif os.path.isfile(files):
            if files.endswith(acceptedFormats):
                fileList.append(os.path.abspath(files))

    sourceFiles = sorted(fileList)
    if not sourceFiles:
        print('No accepted files found. Drag files or folders or both.')
    else:
        videoAttributes = parseVideoData(sourceFiles)
