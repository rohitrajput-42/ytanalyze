from django.shortcuts import render, redirect
import requests
import yt_dlp
from yt_dlp import YoutubeDL
from django.conf import settings
from googleapiclient.discovery import build
import concurrent.futures
from urllib.parse import urlparse, parse_qs
import requests
import re
import json
import html
from django.core.mail import send_mail

API_KEY = settings.YT_API_KEY
youtube = build("youtube", "v3", developerKey=API_KEY)

def home(request):
    return render(request, "index.html")

def monetize(request):
    context = {}

    channel_url = request.GET.get("url_capture")

    if channel_url:
        # --- Case 1: Video URL ---
        if "watch?v=" in channel_url:
            parsed_url = urlparse(channel_url)
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get("v", [None])[0]

            if video_id:
                video_details = youtube.videos().list(
                    part="snippet,contentDetails,status,statistics",
                    id=video_id
                ).execute()

                if not video_details["items"]:
                    context["error"] = "Invalid video URL"
                    return render(request, "monetize.html", context)

                video = video_details["items"][0]
                snippet = video["snippet"]
                status = video["status"]
                content_details = video["contentDetails"]
                statistics = video["statistics"]
                channel_id = snippet["channelId"]

                # Optional: fetch channel data for avatar, country, subscriber count
                channel_response = youtube.channels().list(
                    part="snippet,statistics",
                    id=channel_id
                ).execute()
                channel = channel_response["items"][0]
                avatar_url = channel["snippet"]["thumbnails"]["high"]["url"]
                subscribers = int(channel["statistics"].get("subscriberCount", 0))
                country = channel["snippet"].get("country", "Not Available")

                monetized = (
                    content_details.get("licensedContent", False) and
                    not status.get("madeForKids", False) and
                    status.get("uploadStatus") == "processed"
                )

                context.update({
                    "channel_name": snippet["channelTitle"],
                    "avatar_url": avatar_url,
                    "description": snippet.get("description", ""),
                    "country": country,
                    "creation_date": snippet["publishedAt"].split("T")[0],
                    "subscribers": subscribers,
                    "total_videos": "N/A",
                    "total_views": statistics.get("viewCount", 0),
                    "estimated_earnings": round(int(statistics.get("viewCount", 0)) * 3.00 / 1000, 2),
                    "monetization_status": monetized,
                    "video_url": f"https://www.youtube.com/watch?v={video_id}"
                })

                return render(request, "monetize.html", context)

        # --- Case 2: Channel URL ---
        if "/@" in channel_url:
            username = channel_url.split("/@")[-1]
            search_response = youtube.search().list(
                part="snippet",
                q=username,
                type="channel",
                maxResults=1
            ).execute()

            if not search_response["items"]:
                context["error"] = "Channel not found"
                return render(request, "monetize.html", context)

            channel_id = search_response["items"][0]["id"]["channelId"]
        else:
            channel_id = channel_url.split("/")[-1]

        response = youtube.channels().list(
            part="snippet,statistics,contentDetails,status",
            id=channel_id
        ).execute()

        if not response["items"]:
            context["error"] = "Channel not found"
            return render(request, "monetize.html", context)

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
        
        channel_handle = channel_url.split("@")[1]
        mod_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&forHandle={channel_handle}&key={API_KEY}"

        response = requests.get(mod_url)
        info = response.json()

        context["channel_name"] = info["items"][0]["snippet"]["title"]
        context["channel_avatar"] = info["items"][0]["snippet"]["thumbnails"]["high"]["url"]
        context["channel_url"] = channel_url
        context["channel_id"] = info["items"][0]["id"]
        return render(request, "channel_id.html", context)
    else:
        return render(request, "channel_id.html")

def thumb_fetch(request):
    context = {}
    
    channel_url = request.GET.get("url_capture")
    
    if channel_url:
        
        video_id = channel_url.split("=")[1]
        mod_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet&key={API_KEY}"

        response = requests.get(mod_url)
        data = response.json()

        thumbnails = data["items"][0]["snippet"]["thumbnails"]
        selected_keys = ["high", "standard", "maxres"]        
        thumbnails_data = [{"url": thumbnails[key]["url"], "width": thumbnails[key]["width"], "height": thumbnails[key]["height"]} for key in selected_keys if key in thumbnails]
        
        context["channel_url"] = channel_url
        context["thumbnails"] = thumbnails_data
        
        return render(request, "thumbnail.html", context)
    else:
        return render(request, "thumbnail.html")
    
