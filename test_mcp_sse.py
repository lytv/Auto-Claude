
import urllib.request
import json
import time

def test_mcp_call():
    print("--- Thử gọi add_episode trực tiếp (Python v2) ---")
    url = "http://localhost:8000/sse"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            message_url = None
            for line_bytes in response:
                if line_bytes:
                    line_str = line_bytes.decode('utf-8').strip()
                    if line_str.startswith("data: /messages/"):
                        message_url = f"http://localhost:8000{line_str.replace('data: ', '').strip()}"
                        print(f"Tìm thấy endpoint: {message_url}")
                        break
            
            if not message_url: return

            # Thử gọi tool add_episode
            print("Đang gửi yêu cầu tools/call (add_episode)...")
            payload = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "add_episode",
                    "arguments": {
                        "content": "Đây là một bài kiểm tra ghi nhớ từ Antigravity lúc " + str(time.time())
                    }
                }
            }).encode('utf-8')

            post_req = urllib.request.Request(message_url, data=payload, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(post_req, timeout=10)
            
            print("Đang chờ phản hồi...")
            for line_bytes in response:
                if line_bytes:
                    line_str = line_bytes.decode('utf-8').strip()
                    if line_str.startswith("data:"):
                        data_str = line_str.replace("data: ", "").strip()
                        print(f"Nhận được: {data_str}")
                        if '"id":2' in data_str:
                            if "error" in data_str:
                                print("Lỗi từ server khi gọi tool.")
                            else:
                                print("--- THÀNH CÔNG! Tool add_episode đã được gọi. ---")
                            return
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    test_mcp_call()
