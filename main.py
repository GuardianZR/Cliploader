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
        is_youtube = "youtube.com" in url.lower() or "youtu.be" in url.lower()
        direct_url = None
        title = "p3r_downloaded_media"

        # ==========================================
        # 1. ระบบจัดการ YouTube แบบปลอดภัย 100% (ไม่ใช้คุกกี้)
        # ==========================================
        if is_youtube:
            cobalt_apis = [
                "https://api.cobalt.tools/api/json",
                "https://co.wuk.sh/api/json",
                "https://cobalt.q0.wtf/api/json",
                "https://api.cobalt.bckdr.icu/api/json"
            ]
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            payload = {
                "url": url,
                "videoQuality": resolution if format != "mp3" else "max",
                "isAudioOnly": True if format == "mp3" else False
            }
            
            for api_url in cobalt_apis:
                try:
                    response = requests.post(api_url, json=payload, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        direct_url = data.get("url") or data.get("picker", [{}])[0].get("url")
                        if direct_url:
                            return {"status": "success", "title": "youtube_media", "download_url": direct_url}
                except Exception:
                    continue
            
            # หาก API ทั้ง 4 ตัวไม่สามารถใช้งานได้ จะส่ง Error กลับไปทันทีโดยไม่ใช้ yt-dlp
            raise Exception("API สำหรับ YouTube ขัดข้องทั้งหมด กรุณาลองใหม่ภายหลัง")

        # ==========================================
        # 2. ระบบ yt-dlp ดั้งเดิม (สำหรับ Facebook และอื่นๆ โดยไม่พึ่งคุกกี้)
        # ==========================================
        if format.lower() == "mp3":
            format_query = 'bestaudio/best'
        else:
            format_query = 'best'

        # ลบการเรียกหาและผูกไฟล์ cookies.txt ออกทั้งหมด
        ydl_opts = {
            'format': format_query,
            'quiet': True,
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        }

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