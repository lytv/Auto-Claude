
import asyncio
import os
import sys
from pathlib import Path

# Thêm thư mục hiện tại vào path để import các module của dự án
sys.path.append("/Users/mac/tools/Auto-Claude")
sys.path.append("/Users/mac/tools/Auto-Claude/auto-claude")

async def test_write():
    print("--- Khởi tạo kiểm tra ghi Graphiti ---")
    
    # Thiết lập biến môi trường giả lập (vì .env bị chặn)
    os.environ["GRAPHITI_ENABLED"] = "true"
    os.environ["GRAPHITI_FALKORDB_HOST"] = "localhost"
    os.environ["GRAPHITI_FALKORDB_PORT"] = "6380"
    os.environ["GRAPHITI_DATABASE"] = "test_memory"
    
    # Cần API key nếu dùng OpenAI, nếu không có sẽ lỗi ở tầng LLM
    # Chúng ta chỉ muốn test kết nối DB trước
    
    from integrations.graphiti.queries_pkg.graphiti import GraphitiMemory
    from integrations.graphiti.queries_pkg.schema import GroupIdMode
    
    spec_dir = Path("/Users/mac/tools/Auto-Claude/guides")
    project_dir = Path("/Users/mac/tools/Auto-Claude")
    
    memory = GraphitiMemory(spec_dir, project_dir, GroupIdMode.SPEC)
    
    print(f"Trạng thái enabled: {memory.is_enabled}")
    
    try:
        initialized = await memory.initialize()
        print(f"Khởi tạo thành công: {initialized}")
        
        if initialized:
            print("Đang thử lưu một insight mẫu...")
            # Thử lưu một insight đơn giản
            res = await memory.save_gotcha("Đây là một test gotcha từ script kiểm tra.")
            print(f"Kết quả lưu: {res}")
            
            await memory.close()
            return res
    except Exception as e:
        print(f"Lỗi khi chạy test: {e}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_write())