def tag_extractor(request):
    context = {}
    channel_url = request.GET.get("url_capture")

    if channel_url:
        video_id = channel_url.split("=")[1]
        mod_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={API_KEY}"
        response = requests.get(mod_url)
        data = response.json()

        context["channel_name"] = data["items"][0]["snippet"]["channelTitle"]
        context["video_name"] = data["items"][0]["snippet"]["title"]
        context["video_description"] = data["items"][0]["snippet"]["description"]
        context["channel_id"] = data["items"][0]["snippet"]["channelId"]
        context["channel_url"] = channel_url

        try:
            context["view_count"] = data["items"][0]["statistics"]["viewCount"]
        except:
            context["view_count"] = "N/A"
        
        try:
            context["like_count"] = data["items"][0]["statistics"]["likeCount"]
        except:
            context["like_count"] = "N/A"

        try:
            context["comment_count"] = data["items"][0]["statistics"]["commentCount"]
        except:
            context["comment_count"] = "N/A"
            
        try:
            context["fav_count"] = data["items"][0]["statistics"]["favoriteCount"]
        except:
            context["fav_count"] = "N/A"

        try:
            context["audio_language"] = data["items"][0]["snippet"]["defaultAudioLanguage"]
        except:
            context["audio_language"] = "N/A"
        
        try:
            context["tags"] = data["items"][0]["snippet"]["tags"]
        except:
            context["tags"] = "knull"

        return render(request, "tags_extractor.html", context)
    else:
        return render(request, "tags_extractor.html")
    
def aboutus(request):
    return render(request, "aboutus.html")

def contact_us(request):
    if request.method == 'POST':
        first = request.POST.get('first_name')
        try:
            last = request.POST.get('last_name')
        except:
            last = ""
        email = request.POST.get('email')
        try:
            phone = request.POST.get('phone')
        except:
            phone = ""
        message = request.POST.get('message')

        full_message = f"""
        Name: {first} {last}
        Email: {email}
        Phone: {phone}
        Message: VIA YT-Analyze .....
        {message}
        """

        send_mail(
            subject=f"Contact Form Submission from {first} {last}",
            message=full_message,
            from_email="rohit1471997@gmail.com",
            recipient_list=['rohit1471997@gmail.com'],
        )

        return redirect('/contact_us?success=1')

    mail_status = "pass" if request.GET.get('success') == '1' else None
    return render(request, 'contact_us.html', {"mail_status": mail_status})

def disclaimer(request):
    return render(request, "disclaimer.html")

def privacy(request):
    return render(request, "privacy.html")

def tnc(request):
    return render(request, "tnc.html")


def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

def transcript(request):
    context = {}
    channel_url = request.GET.get("url_capture")

    if channel_url:
        video_id = extract_video_id(channel_url)
        if video_id:

            url = "https://youtube-transcript3.p.rapidapi.com/api/transcript"
            querystring = {"videoId":{video_id}}
            headers = {
                "x-rapidapi-key": "d238aa1b7dmshf04380b819eb24bp17919cjsn47899c5a4c0b",
                "x-rapidapi-host": "youtube-transcript3.p.rapidapi.com"
            }
            response = requests.get(url, headers=headers, params=querystring)
            result = response.json()

            capt_list = []
            for capt in result.get("transcript", []):
                try:
                    text = capt["text"]
                    # Decode HTML entities here
                    decoded_text = html.unescape(text)
                    capt_list.append(decoded_text)
                except Exception:
                    pass

            if result["success"] == True:
                context["transcript"] = capt_list
                context["transcript_status"] = "ok"
            else:
                context["transcript"] = "Transcript not available !"
                context["transcript_status"] = "knull"
            context["channel_url"] = channel_url

    return render(request, "transcript.html", context)


def test_404(request):
    return render(request, '404.html', status=404)

def test_500(request):
    return render(request, "500.html", status=500)