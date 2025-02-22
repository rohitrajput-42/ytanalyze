from django.shortcuts import render
import requests
import yt_dlp
from yt_dlp import YoutubeDL
from django.conf import settings
from googleapiclient.discovery import build
import concurrent.futures

API_KEY = settings.YT_API_KEY
youtube = build("youtube", "v3", developerKey=API_KEY)

def home(request):
    return render(request, "index.html")

def monetize(request):
    context = {}
    
    channel_url = request.GET.get("url_capture")
    
    if channel_url:
        username = channel_url.split('@')[-1]
        response = youtube.search().list(part="snippet", q=username, type="channel", maxResults=1).execute()
        
        if not response.get("items"):
            return JsonResponse({"error": "Channel not found"})
        
        channel_info = response["items"][0]
        channel_id = channel_info["id"]["channelId"]
    
        avatar_url = channel_info["snippet"]["thumbnails"]["high"]["url"]

        response = youtube.search().list(part="id", channelId=channel_id, maxResults=10, order="date").execute()
        video_ids = [item["id"]["videoId"] for item in response.get("items", []) if item["id"]["kind"] == "youtube#video"]
        
        if not video_ids:
            return JsonResponse({"monetized": False})
        
        request = youtube.videos().list(part="snippet,contentDetails,status", id=",".join(video_ids))
        response = request.execute()
        
        monetized = any(
            video["contentDetails"].get("licensedContent", False) and not video["status"].get("madeForKids", False)
            for video in response.get("items", [])
        )

        context["avatar_url"] = avatar_url
        context["video_url"] = channel_url
        context["monetization_status"] = monetized

        return render(request, "monetize.html", context)
    else:
        return render(request, "monetize.html")

def channel_id(request):
    context = {}
    
    channel_url = request.GET.get("url_capture")
    
    if channel_url:
        options = {
            'quiet': True,
            'extract_flat': True,
            'playlistend': 1
        }
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            channel_id = info["channel_id"]

        avatar_url = info["thumbnails"][-1]["url"]

        context["channel_name"] = info["channel"]
        context["channel_avatar"] = avatar_url
        context["channel_url"] = channel_url
        context["channel_id"] = channel_id
        return render(request, "channel_id.html", context)
    else:
        return render(request, "channel_id.html")

def thumb_fetch(request):
    context = {}
    
    channel_url = request.GET.get("url_capture")
    
    if channel_url:
        options = {
            'quiet': True,
            'extract_flat': True,
            'cookies_from_browser': True,
            'playlistend': 1
        }
        
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(channel_url, download=False)

            thumbnails = info.get("thumbnails", [])
            unique_thumbnails = {thumbnail['url']: thumbnail for thumbnail in thumbnails}.values()
            thumbnails_data = []

            for thmb in unique_thumbnails:
                thmb_dict = {}
                if "resolution" in thmb and thmb["resolution"] in ["1920x1080", "686x386", "640x480"]:
                    thmb_dict["url"] = thmb["url"]
                    thmb_dict["width"] = thmb["width"]
                    thmb_dict["height"] = thmb["height"]

                    thumbnails_data.append(thmb_dict)    

            context["channel_name"] = info.get("channel")
            context["channel_avatar"] = thumbnails[-1]["url"] if thumbnails else None
            context["channel_url"] = channel_url
            context["channel_id"] = info.get("channel_id")
            context["thumbnails"] = thumbnails_data
        
        return render(request, "thumbnail.html", context)
    else:
        return render(request, "thumbnail.html")