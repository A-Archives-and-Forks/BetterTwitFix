import base64
import os
import subprocess
import json
import sys
import tempfile

def extractStatus(url):
    return ""

def get_video_frame_rate(filename):
    result = subprocess.run(
        [
            "./ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            "-show_entries",
            "stream=r_frame_rate",
            filename,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    result_string = result.stdout.decode('utf-8').split()[0].split('/')
    fps = float(result_string[0])/float(result_string[1])
    return fps

def get_video_length_seconds(filename):
    result = subprocess.run(
        [
            "./ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    result_string = result.stdout.decode('utf-8').split()[0]
    return float(result_string)

def calcEdits(vlen,loopTimes):
    st="r"
    currTime=0.0
    for i in range(loopTimes):
        st+=f'e{str(currTime)}-9999,0'
        currTime+=vlen
    return st

def loop_video_until_length(filename, length):
    # use stream_loop to loop video until it's at least length seconds long
    video_length = get_video_length_seconds(filename)
    if video_length < length:
        loops = int(length/video_length)
        new_filename = tempfile.mkstemp(suffix=".mp4")[1]
        edits = calcEdits(video_length,loops)
        #out = subprocess.call(["ffmpeg","-stream_loop",str(loops),"-i",filename,"-c","copy","-y",new_filename],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        subprocess.run(["./mp4box", "-add",filename,"-edits",f'1={edits}',new_filename])
        return new_filename
    else:
        return filename



def lambda_handler(event, context):
    if ("queryStringParameters" not in event):
        return {
            "statusCode": 400,
            "body": "Invalid request."
        }
    
    url = event["queryStringParameters"].get("url","")

    # download video
    videoLocation = tempfile.mkstemp(suffix=".mp4")[1]
    subprocess.call(["wget","-O",videoLocation,url],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)

    videoLocationLooped = loop_video_until_length(videoLocation, 30)
    if videoLocationLooped != videoLocation:
        os.remove(videoLocation)
        videoLocation = videoLocationLooped

    with open(videoLocation, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('ascii')
    os.remove(videoLocation)
    return {
        'statusCode': 200,
        "headers": 
        {
            "Content-Type": "video/mp4"
        },
        'body': encoded_string,
        'isBase64Encoded': True
    }