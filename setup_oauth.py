import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/api/download")
async def get_download_link_via_api(url: str, format: str = "mp4"):
    try:
        # ตัวอย่างการเรียกใช้ API สมมติ (คุณสามารถหา API ฟรีได้จากแพลตฟอร์มเช่น RapidAPI)
        api_endpoint = "https://example-video-downloader-api.com/extract"
        
        headers = {
            "Authorization": "Bearer YOUR_API_KEY",
            "Content-Type": "application/json"
        }
        
        payload = {
            "video_url": url,
            "format": format
        }

        # ส่งคำขอไปยังเซิร์ฟเวอร์ของผู้ให้บริการ
        response = requests.post(api_endpoint, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # ส่งลิงก์ดาวน์โหลดที่ได้จาก API กลับไปยังหน้าเว็บ (Frontend) ของเรา
            return {"status": "success", "title": data.get("title"), "download_url": data.get("direct_link")}
        else:
            raise Exception("API ภายนอกไม่สามารถดึงข้อมูลได้")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))