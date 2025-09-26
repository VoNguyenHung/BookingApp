from appSale.models import Category, Product, UserRole, Order, OrderItem, User
from appSale import app, db
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import logout_user, current_user
from flask import redirect
from datetime import datetime, timezone, date

from utils import get_monthly_revenue_stats, get_product_sales_stats, get_general_stats

admin = Admin(app=app, name='QUẢN TRỊ TRÀ SỮA OU', template_mode='bootstrap4')


class AuthenticatedAdmin(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AuthenticatedUser(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class MyProductView(AuthenticatedAdmin):
    column_list = ['id', 'name', 'price', 'active']
    column_searchable_list = ['name']
    column_filters = ['price', 'name']
    can_export = True
    edit_modal = True


class MyCategoryView(AuthenticatedAdmin):
    column_list = ['name', 'products']

    def products_formatter(view, context, model, name):

        product_names = [p.name for p in model.products]

        return ", ".join(product_names)

    column_formatters = {
        'products': products_formatter
    }



class MyOrderView(AuthenticatedAdmin): # Tùy chỉnh cho Order
    column_list = ['id', 'user', 'order_date', 'total_amount', 'status']
    column_searchable_list = ['status']
    column_filters = ['order_date', 'status', 'total_amount']
    column_editable_list = ['status'] # Có thể cho phép sửa status đơn hàng
    # Định dạng ngày tháng
    column_formatters = {
        'order_date': lambda v, c, m, p: m.order_date.strftime('%d/%m/%Y %H:%M:%S') if m.order_date else ''
    }
    column_filters = [
        'order_date',  # Giữ lại bộ lọc ngày mặc định nếu bạn muốn tùy chọn khác
        'status',
        'total_amount',

    ]



class MyOrderItemView(AuthenticatedAdmin): # Tùy chỉnh cho OrderItem
    column_list = ['id', 'order', 'product', 'quantity', 'price_at_purchase']
    column_searchable_list = ['product.name']
    column_filters = ['quantity']

    column_formatters = {
        'product': lambda v, c, m, p: f"{m.product.name} ({m.product.price:,.0f} VNĐ)"
    }
class MyStatsView(AuthenticatedUser): # Vẫn đảm bảo chỉ admin truy cập
    @expose("/")
    def index(self):
        # Lấy năm hiện tại để truyền vào các hàm thống kê
        current_year = datetime.now().year

        # Gọi các hàm từ utils.py
        general_stats = get_general_stats()
        monthly_revenue_stats = get_monthly_revenue_stats(year=current_year)
        product_sales_stats = get_product_sales_stats(year=current_year)
        today = datetime.now(timezone.utc).date()

        today_start = datetime.combine(date.today(), datetime.min.time())  # Bắt đầu ngày hôm nay
        today_end = datetime.combine(date.today(), datetime.max.time())  # Kết thúc ngày hôm nay
        # Truyền tất cả dữ liệu đã lấy vào template
        return self.render('admin/stats.html',
                           # Dữ liệu tổng quan
                           num_products=general_stats['num_products'],
                           num_orders=general_stats['num_orders'],
                           total_revenue=general_stats['total_revenue'],
                           new_orders_today=general_stats['new_orders_today'],
                           today_date_str=today.strftime('%d/%m/%Y'),
                           current_year=current_year,  # Vẫn truyền năm để hiển thị trên tiêu đề

                           # Dữ liệu cho biểu đồ Doanh thu theo tháng
                           monthly_labels=monthly_revenue_stats['labels'],
                           monthly_revenues=monthly_revenue_stats['data'],

                           # Dữ liệu cho biểu đồ Số lượng sản phẩm bán ra
                           product_labels=product_sales_stats['labels'],
                            product_quantities=product_sales_stats['data'],
                           today_filter_start=today_start.isoformat(),
                           today_filter_end=today_end.isoformat()
                           )


class LogoutView(AuthenticatedUser):
    @expose("/")
    def index(self):
        logout_user()
        return redirect('/')


admin.add_view(MyCategoryView(Category, db.session))
admin.add_view(MyProductView(Product, db.session))
admin.add_view(MyOrderView(Order, db.session)) # THÊM
admin.add_view(MyOrderItemView(OrderItem, db.session)) # THÊM
admin.add_view(MyStatsView(name='Thống kê báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))
