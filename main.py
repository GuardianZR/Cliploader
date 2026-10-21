from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import os

app = FastAPI()

# ตั้งค่า CORS อนุญาตให้หน้าเว็บเรียกใช้งาน API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. เสิร์ฟหน้าเว็บหลัก
@app.get("/")
async def serve_frontend():
    html_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}

# 2. เสิร์ฟไฟล์เพลงประกอบ
@app.get("/bgm.mp3")
async def serve_bgm():
    bgm_path = os.path.join(BASE_DIR, "bgm.mp3")
    if os.path.exists(bgm_path):
        return FileResponse(bgm_path)
    return {"error": "bgm.mp3 not found"}

# 3. API สกัดลิงก์วิดีโอ (ใช้ yt-dlp ดึงลิงก์ตรง)
@app.get("/api/download")
async def get_download_link(url: str, format: str = "mp4", resolution: str = "1080"):
    try:
        # เลือกรูปแบบไฟล์ที่ยืดหยุ่นที่สุดเพื่อรองรับทุกแพลตฟอร์ม
        if format.lower() == "mp3":
            format_query = 'bestaudio/best'
        else:
            format_query = 'best[ext=mp4]/best'

        ydl_opts = {
            'format': format_query,
            'quiet': True,
            'noplaylist': True,
            'extractor_args': {
                'youtube': ['player_client=android,ios,tv,web']
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        # อ่านไฟล์คุกกี้หากมีอยู่ในระบบ
        cookie_path = os.path.join(BASE_DIR, "cookies.txt")
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # ดึง URL ตรงจากวิดีโอ
            direct_url = info.get('url')
            
            # หากไม่มี URL ตรง ให้ค้นหาจากรายการ formats ทั้งหมด
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