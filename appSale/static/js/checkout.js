
document.addEventListener('DOMContentLoaded', function() {
    console.log("Checkout script loaded!"); // Xác nhận script đã tải
    const placeOrderBtn = document.getElementById('placeOrderBtn');
    if (placeOrderBtn) { // Đảm bảo nút tồn tại trước khi thêm listener
        placeOrderBtn.addEventListener('click', placeOrder);
        console.log("Event listener attached to placeOrderBtn.");
    } else {
        console.error("Error: placeOrderBtn not found!");
    }
});
// Hàm để xử lý logic đặt hàng
function placeOrder() {
    // 1. Lấy dữ liệu từ các trường input trên form
    const fullName = document.getElementById('fullName').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const address = document.getElementById('address').value.trim();
    const notes = document.getElementById('notes').value.trim();
    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;

    // Kiểm tra hợp lệ dữ liệu
    if (!fullName || !phone || !address) {
        alert('Vui lòng điền đầy đủ Họ và tên người nhận, Số điện thoại và Địa chỉ giao hàng.');
        return; // Dừng hàm nếu dữ liệu không hợp lệ
    }

    // Tạo đối tượng dữ liệu đơn hàng
    const orderData = {
        'customer_info': {
            'full_name': fullName,
            'phone': phone,
            'address': address,
            'notes': notes
        },
        'payment_method': paymentMethod
    };

    // Gửi yêu cầu đặt hàng đến backend (API Flask)
    fetch('/api/place-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
    })
    .then(response => {
        // Kiểm tra xem phản hồi có phải là JSON không
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        } else {
            // Nếu không phải JSON, có thể là lỗi server không trả về JSON
            throw new Error('Phản hồi từ server không phải JSON. Vui lòng kiểm tra lại backend.');
        }
    })
    .then(data => {
        if (data.success) {
            alert(data.message); // Hiển thị thông báo từ server
            // Chuyển hướng người dùng đến trang xác nhận đơn hàng
            window.location.href = '/order-confirmation/' + data.order_id;
        } else {
            alert('Có lỗi xảy ra khi đặt hàng: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Lỗi khi gửi yêu cầu đặt hàng:', error);
        alert('Không thể kết nối đến máy chủ hoặc có lỗi xảy ra. Vui lòng thử lại.');
    });
}

// Gắn sự kiện cho nút "Xác nhận đặt hàng" sau khi DOM đã tải hoàn toàn