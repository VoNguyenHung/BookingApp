function addToCart(id, name, price) {
    fetch('/api/add-cart', {
        method: "post",
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        console.info(data)
        let d = document.getElementsByClassName("cart-counter")
        for (let i = 0; i < d.length; i++)
            d[i].innerText = data.total_quantity
    })
    alert("đã thêm vào giỏ hàng")
}

async function updateCart(id, quantity) {
    try {
        const response = await fetch('/api/update-cart', {
            method: "PUT",
            body: JSON.stringify({
                "id": id,
                "quantity": quantity
            }),
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error updating cart:', errorData.error);
            alert('Có lỗi xảy ra khi cập nhật giỏ hàng: ' + errorData.error);
            return;
        }

        const data = await response.json();

        // Cập nhật số lượng sản phẩm trong giỏ hàng
        document.querySelectorAll(".cart-counter").forEach(el => {
            el.innerText = data.total_quantity;
        });

        // Cập nhật tổng số tiền hiển thị trong giỏ hàng
        document.querySelectorAll(".cart-amount").forEach(el => {
            el.innerText = new Intl.NumberFormat().format(data.total_amount) + ' VNĐ';
        });

    } catch (error) {
        console.error('Error updating cart:', error);
        alert('Có lỗi xảy ra khi cập nhật giỏ hàng.');
    }
}

function validateAndUpdateCart(id, inputElement, delta = 0) { // Thêm delta = 0 làm mặc định
    let quantity = parseInt(inputElement.value, 10);

    if (delta !== 0) { // Nếu gọi từ nút +/-
        quantity += delta;
    }

    if (isNaN(quantity) || quantity < 1) {
        quantity = 1;
    }
    inputElement.value = quantity; // Cập nhật giá trị input ngay lập tức

    // Gọi hàm updateCart để cập nhật giỏ hàng
    updateCart(id, quantity);
}

function deleteCart(id) {
    fetch('/api/delete-cart', {
        method: "POST",
        body: JSON.stringify({
            "id": id
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        console.info(data)
        let d = document.getElementsByClassName("cart-counter")
        for (let i = 0; i < d.length; i++)
            d[i].innerText = data.total_quantity

        // Cập nhật tổng tiền hiển thị trong giỏ hàng
        let totalAmount = document.getElementsByClassName("cart-amount")
        for (let i = 0; i < totalAmount.length; i++)
            totalAmount[i].innerText = new Intl.NumberFormat().format(data.total_amount) + ' VNĐ'

        // Xóa sản phẩm khỏi giao diện người dùng
        let item = document.getElementById(`cart${id}`)
        if (item) {
            item.remove()
        }
    }).catch(error => console.error('Error deleting item from cart:', error))
}
function pay() {
    // Lấy tổng số lượng sản phẩm trong giỏ hàng để kiểm tra
    // Giả sử bạn có một phần tử có class 'cart-counter' hiển thị tổng số lượng
    const cartTotalQuantityElement = document.querySelector('.cart-counter');
    let cartTotalQuantity = 0;
    if (cartTotalQuantityElement) {
        cartTotalQuantity = parseInt(cartTotalQuantityElement.innerText);
    }

    // Kiểm tra xem giỏ hàng có trống không
    if (cartTotalQuantity === 0) {
        // Sử dụng hàm showCartMessage nếu bạn đã định nghĩa, hoặc dùng alert
        // showCartMessage('Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm để thanh toán.', 'warning');
        alert('Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm để thanh toán.');
        return; // Ngừng hàm nếu giỏ hàng rỗng
    } else
        window.location.href = '/checkout'
}



