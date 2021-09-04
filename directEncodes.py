
import os
import sys
import subprocess
import datetime
import argparse
import json

ffprobe = os.path.join(os.path.dirname(sys.argv[0])  + '/ffprobe')
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

def generateTotalDuration(videoFileList):
    aggregatedVideoDurations = []
    for file in videoFileList:

        stdout, stderr=subprocess.Popen([ffprobe, "-sexagesimal", "-print_format", "json", "-show_entries", "stream=codec_type,codec_name,duration,sample_rate,bit_rate", file, "-sexagesimal"] , universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate() 
        videoMetaData = json.loads(stdout)
        videoDuration = getVideoStreamDuration(videoMetaData)
        aggregatedVideoDurations.append(videoDuration)


    sum = datetime.timedelta()
    for videoDuration in aggregatedVideoDurations:
        (h, m, s, ms) = videoDuration.split(':')

        durationTimeDelta = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s),microseconds=int(ms))
        sum += durationTimeDelta
    return datetime.datetime.strftime(datetime.datetime.strptime(str(sum),"%H:%M:%S.%f"), "%Hh:%Mm:%Ss")        


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
        totalDuration = generateTotalDuration(sourceFiles)
        print(totalDuration)
        