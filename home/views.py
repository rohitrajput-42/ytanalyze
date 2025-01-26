from django.shortcuts import render
import requests
import yt_dlp
from yt_dlp import YoutubeDL

def home(request):
    return render(request, "index.html")

def get_top_videos_from_channel(channel_url, max_results=15):
    options = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': max_results,
        'no_cache_dir': True,
        'download': False

    }
    with YoutubeDL(options) as ydl:
        vid_info = ydl.extract_info(channel_url, download=False)
        vids_list = []

        if "entries" in vid_info and "ie_key" in vid_info["entries"][0]:
            for x in vid_info["entries"][:20]:vids_list.append({
                    'id': x['id'],
                    'views': x.get('view_count', 0)
                })
        else:
            for x in vid_info["entries"][0]["entries"][:20]:
                vids_list.append({
                    'id': x['id'],
                    'views': x.get('view_count', 0)
                })

        sorted_vids = sorted(vids_list, key=lambda v: v['views'], reverse=True)
        return sorted_vids[:max_results]

def monetize(request):
    context = {}
    
    channel_url = request.GET.get("url_capture")
    
    if channel_url:

        options = {
            'quiet': True,
            'extract_flat': True,
            'playlistend': 1,
            'no_cache_dir': True,
            'download': False

        }
        with YoutubeDL(options) as ydl:
            avatar_info = ydl.extract_info(channel_url, download=False)
        avatar_url = avatar_info["thumbnails"][-1]["url"]

        monetization_status = False
        top_videos = get_top_videos_from_channel(channel_url)
        result = []
        for video in top_videos:
            video_url = f"https://www.youtube.com/watch?v={video['id']}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(video_url, headers=headers)
            response.raise_for_status()

            if '{"key":"yt_ad","value":"1"}' in response.text:
                result.append("yes")
            else:
                result.append("no")

        if "yes" in result:
            monetization_status = True
        else:
            monetization_status = False

        context["avatar_url"] = avatar_url
        context["video_url"] = channel_url
        context["monetization_status"] = monetization_status

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