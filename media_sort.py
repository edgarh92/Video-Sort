#!/usr/bin/env python
import datetime
from shutil import which, move
import os
import json
import subprocess
import mimetypes
import click
from pathlib import Path
from typing import Tuple


OUTPUT_DIRS = ["Landscape", "Portrait", "Image"]
ACCEPTED_FORMATS = ('.avi', '.mp4', '.mxf', '.mov', '.webm', '.m4v', '.h264', '.mkv', '.jpg', '.jpeg', '.png')


def process_object(video_object, attribute_requested: str):
    for stream in video_object['streams']:
        if stream['codec_type'] == "video":
            attribute = stream[attribute_requested]
            break
    return attribute


class MediaProcessor():
    def __init__(self, source_file: Path):
        self.media_file = source_file
        self.media_object = None

    def get_media_stream_duration(self) -> str:
        stream_duration = None
        stream_duration = process_object(self.media_object, 'duration')
        formated_duration = datetime.datetime.strftime(datetime.datetime.strptime(stream_duration.strip(), "%H:%M:%S.%f"), "%H:%M:%S:%f")
        return formated_duration

    def get_media_aspect_ratio(self) -> int:
        media_width = int(process_object(self.media_object, 'width'))
        media_height = int(process_object(self.media_object, 'height'))
        media_aspect_ratio = media_width / media_height
        return media_aspect_ratio

    def get_rotation(self) -> int:
        try:
            rotation = int(self.media_object['streams'][0]['side_data_list'][0]['rotation'])
            return rotation
        except KeyError:
            return None

    def parse_media_data(self) -> Tuple:
        '''Returns JSON of media attributes requested from ffprobe
            media_dict >> duration
            media_dict >> media_width
        '''

        attributes_request = "stream=codec_type,codec_name,duration,sample_rate,bit_rate,width,height"
        if which("ffprobe") is not None:
            stdout, stderr = subprocess.Popen(
                [
                    "ffprobe", "-sexagesimal", "-print_format", "json",
                    "-show_entries", attributes_request,
                    self.media_file, "-sexagesimal"],
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()
            self.media_object = json.loads(stdout)
            if self.media_object is not None:
                media_duration = self.get_media_stream_duration()
                media_aspect_ratio = self.get_media_aspect_ratio()
                if media_duration and media_aspect_ratio:
                    return media_duration, media_aspect_ratio
                else:
                    print("No attributes found")
                    return None
            else:
                print("No attributes found")
                return None
        else:
            print(f'Ffprobe not installed. Please install')

    def get_media_type(self) -> str:
        mime_type, _ = mimetypes.guess_type(str(self.media_file))
        if mime_type is None:
            return None
        return mime_type.split('/')[0]


def get_media_orientation(media_aspect_ratio) -> str:
    if media_aspect_ratio == 0.5625:
        return "Portrait"
    else:
        return "Landscape"


def media_length_is_valid(media_duration):
    '''Ignores movies shorter than 1 second. These should be ignored and sorted on their own.'''
    (h, m, s, ms) = media_duration.split(':')
    if int(s) > 1:
        return True
    else:
        print(f'Media is shorter than 1 second: {media_duration}. Skipped')
        return False


def sort_by_attributes(media_file, media_metadata):
    input_path = os.path.dirname(os.path.abspath(media_file))
    DIR_NAMES = ["Portrait", "Landscape", "Image"]
    OUTPUT_DIRS = []
    for output_dir in DIR_NAMES:
        output_path = os.path.join(input_path, output_dir)
        OUTPUT_DIRS.append(output_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

    media_duration, media_aspect_ratio = media_metadata

    media_type = MediaProcessor(media_file).get_media_type()
    if media_type == "video":
        orientation_type = get_media_orientation(media_aspect_ratio)
        if orientation_type == "Portrait":
            print("Moved to Portrait")
            move(media_file, OUTPUT_DIRS[0])
        elif orientation_type == "Landscape":
            print("Moved to Landscape")
            move(media_file, OUTPUT_DIRS[1])
        else:
            print("Error: Orientation Cannot be determined")
    elif media_type == "image":
        print("Moved to Image")
        move(media_file, OUTPUT_DIRS[2])
    else:
        print("Error: Media type cannot be determined")


def build_media_list(source_file) -> list:
    media_list = []
    for files in source_file:
        if os.path.isdir(files):
            directory_files = sorted(os.listdir(files))
            for file in directory_files:
                if file.lower().endswith(ACCEPTED_FORMATS):
                    media_list.append(os.path.join(files, file))
        if files.lower().endswith(ACCEPTED_FORMATS):
            media_list.append(os.path.abspath(files))

    return media_list


@click.command()
@click.option('-v', '--video', is_flag=True, help='Process only video files')
@click.option('-i', '--image', is_flag=True, help='Process only image files')
@click.argument('files', nargs=-1, type=click.Path(exists=True))
def main(video, image, files):
    sorted_media_file_list = sorted(build_media_list(files))
    if not sorted_media_file_list or len(sorted_media_file_list) == 0:
        print('No accepted files found. Drag files or folders or both.')
    else:
        for media_file in sorted_media_file_list:
            print(f'Processing: {media_file}')
            media_processor = MediaProcessor(media_file)
            media_metadata = media_processor.parse_media_data()
            media_type = media_processor.get_media_type()
            if (not video and not image) or (video and media_type == "video") or (image and media_type == "image"):
                sort_by_attributes(media_file, media_metadata)


if __name__ == "__main__":
    main()
