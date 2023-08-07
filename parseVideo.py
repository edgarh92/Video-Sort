import subprocess
import datetime
import json
import click
from pathlib import Path
import mimetypes
import shutil
from PIL import Image



ffprobe_path = shutil.which('ffprobe')
if ffprobe_path is None:
    raise Exception('ffprobe not found on the system')


def get_video_stream_duration(video_object):
    found_duration = None
    stream_duration = None
    for i in range(len(video_object)):

        if video_object['streams'][i]["codec_type"] == "video":
            stream_duration = str(video_object['streams'][i]["duration"])
            break
        elif video_object['streams'][i]["codec_type"] == "audio":
            stream_duration = str(video_object['streams'][i]["duration"])
            break
    formated_duration = datetime.datetime.strftime(datetime.datetime.strptime(stream_duration.strip(), "%H:%M:%S.%f"), "%H:%M:%S:%f")
    return formated_duration


def get_video_aspect_ratio(video_object):
    for i in range(len(video_object)):

        if video_object['streams'][i]["codec_type"] == "video":
            video_width = int(video_object['streams'][i]["width"])
            video_height = int(video_object['streams'][i]["height"])
            video_aspect_ratio = video_width / video_height
            break
    return video_aspect_ratio


def sort_by_aspect(file, video_aspect_ratio):
    if video_aspect_ratio == 0.5625:
        print("Portrait")
        metadata = 'orientation=portrait'
    else:
        print("Landscape")
        metadata = 'orientation=landscape'
    file_path = Path(file)
    output_file = Path('tagged_videos') / file_path.name
    try:
        subprocess.run(['ffmpeg', '-i', str(file_path),  '-update', '-metadata', metadata, '-codec', 'copy', '-y', str(output_file)], check=True)
        shutil.move(str(file_path), Path('processed_videos') / file_path.name)
    except subprocess.CalledProcessError as e:
        print(f"Error tagging {file_path}: {e}")
    except shutil.Error as e:
        print(f"Error moving {file_path}: {e}")

def sort_by_duration(file, video_duration):
    (h, m, s, ms) = video_duration.split(':')
    print(h, m, s, ms)
    if int(s) < 10:
        print(s)
        print("Less than 10 seconds")
    else:
        print("Longer than 10 seconds")


def parse_video_data(video_file_list):
    for file in video_file_list:
        stdout, _ = subprocess.Popen([ffprobe_path, "-sexagesimal", "-print_format", "json", "-show_entries", "stream=codec_type,codec_name,duration,sample_rate,bit_rate,width,height", file, "-sexagesimal"], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        video_meta_data = json.loads(stdout)
        video_duration = get_video_stream_duration(video_meta_data)
        video_aspect_ratio = get_video_aspect_ratio(video_meta_data)
        sort_by_duration(file, video_duration)
        sort_by_aspect(file, video_aspect_ratio)




def get_image_aspect_ratio(image_file):
    try:
        with Image.open(image_file) as img:
            width, height = img.size
            return width / height
    except (IOError, ValueError):
        return None


def sort_images_by_aspect_ratio(image_files):
    for image_file in image_files:
        aspect_ratio = get_image_aspect_ratio(image_file)
        if aspect_ratio is not None:
            sort_by_aspect(image_file, aspect_ratio)


@click.command()
@click.option('-v', '--videos', type=click.Path(exists=True), help='Path to video files')
@click.option('-i', '--images', type=click.Path(exists=True), help='Path to image files')
def main(videos, images):
    if videos:
            video_files = []
            for path in Path(videos).rglob('*'):
                if path.is_file() and mimetypes.guess_type(str(path))[0].startswith('video/'):
                    video_files.append(str(path))
            if not video_files:
                print('No accepted video files found.')
            else:
                parse_video_data(video_files)

    if images:
        image_files = []
        for path in Path(images).rglob('*'):
            mime_type = mimetypes.guess_type(str(path))[0]
            if mime_type is not None and mime_type.startswith('image/'):
                image_files.append(str(path))
        if not image_files:
            print('No accepted image files found.')
        else:
            sort_images_by_aspect_ratio(image_files)


if __name__ == "__main__":
    main()
