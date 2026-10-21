from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

# 1. ส่งหน้าเว็บ (index.html)
@app.get("/")
async def serve_frontend():
    html_path = os.path.join(BASE_DIR, "p3r_strict_ui_downloader.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}

# 2. ส่งไฟล์เพลง (bgm.mp3)
@app.get("/bgm.mp3")
async def serve_bgm():
    bgm_path = os.path.join(BASE_DIR, "bgm.mp3")
    if os.path.exists(bgm_path):
        return FileResponse(bgm_path)
    return {"error": "bgm.mp3 not found"}

# 3. API สำหรับดาวน์โหลดโดยใช้ 3rd Party API ภายนอก
@app.get("/api/download")
async def get_download_link(url: str, format: str = "mp4", resolution: str = "1080"):
    try:
        # ตัวอย่างการใช้งาน Public API / หรือเปลี่ยนเป็น Endpoint ของผู้ให้บริการที่คุณเลือก
        # (ตัวอย่างนี้จำลองโครงสร้างการส่ง Request ไปยัง Service ภายนอก)
        api_url = "https://api.cobalt.tools/api/json" # ตัวอย่างการเรียกใช้ Cobalt API แบบสาธารณะ
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "vQuality": resolution if format != "mp3" else "max",
            "isAudioOnly": True if format == "mp3" else False
        }

        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("url") or data.get("picker", [{}])[0].get("url")
            
            if not download_url:
                raise Exception("ไม่สามารถดึงลิงก์ดาวน์โหลดจากระบบภายนอกได้")
                
            return {
                "status": "success", 
                "title": "p3r_downloaded_media", 
                "download_url": download_url
            }
        else:
            raise Exception("3rd Party API ขัดข้องหรือปฏิเสธคำขอ")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))