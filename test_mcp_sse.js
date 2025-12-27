
const EventSource = require('eventsource');
const axios = require('axios');

async function testMCP() {
    console.log('--- Đang kết nối tới Graphiti MCP SSE ---');
    const es = new EventSource('http://localhost:8000/sse');
    
    let messageEndpoint = '';
    
    es.addEventListener('endpoint', async (event) => {
        messageEndpoint = 'http://localhost:8000' + event.data;
        console.log('Nhận được endpoint tin nhắn:', messageEndpoint);
        
        try {
            console.log('Đang gửi yêu cầu listing tools...');
            const response = await axios.post(messageEndpoint, {
                jsonrpc: '2.0',
                id: 1,
                method: 'tools/list'
            });
            console.log('Yêu cầu POST thành công (HTTP 202/Accepted)');
        } catch (error) {
            console.error('Lỗi khi gửi POST:', error.message);
        }
    });

    es.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.result && data.result.tools) {
                console.log('--- Danh sách công cụ tìm thấy: ---');
                data.result.tools.forEach(tool => {
                    console.log(` - ${tool.name}: ${tool.description}`);
                });
                es.close();
                process.exit(0);
            } else {
                console.log('Nhận được dữ liệu SSE:', event.data);
            }
        } catch (e) {
            console.log('Nhận được dữ liệu thô:', event.data);
        }
    };

    es.onerror = (err) => {
        console.error('Lỗi SSE:', err);
        es.close();
        process.exit(1);
    };

    // Timeout sau 15 giây
    setTimeout(() => {
        console.log('Hết thời gian chờ phản hồi tools/list');
        es.close();
        process.exit(1);
    }, 15000);
}

testMCP();
