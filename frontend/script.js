// ============================================================
// 🧠 LEXAI CORE ENGINE - JAVASCRIPT
// ============================================================

// 1. Cấu hình địa chỉ API Backend
// Lưu ý: Vì Vinh đang dùng Port Forwarding trên VS Code, chúng ta dùng localhost:8000
const API_BASE_URL = "http://localhost:8000";

// Trạng thái lĩnh vực mặc định khi vừa mở web
let currentField = "HD_Laodong";

/**
 * Hàm 1: Xử lý khi người dùng click chọn lĩnh vực pháp lý ở Sidebar
 */
function selectField(fieldName, element) {
    currentField = fieldName;

    // Xóa trạng thái 'active' (đổi màu) của tất cả các nút
    document.querySelectorAll('.field-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Thêm trạng thái 'active' cho nút vừa được click
    element.classList.add('active');

    // Thông báo cho người dùng biết hệ thống đã chuyển dữ liệu
    const fieldTextName = element.innerText.trim();
    appendMessage("bot", `🔄 Đã chuyển cơ sở dữ liệu sang: <b>${fieldTextName}</b>. Bạn có câu hỏi nào không?`);
}

/**
 * Hàm 2: Xử lý gửi câu hỏi tới Backend (Quan trọng nhất)
 */
async function ask() {
    const inputField = document.getElementById('user-query');
    const query = inputField.value.trim();

    // Nếu ô nhập rỗng thì không làm gì cả
    if (!query) return;

    // Hiển thị câu hỏi của người dùng lên màn hình
    appendMessage("user", query);
    
    // Xóa trắng ô nhập liệu sau khi gửi để người dùng có thể gõ câu tiếp theo
    inputField.value = "";

    // Tạo ID ngẫu nhiên cho dòng trạng thái "đang suy nghĩ"
    const typingId = "typing-" + Date.now();
    
    // Hiển thị trạng thái AI đang xử lý
    appendMessage("bot", `<i>LexAI đang đọc tài liệu và phân tích...</i>`, typingId);

    try {
        // Gửi yêu cầu HTTP POST tới FastAPI Backend
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: query,
                field: currentField
            })
        });

        // Chờ và lấy kết quả trả về từ Python
        const data = await response.json();

        // Xóa dòng trạng thái "đang suy nghĩ..."
        removeMessage(typingId);

        // Xử lý và hiển thị câu trả lời
        if (data.status === "success") {
            const formattedAnswer = formatAIResponse(data.answer, data.source_type);
            appendMessage("bot", formattedAnswer);
        } else {
            appendMessage("bot", `❌ Có lỗi xảy ra: ${data.answer}`);
        }

    } catch (error) {
        // Xóa dòng "đang suy nghĩ" nếu bị lỗi kết nối
        removeMessage(typingId);
        appendMessage("bot", "❌ Lỗi kết nối! Vinh hãy kiểm tra xem `web_server.py` đã chạy chưa và Port 8000 đã được Forward trong VS Code chưa nhé.");
        console.error("Lỗi Fetch API:", error);
    }
}

/**
 * Hàm 3: In tin nhắn ra khung chat
 */
function appendMessage(role, text, id = null) {
    const msgContainer = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    
    msgDiv.className = `msg ${role}`;
    if (id) msgDiv.id = id;

    msgDiv.innerHTML = `
        <div class="msg-content">
            ${role === 'bot' && !id ? '<b>⚖️ LexAI:</b><br>' : ''}
            ${text}
        </div>
    `;

    msgContainer.appendChild(msgDiv);
    
    // Tự động cuộn trang xuống dòng tin nhắn mới nhất
    msgContainer.scrollTop = msgContainer.scrollHeight;
}

/**
 * Hàm 4: Xóa một tin nhắn (Dùng để xóa dòng "đang suy nghĩ" sau khi có kết quả)
 */
function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Hàm 5: Định dạng lại câu trả lời của AI (Xuống dòng và gắn thẻ nguồn)
 */
function formatAIResponse(answer, sourceType) {
    // Đổi các ký tự \n của Python thành thẻ <br> của HTML để hiển thị xuống dòng đúng
    let formatted = answer.replace(/\n/g, '<br>');
    
    // Gắn thêm thẻ hiển thị nguồn tài liệu vào cuối câu trả lời (nếu có)
    if (sourceType) {
        formatted += `<span class="source-tag">📌 Nguồn truy xuất: <b>${sourceType}</b></span>`;
    }
    
    return formatted;
}

/**
 * Hàm 6: Cho phép nhấn phím Enter để gửi câu hỏi nhanh (không cần click chuột)
 */
document.getElementById('user-query').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        ask();
    }
});