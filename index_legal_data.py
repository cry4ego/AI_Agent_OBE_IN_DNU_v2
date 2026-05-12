"""
Index Legal Data – Nạp dữ liệu pháp luật vào Qdrant (sử dụng index_builder)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio
from rag.index_builder import initialize_legal_rag

async def main():
    success = await initialize_legal_rag()
    if success:
        print("✅ Index dữ liệu pháp luật thành công!")
    else:
        print("❌ Index dữ liệu pháp luật thất bại.")

if __name__ == "__main__":
    asyncio.run(main())
