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
        # --- 1. ปรับความยืดหยุ่นของการค้นหาไฟล์ (Format Query) ---
        if format.lower() == "mp3":
            format_query = 'bestaudio/best'
        else:
            if resolution == "original":
                # ขอไฟล์เดี่ยวที่มีทั้งภาพ+เสียง ที่เป็น mp4 ถ้าไม่มีให้เอาที่ดีที่สุดแทน
                format_query = 'best[ext=mp4]/best'
            else:
                # ขอความละเอียดตามที่กำหนด ถ้าไม่เป๊ะก็เอาที่ดีที่สุดที่สอดคล้อง
                format_query = f'best[height<={resolution}][ext=mp4]/best[height<={resolution}]/best'

        # กำหนดที่อยู่ไฟล์คุกกี้
        # กำหนดที่อยู่ไฟล์คุกกี้
        cookie_path = os.path.join(BASE_DIR, "cookies.txt")

        # ปรับ Format Query ให้ปลอดภัยสำหรับเซิร์ฟเวอร์ที่ไม่มีระบบรวมไฟล์ภาพ+เสียง (ffmpeg)
        if format.lower() == "mp3":
            format_query = 'bestaudio/best'
        else:
            # ดึงไฟล์วิดีโอเดี่ยวที่มีทั้งภาพและเสียงรวมกันแล้ว (Pre-merged) ที่ดีที่สุดตามความละเอียด
            if resolution == "original":
                format_query = 'best[ext=mp4]/best'
            else:
                format_query = f'best[height<={resolution}][ext=mp4]/best[ext=mp4]/best'

        # --- ท่าไม้ตายใหม่: สั่งให้สลับปลอมตัวเป็น TV, Android, iOS อัตโนมัติ ---
        ydl_opts = {
            'format': format_query,
            'quiet': True,
            'noplaylist': True,
            'extractor_args': {
                # ให้ yt-dlp ลองเจาะผ่าน Client หลายๆ แบบตามลำดับ
                'youtube': ['player_client=tv,ios,android,web']
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        }

        # ตรวจสอบและใช้งานไฟล์ Cookies
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
        else:
            print("WARNING: COOKIE FILE NOT FOUND AT", cookie_path) # พิมพ์แจ้งเตือนใน Log ของ Render

        # --- 3. ดึงข้อมูลและค้นหาลิงก์ตรงที่เล่นได้จริง ---
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            direct_url = info.get('url')
            
            # แผนสำรอง: หากไม่ได้ลิงก์ตรง ให้ค้นหาจากรายการ Format ทั้งหมด
            if not direct_url and 'formats' in info:
                for f in reversed(info['formats']):
                    # กรองเอาเฉพาะไฟล์ที่มีทั้งภาพ (vcodec) และเสียง (acodec) รวมอยู่ด้วยกัน
                    if f.get('url') and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        direct_url = f['url']
                        break
                
                # หากยังไม่เจออีก ให้เอาลิงก์แรกสุดที่ใช้งานได้
                if not direct_url:
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