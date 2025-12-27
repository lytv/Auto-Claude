#!/bin/bash

echo "--- Bắt đầu kiểm tra Graphiti MCP qua SSE (Bash v2) ---"

# 1. Kết nối tới SSE và lấy endpoint (timeout sau 5 giây)
echo "Đang lấy endpoint từ SSE..."
ENDPOINT_FILE="endpoint_temp.txt"
timeout 5 curl -s -N http://localhost:8000/sse > "$ENDPOINT_FILE" 2>/dev/null

ENDPOINT_DATA=$(grep "event: endpoint" -A 1 "$ENDPOINT_FILE" | tail -n 1)

if [ -z "$ENDPOINT_DATA" ]; then
    echo "Lỗi: Không tìm thấy endpoint từ SSE stream."
    rm "$ENDPOINT_FILE"
    exit 1
fi

MESSAGES_PATH=$(echo $ENDPOINT_DATA | sed 's/data: //')
MESSAGES_URL="http://localhost:8000$MESSAGES_PATH"

echo "Tìm thấy endpoint: $MESSAGES_URL"

# 2. Gửi yêu cầu liệt kê công cụ (POST)
echo "Đang gửi yêu cầu tools/list..."
# Lưu ý: Kết quả có thể trả về trong Body của POST hoặc trong Stream SSE.
# Chúng ta sẽ thử lấy kết quả từ Body trước.
RESPONSE=$(curl -s -X POST "$MESSAGES_URL" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}')

echo "Phản hồi từ POST: $RESPONSE"

if [[ "$RESPONSE" == *"tools"* ]]; then
    echo "--- Thành công! Tìm thấy danh sách công cụ trong Body ---"
    echo $RESPONSE | python3 -m json.tool
else
    echo "Phản hồi không chứa 'tools'. Kiểm tra lại stream SSE để tìm kết quả..."
    # Đọc lại file endpoint_temp.txt xem có kết quả tools/list được gửi về sau đó không
    cat "$ENDPOINT_FILE"
fi

rm "$ENDPOINT_FILE"
