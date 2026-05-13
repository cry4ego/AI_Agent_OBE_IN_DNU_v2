import os
os.environ["SERPER_API_KEY"] = "27665e5d42e73cf9a4f79d804b1a93c73c3cbdd9"
# ============================================================
# ⚠️ BẮT BUỘC ĐẶT Ở DÒNG ĐẦU TIÊN TRƯỚC KHI IMPORT THƯ VIỆN KHÁC
# ============================================================
HDD3_PATH = "/hdd3/vinhnv"
HF_CACHE = os.path.join(HDD3_PATH, "hf_cache_models")
TMP_CACHE = os.path.join(HDD3_PATH, "tmp_cache")

os.makedirs(HF_CACHE, exist_ok=True)
os.makedirs(TMP_CACHE, exist_ok=True)

# Ép hệ thống 100% phải dùng hdd3 ngay từ khi khởi động
os.environ["HF_HOME"] = HF_CACHE
os.environ["HUGGINGFACE_HUB_CACHE"] = HF_CACHE
os.environ["TMPDIR"] = TMP_CACHE
os.environ["TEMP"] = TMP_CACHE
os.environ["TMP"] = TMP_CACHE
# ============================================================

# BÂY GIỜ MỚI ĐƯỢC IMPORT CÁC THƯ VIỆN AI
import asyncio
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from run_multi_md_qa import chunk_all_md, build_index, ask_with_smart_router
from utils.local_llm import generate_response
from contextlib import asynccontextmanager

app_state = {"vs_map": {}}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Đang khởi động LexAI Engine tại AIOT-Lab...")
    base_dir = "data/TaiLieu_Chatbot"
    folders = ["HD_Laodong", "HD_Thuongmai", "Luat_DN", "CS_Hr", "Thue_Taichinh", "Tranhchap_xuli"]
    
    for folder in folders:
        path = os.path.join(base_dir, folder)
        if os.path.exists(path):
            print(f"📦 Đang nạp dữ liệu lĩnh vực: {folder}...")
            docs = chunk_all_md(path)
            if docs:
                app_state["vs_map"][folder] = build_index(docs)

    print("🔥 Đang mồi model Qwen-7B lên GPU (Tiến trình sẽ chạy hoàn toàn trên HDD3)...")
    try:
        generate_response([{"role": "user", "content": "hi"}], max_new_tokens=1)
        print("✅ Model Qwen & Knowledge Base đã SẴN SÀNG trên GPU!")
    except Exception as e:
        print(f"⚠️ Lỗi trong quá trình mồi model: {e}")

    yield
    app_state["vs_map"].clear()
    torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    field: str

@app.post("/ask")
async def chat_endpoint(req: ChatRequest):
    vs = app_state["vs_map"].get(req.field)
    if not vs:
        raise HTTPException(status_code=404, detail="Lĩnh vực này chưa có dữ liệu.")
    
    try:
        answer, sources, source_type = await ask_with_smart_router(req.prompt, vs)
        return {"answer": answer, "source_type": source_type, "status": "success"}
    except Exception as e:
        print(f"❌ Lỗi xử lý backend: {e}")
        return {"answer": "Hệ thống đang bận hoặc GPU quá tải.", "status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)