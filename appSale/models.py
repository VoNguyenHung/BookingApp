from datetime import datetime, date, timedelta, timezone
from sqlalchemy import Column, String, Integer, Enum, Float, ForeignKey, Date, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy # Import SQLAlchemy ở đây
from flask_login import UserMixin
from enum import Enum as UserEnum # Đổi tên để tránh xung đột với Enum của SQLAlchemy
import hashlib
from appSale import app, db
class Basemodel(db.Model):
    __abstract__ = True # Đánh dấu đây là một lớp trừu tượng (abstract base class)

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Có thể thêm các trường chung khác như created_at, updated_at ở đây


class UserRole(UserEnum):
    CUSTOMER = 1
    ADMIN = 2
    EMP = 3

class OrderStatus(UserEnum):
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'
    DELIVERED = 'Delivered'

class User(Basemodel, UserMixin):
    __tablename__ = 'users'

    name = Column(String(50), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    password = Column(String(128), nullable=False) # Lưu password hash, không phải plaintext
    phone = Column(String(20), nullable=True) # Số điện thoại có thể không bắt buộc
    address = Column(String(255), nullable=True) # Địa chỉ mặc định
    avatar = Column(String(255), nullable=True) # Đường dẫn tới ảnh đại diện
    user_role = Column(Enum(UserRole), default=UserRole.CUSTOMER)

    # Mối quan hệ với các bảng khác
    orders = relationship('Order', backref='user', lazy=True)




class Category(Basemodel):
    __tablename__ = 'categories'

    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True) # Mô tả chi tiết hơn về danh mục
    products = relationship('Product', backref='category', lazy=True)


class Product(Basemodel):
    __tablename__ = 'products'

    name = Column(String(150), nullable=False)
    description = Column(String(1000), nullable=True)
    price = Column(Numeric(10, 2), nullable=False) # Sử dụng Numeric cho giá tiền
    image_url = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True) # Trạng thái sản phẩm (còn bán không)

    # Khóa ngoại đến Category
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    # Mối quan hệ với OrderItem
    order_items = relationship('OrderItem', backref='product', lazy=True)


class Order(Basemodel):
    __tablename__ = 'orders'

    order_date = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    total_amount = Column(Numeric(12, 2), nullable=False)

    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    delivery_address = Column(String(255), nullable=False)
    delivery_fee = Column(Numeric(10, 2), default=0.00)
    notes = Column(String(500), nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(50), nullable=True, default='Unpaid')

    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    items = relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")


class OrderItem(Basemodel):
    __tablename__ = 'order_items'

    quantity = Column(Integer, nullable=False, default=1)
    price_at_order = Column(Numeric(10, 2), nullable=False) # Giá sản phẩm tại thời điểm đặt hàng
    item_total = Column(Numeric(10, 2), nullable=False) # quantity * price_at_order

    # Khóa ngoại đến Order và Product
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

class Comment(Basemodel):
    __tablename__ = 'comments'

    content = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.now(timezone.utc))

    # Khóa ngoại đến User
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # Khóa ngoại đến Product
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

    # Mối quan hệ với các bảng khác
    user = relationship('User', backref='comments', lazy=True)
    product = relationship('Product', backref='comments', lazy=True)

