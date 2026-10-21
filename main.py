# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse # เพิ่มบรรทัดนี้
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

# --- 1. เพิ่ม Route สำหรับเสิร์ฟหน้าเว็บ UI ---
@app.get("/")
async def serve_frontend():
    # ตรวจสอบว่ามีไฟล์ index.html อยู่หรือไม่
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}

# --- 2. Route สำหรับ API ดาวน์โหลด (อันเดิมของคุณ) ---
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

        ydl_opts = {
            'format': format_query,
            'quiet': True,
            'noplaylist': True,
        }

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