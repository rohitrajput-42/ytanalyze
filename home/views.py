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
        if "/@" in channel_url:
            username = channel_url.split("/@")[-1]
            search_response = youtube.search().list(
                part="snippet",
                q=username,
                type="channel",
                maxResults=1
            ).execute()

            if not search_response.get("items"):
                return JsonResponse({"error": "Channel not found (handle issue)"})

            channel_id = search_response["items"][0]["id"]["channelId"]
        else:
            channel_id = channel_url.split("/")[-1]

        response = youtube.channels().list(
            part="snippet,statistics,contentDetails,status",
            id=channel_id
        ).execute()

        if "items" not in response or not response["items"]:
            return JsonResponse({"error": "Channel not found (invalid ID)"})

        channel = response["items"][0]
        
        channel_name = channel["snippet"]["title"]
        avatar_url = channel["snippet"]["thumbnails"]["high"]["url"]
        description = channel["snippet"]["description"]
        country = channel["snippet"].get("country", "Not Available")
        creation_date = channel["snippet"]["publishedAt"]
        subscribers = int(channel["statistics"].get("subscriberCount", 0))
        total_videos = int(channel["statistics"].get("videoCount", 0))
        total_views = int(channel["statistics"].get("viewCount", 0))

        avg_rpm = 3.00  
        estimated_earnings = round((total_views * avg_rpm) / 1000, 2)

        video_response = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=10,
            order="date"
        ).execute()

        video_ids = [item["id"]["videoId"] for item in video_response.get("items", []) if item["id"]["kind"] == "youtube#video"]
        
        monetized = False
        if video_ids:
            video_details = youtube.videos().list(
                part="contentDetails,status",
                id=",".join(video_ids)
            ).execute()

            monetized = any(
                video["contentDetails"].get("licensedContent", False) and 
                not video["status"].get("madeForKids", False)
                for video in video_details.get("items", [])
            )

        context.update({
            "channel_name": channel_name,
            "avatar_url": avatar_url,
            "description": description,
            "country": country,
            "creation_date": creation_date.split("T")[0],
            "subscribers": subscribers,
            "total_videos": total_videos,
            "total_views": total_views,
            "estimated_earnings": estimated_earnings,
            "monetization_status": monetized,
            "video_url": channel_url
        })

        return render(request, "monetize.html", context)

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