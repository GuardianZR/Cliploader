from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ประกาศที่อยู่ของโฟลเดอร์ปัจจุบัน
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. ส่งหน้าเว็บ (index.html)
@app.get("/")
async def serve_frontend():
    html_path = os.path.join(BASE_DIR, "p3r_strict_ui_downloader.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}

# 2. ส่งไฟล์เพลง (bgm.mp3) *นี่คือส่วนที่เพิ่มเข้ามาแก้ปัญหาเพลงไม่ดัง*
@app.get("/bgm.mp3")
async def serve_bgm():
    bgm_path = os.path.join(BASE_DIR, "bgm.mp3")
    if os.path.exists(bgm_path):
        return FileResponse(bgm_path)
    return {"error": "bgm.mp3 not found"}

# 3. API สำหรับดาวน์โหลด
@app.get("/api/download")
async def get_download_link(url: str, format: str = "mp4", resolution: str = "1080"):
    try:
        if format.lower() == "mp3":
            format_query = 'bestaudio/best'
        else:
            if resolution == "original":
                format_query = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                format_query = f'bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best'

        # กำหนดพาธของไฟล์คุกกี้
        cookie_path = os.path.join(BASE_DIR, "cookies.txt")

        # ตั้งค่าตัวเลือกสำหรับ yt-dlp
        ydl_opts = {
            'format': format_query,
            'quiet': True,
            'noplaylist': True,
            # เพิ่มการตั้งค่าเพื่อหลอกระบบว่าเป็นแอปบนอุปกรณ์พกพาหรือทีวี
            'extractor_args': {
                'youtube': ['client=android,ios,tv']
            }
        }

        # ตรวจสอบว่าอัปโหลดไฟล์คุกกี้มาแล้วหรือไม่ ถ้ามีให้ใช้งานด้วย
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

            title = info.get('title', 'video_download')
            if not direct_url:
                raise Exception("ไม่สามารถดึงลิงก์ดาวน์โหลดจาก URL นี้ได้")

            return {"status": "success", "title": title, "download_url": direct_url}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))