if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        common_password_hash = str(hashlib.md5("123456".strip().encode('utf-8')).hexdigest())

        admin_user = User(
            name='Nguyễn Văn Admin',
            email='admin@example.com',
            password=common_password_hash,
            phone='0987654321',
            address='123 Đường Admin, Quận 1, TP.HCM',
            avatar='https://example.com/avatars/admin.jpg',
            user_role=UserRole.ADMIN
        )

        customer1 = User(
            name='Trần Thị Khách Hàng',
            email='customer1@example.com',
            password=common_password_hash,
            phone='0901234567',
            address='456 Đường Khách, Quận 3, TP.HCM',
            avatar='https://example.com/avatars/customer1.jpg',
            user_role=UserRole.CUSTOMER
        )

        customer2 = User(
            name='Lê Văn Vãng Lai',
            email='customer2@example.com',
            password=common_password_hash,
            phone='0902345678',
            address='789 Đường Vãng Lai, Quận 5, TP.HCM',
            avatar='https://example.com/avatars/customer2.jpg',
            user_role=UserRole.CUSTOMER
        )
        emp = User(
            name='Võ Nguyên HÙng',
            email='emp@example.com',
            password=common_password_hash,
            phone='0901234567',
            address='Nhà Bè, TP.HCM',
            avatar='https://example.com/avatars/customer1.jpg',
            user_role=UserRole.EMP
        )

        db.session.add_all([admin_user, customer1, customer2, emp])
        db.session.commit()
        print("Đã tạo dữ liệu Users.")

        # --- 2. Tạo dữ liệu Categories ---
        cat_coffee = Category(name='Cà Phê', description='Các loại cà phê hạt, rang xay và pha sẵn.')
        cat_milk_tea = Category(name='Trà Sữa', description='Các loại trà sữa trân châu, pudding và topping đa dạng.')
        cat_juice = Category(name='Nước Ép', description='Các loại nước ép trái cây tươi nguyên chất.')
        cat_bakery = Category(name='Bánh Ngọt', description='Các loại bánh ngọt, bánh mì và món tráng miệng.')

        db.session.add_all([cat_coffee, cat_milk_tea, cat_juice, cat_bakery])
        db.session.commit()
        print("Đã tạo dữ liệu Categories.")

        # --- 3. Tạo dữ liệu Products ---
        # Đảm bảo các category đã có ID sau khi commit
        prod_espresso = Product(
            name='Espresso Shot',
            description='Cà phê Espresso đậm đặc, thơm ngon.',
            price=25000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753527613/capheden_rmmslt.png',
            category_id=cat_coffee.id
        )

        prod_latte = Product(
            name='Latte Đá',
            description='Latte đá với sữa tươi và lớp bọt sữa mịn.',
            price=45000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753527719/latte_eafndd.png',
            category_id=cat_coffee.id
        )

        prod_pearl_milk_tea = Product(
            name='Trà Sữa Trân Châu Đường Đen',
            description='Trà sữa truyền thống với trân châu đường đen dai ngon.',
            price=35000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753527798/tcdd_zx0i8i.png',
            category_id=cat_milk_tea.id
        )

        prod_matcha_milk_tea = Product(
            name='Trà Sữa Matcha',
            description='Trà sữa vị Matcha thanh mát.',
            price=40000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753527845/matcha_ka8v5v.png',
            category_id=cat_milk_tea.id
        )

        prod_orange_juice = Product(
            name='Nước Cam Tươi',
            description='Nước cam tươi 100% vắt từ cam sành.',
            price=30000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753527894/cam_shi9ns.png',
            category_id=cat_juice.id
        )

        prod_carrot_juice = Product(
            name='Nước Ép Cà Rốt',
            description='Nước ép cà rốt nguyên chất tốt cho mắt.',
            price=32000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753527946/caRot_tjx7yu.png',
            category_id=cat_juice.id
        )

        prod_tiramisu = Product(
            name='Bánh Tiramisu',
            description='Bánh Tiramisu chuẩn Ý với lớp kem mascarpone béo ngậy.',
            price=60000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753527987/tiramisu_wftwuu.png',
            category_id=cat_bakery.id
        )

        prod_croissant = Product(
            name='Bánh Croissant Bơ',
            description='Bánh sừng bò Pháp giòn rụm với hương bơ.',
            price=20000.00,
            image_url='https://res.cloudinary.com/dr1dlhww5/image/upload/v1753528063/banhBo_wkw92y.png',
            category_id=cat_bakery.id
        )

        db.session.add_all([
            prod_espresso, prod_latte, prod_pearl_milk_tea, prod_matcha_milk_tea,
            prod_orange_juice, prod_carrot_juice, prod_tiramisu, prod_croissant
        ])
        db.session.commit()
        print("Đã tạo dữ liệu Products.")

        # --- 4. Tạo dữ liệu Orders ---
        # Đơn hàng của customer1
        order1 = Order(
            order_date=datetime.now(timezone.utc) - timedelta(days=5),  # 5 ngày trước
            total_amount=95000.00,  # Sẽ được tính lại chính xác bởi OrderItems
            status=OrderStatus.COMPLETED,
            delivery_address='456 Đường Khách, Quận 3, TP.HCM',
            payment_method='MoMo',
            payment_status='Paid',
            user_id=customer1.id
        )

        # Đơn hàng của customer2
        order2 = Order(
            order_date=datetime.now(timezone.utc) - timedelta(days=2),  # 2 ngày trước
            total_amount=135000.00,  # Sẽ được tính lại chính xác bởi OrderItems
            status=OrderStatus.COMPLETED,
            delivery_address='789 Đường Vãng Lai, Quận 5, TP.HCM',
            payment_method='Cash',
            payment_status='Unpaid',
            user_id=customer2.id
        )

        # Đơn hàng của khách vãng lai (user_id = NULL)
        order3 = Order(
            order_date=datetime.now(timezone.utc) - timedelta(days=1),  # 1 ngày trước
            total_amount=70000.00,  # Sẽ được tính lại chính xác bởi OrderItems
            status=OrderStatus.COMPLETED,
            delivery_address='101 Đường Tự Do, Quận Bình Thạnh, TP.HCM',
            payment_method='Cash',
            payment_status='Unpaid',
            user_id=None  # Khách vãng lai
        )

        db.session.add_all([order1, order2, order3])
        db.session.commit()
        print("Đã tạo dữ liệu Orders.")

        # --- 5. Tạo dữ liệu OrderItems ---
        # Order 1 (customer1): Latte Đá (1) + Trà Sữa Trân Châu Đường Đen (1) + Nước Cam Tươi (1)
        item1_order1 = OrderItem(
            order_id=order1.id,
            product_id=prod_latte.id,
            quantity=1,
            price_at_order=prod_latte.price,
            item_total=prod_latte.price * 1
        )
        item2_order1 = OrderItem(
            order_id=order1.id,
            product_id=prod_pearl_milk_tea.id,
            quantity=1,
            price_at_order=prod_pearl_milk_tea.price,
            item_total=prod_pearl_milk_tea.price * 1
        )
        item3_order1 = OrderItem(
            order_id=order1.id,
            product_id=prod_orange_juice.id,
            quantity=1,
            price_at_order=prod_orange_juice.price,
            item_total=prod_orange_juice.price * 1
        )

        # Order 2 (customer2): Trà Sữa Matcha (2) + Bánh Tiramisu (1)
        item1_order2 = OrderItem(
            order_id=order2.id,
            product_id=prod_matcha_milk_tea.id,
            quantity=2,
            price_at_order=prod_matcha_milk_tea.price,
            item_total=prod_matcha_milk_tea.price * 2
        )
        item2_order2 = OrderItem(
            order_id=order2.id,
            product_id=prod_tiramisu.id,
            quantity=1,
            price_at_order=prod_tiramisu.price,
            item_total=prod_tiramisu.price * 1
        )

        # Order 3 (khách vãng lai): Espresso Shot (1) + Bánh Croissant Bơ (1)
        item1_order3 = OrderItem(
            order_id=order3.id,
            product_id=prod_espresso.id,
            quantity=1,
            price_at_order=prod_espresso.price,
            item_total=prod_espresso.price * 1
        )
        item2_order3 = OrderItem(
            order_id=order3.id,
            product_id=prod_croissant.id,
            quantity=1,
            price_at_order=prod_croissant.price,
            item_total=prod_croissant.price * 1
        )

        db.session.add_all([
            item1_order1, item2_order1, item3_order1,
            item1_order2, item2_order2,
            item1_order3, item2_order3
        ])
        db.session.commit()
        print("Đã tạo dữ liệu OrderItems.")

        # --- Cập nhật total_amount cho các Order (quan trọng) ---
        # Trong một ứng dụng thực tế, total_amount nên được tính toán khi Order được tạo hoặc cập nhật
        # Ở đây, ta cập nhật sau khi OrderItems đã được tạo
        for order in [order1, order2, order3]:
            total_items_value = sum(item.item_total for item in order.items)
            order.total_amount = total_items_value + order.delivery_fee
            db.session.add(order)  # Đưa lại vào session để cập nhật

        comment1 = Comment(
            content='Bánh rất ngon, giao hàng nhanh.',
            created_date=datetime.now(timezone.utc),
            user_id=customer1.id,
            product_id=prod_croissant.id
        )

        comment2 = Comment(
            content='Nước cam tươi, ngọt.',
            created_date=datetime.now(timezone.utc),
            user_id=customer2.id,
            product_id=prod_orange_juice.id
        )

        comment3 = Comment(
            content='Giá hơi cao nhưng đáng tiền.',
            created_date=datetime.now(timezone.utc),
            user_id=customer2.id,
            product_id=prod_matcha_milk_tea.id
        )

        # Thêm tất cả các đối tượng vào session
        db.session.add_all([comment1, comment2, comment3])
        db.session.commit()
