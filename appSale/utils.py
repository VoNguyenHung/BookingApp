from appSale.models import Category, Product, User
from appSale import app, db
import hashlib
import re
from flask import request, flash
from appSale.models import Product, Order, OrderItem
from sqlalchemy import func, extract

from datetime import datetime, timezone

def get_categories():
    return Category.query.all()


def get_products(kw, cate_id, page=None):
    products = Product.query

    if kw:
        products = products.filter(Product.name.contains(kw))

    if cate_id:
        products = products.filter(Product.category_id.__eq__(cate_id))

    if page:
        page = int(page)
        page_size = app.config['PAGE_SIZE']
        start = (page - 1)*page_size

        return products.slice(start, start + page_size)

    return products.all()


def count_products():
    return Product.query.count()
def add_user(name, email, password, phone, **kwargs):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(name=name.strip(),
                email=email.strip(),
                phone=phone.strip(),
                password=password,
                avatar=kwargs.get('avatar'))
    db.session.add(user)
    db.session.commit()
def get_prev_url():
    referer = request.headers.get('Referer')

    if referer and referer != request.url:
        return referer
    else:
        return '/'
def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)

# THÊM HOẶC ĐẢM BẢO HÀM NÀY CÓ TRONG utils.py
def get_user_by_email(email):
    return User.query.filter_by(email=email).first()
def check_login(email, password):
    if email and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        return User.query.filter(User.email.__eq__(email.strip()),
                                 User.password.__eq__(password)).first()
def get_user_by_id(user_id):
    return User.query.get(user_id)
def get_email(user_email, ):
    return User.query.filter_by(email=user_email).first()


def cart_stats(cart):
    total_amount, total_quantity = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity']*c['price']

    return {
        'total_amount': total_amount,
        'total_quantity': total_quantity
    }


def get_monthly_revenue_stats(year=None):
    """
    Thống kê doanh thu theo tháng cho các đơn hàng đã hoàn thành.
    Mặc định lấy thống kê cho năm hiện tại.
    """
    if year is None:
        year = datetime.now().year

    monthly_revenue_data = db.session.query(
        extract('month', Order.order_date).label('month'),
        func.sum(Order.total_amount).label('total_revenue')
    ).filter(
        Order.status == 'Completed',
        extract('year', Order.order_date) == year
    ).group_by('month').order_by('month').all()

    # Chuyển đổi dữ liệu sang định dạng phù hợp cho Chart.js
    labels = []
    revenues = []
    for row in monthly_revenue_data:
        labels.append(f"Tháng {int(row.month)}")
        revenues.append(float(row.total_revenue))

    return {
        'labels': labels,
        'data': revenues,
        'year': year
    }

def get_product_sales_stats(year=None):
    """
    Thống kê số lượng sản phẩm bán ra cho các đơn hàng đã hoàn thành.
    Mặc định lấy thống kê cho năm hiện tại.
    """
    if year is None:
        year = datetime.now().year

    product_sales_data = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(OrderItem, Product.id == OrderItem.product_id)\
    .join(Order, OrderItem.order_id == Order.id)\
    .filter(
        Order.status == 'Completed',
        extract('year', Order.order_date) == year
    )\
    .group_by(Product.name).order_by(func.sum(OrderItem.quantity).desc()).all()

    # Chuyển đổi dữ liệu sang định dạng phù hợp cho Chart.js
    labels = []
    quantities = []
    for row in product_sales_data:
        labels.append(row.name)
        quantities.append(int(row.total_quantity))

    return {
        'labels': labels,
        'data': quantities,
        'year': year
    }

def get_general_stats():
    """
    Lấy các thống kê tổng quan (số sản phẩm, số người dùng, tổng đơn hàng, tổng doanh thu, đơn hàng mới hôm nay).
    """
    num_products = db.session.query(Product).count()
    num_orders = db.session.query(Order).count()

    total_revenue_obj = db.session.query(func.sum(Order.total_amount)).filter(Order.status == 'Completed').scalar()
    total_revenue = total_revenue_obj if total_revenue_obj else 0

    today = datetime.now(timezone.utc).date()
    new_orders_today = db.session.query(Order).filter(
        func.date(Order.order_date) == today
    ).count()

    return {
        'num_products': num_products,
        'num_orders': num_orders,
        'total_revenue': total_revenue,
        'new_orders_today': new_orders_today,
        'today_date_str': today.strftime('%d/%m/%Y')
    }

