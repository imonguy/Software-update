import httpx
import base64
import xml.etree.ElementTree as ET
import json
from datetime import datetime

# DANH SÁCH THEO DÕI: Bạn có thể thêm hàng trăm máy vào đây (Phone/Tablet)
DEVICES = [
    {"model": "SM-S928B", "csc": "XXV", "name": "S24 Ultra (VN)"},
    {"model": "SM-S928B", "csc": "EUX", "name": "S24 Ultra (Test EU)"},
    {"model": "SM-X910", "csc": "XXV", "name": "Tab S9 Ultra"},
    {"model": "SM-F946B", "csc": "XXV", "name": "Z Fold 5"},
    {"model": "SM-A556E", "csc": "XXV", "name": "Galaxy A55"},
]

def fus_decrypt(data):
    """Giải mã chuỗi Base64 từ Server FUS"""
    try:
        return base64.b64decode(data).decode('utf-8')
    except:
        return data

async def capture_fota(model, csc):
    url = "https://fota-cloud-dn.ospserver.net/firmware/FUS/check"
    # Header hiện đại, không dùng Kies
    headers = {
        "User-Agent": "FUS-4.0/Android", 
        "Content-Type": "application/xml"
    }
    
    # Bản tin XML FUS Request chuẩn cho One UI
    payload = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <FUSRequest>
        <Device>
            <Model>{model.upper()}</Model>
            <SalesCode>{csc.upper()}</SalesCode>
        </Device>
        <Protocol>3.0</Protocol>
    </FUSRequest>"""
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, content=payload, headers=headers, timeout=20.0)
            if r.status_code != 200: return "Server Error"
            
            # Giải mã nội dung
            xml_text = fus_decrypt(r.text)
            root = ET.fromstring(xml_text)
            
            # Bắt tag nội bộ (fw_version) hoặc tag công khai (latest)
            fw = root.find(".//fw_version")
            if fw is None: fw = root.find(".//latest")
            
            return fw.text if fw is not None else "Null (Hidden/No Update)"
        except Exception as e:
            return f"Error: {str(e)}"

async def main():
    results = []
    print(f"🚀 Bắt đầu quét {len(DEVICES)} thiết bị...")
    
    for d in DEVICES:
        version = await capture_fota(d['model'], d['csc'])
        results.append({
            "name": d['name'],
            "model": d['model'],
            "csc": d['csc'],
            "version": version,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        print(f"✅ {d['name']}: {version}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
