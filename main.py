from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
async def serve_frontend():
    html_path = os.path.join(BASE_DIR, "p3r_strict_ui_downloader.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "p3r_strict_ui_downloader.html not found"}

@app.get("/bgm.mp3")
async def serve_bgm():
    bgm_path = os.path.join(BASE_DIR, "bgm.mp3")
    if os.path.exists(bgm_path):
        return FileResponse(bgm_path)
    return {"error": "bgm.mp3 not found"}

@app.get("/api/download")
async def get_download_link(url: str, format: str = "mp4", resolution: str = "1080"):
    try:
        # ==========================================
        # 1. ระบบ Smart Routing สำหรับ YouTube
        # ==========================================
        is_youtube = "youtube.com" in url.lower() or "youtu.be" in url.lower()
        
        if is_youtube:
            # ใช้ Cobalt API ทะลวงบล็อก YouTube โดยไม่ต้องง้อ Cookies
            api_url = "https://api.cobalt.tools/api/json"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            payload = {
                "url": url,
                "vQuality": resolution if format != "mp3" else "max",
                "isAudioOnly": True if format == "mp3" else False
            }
            
            try:
                response = requests.post(api_url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    direct_url = data.get("url") or data.get("picker", [{}])[0].get("url")
                    if direct_url:
                        return {"status": "success", "title": "youtube_media", "download_url": direct_url}
            except Exception as e:
                print("Cobalt API Error, falling back to yt-dlp:", e)
                # หาก API ล่ม โค้ดจะไหลลงไปใช้ yt-dlp ด้านล่างเป็นแผนสำรอง

       # ==========================================
        # 2. ระบบดั้งเดิม (yt-dlp) สำหรับ Facebook และอื่นๆ (รวมถึง YouTube สำรอง)
        # ==========================================
        if format.lower() == "mp3":
            format_query = 'bestaudio/best'
        else:
            format_query = 'best'

        ydl_opts = {
            'format': format_query,
            'quiet': True,
            'noplaylist': True,
            # แก้ไขบรรทัดนี้: ลบคำว่า 'web' ออก เพื่อป้องกันไม่ให้ YouTube ส่ง JavaScript Challenge มา
            'extractor_args': {
                'youtube': ['player_client=android,ios'] 
            },
            # ปรับ User-Agent ให้เหมือนมือถือ Android จริงๆ เพื่อความแนบเนียน
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            }
        }

        cookie_path = os.path.join(BASE_DIR, "cookies.txt")
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        cookie_path = os.path.join(BASE_DIR, "cookies.txt")
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            direct_url = info.get('url')
            
            if not direct_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url'):
                        direct_url = f['url']
                        break

            title = info.get('title', 'p3r_downloaded_media')
            
            if not direct_url:
                raise Exception("ไม่สามารถดึงลิงก์วิดีโอจาก URL นี้ได้")

            return {
                "status": "success", 
                "title": title, 
                "download_url": direct_url
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))