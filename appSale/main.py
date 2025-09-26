from flask import render_template, request, redirect, url_for, session, jsonify, flash
from appSale import app, utils, login, db
import math
import cloudinary.uploader
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from appSale.models import UserRole, User, Order, OrderItem, Comment, Product, OrderStatus
from datetime import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
import json

# Lấy thời gian hiện tại theo UTC
utc_now = datetime.now(timezone.utc)

# Định nghĩa múi giờ Việt Nam
vn_timezone = ZoneInfo('Asia/Ho_Chi_Minh')

# Chuyển đổi sang giờ Việt Nam
vn_time = utc_now.astimezone(vn_timezone)

@app.route('/')
def index():
    kw = request.args.get('kw')
    cate_id = request.args.get('cate_id')
    page = request.args.get('page', 1)

    cates = utils.get_categories()
    prods = utils.get_products(kw, cate_id, page)
    countPro = utils.count_products()

    page_size = app.config['PAGE_SIZE']

    return render_template('index.html', categories=cates,
                           products=prods, pages=math.ceil(countPro / app.config['PAGE_SIZE']))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Lấy sản phẩm dựa trên product_id
    product = Product.query.get_or_404(product_id)
    # Lấy tất cả bình luận của sản phẩm đó, sắp xếp theo ngày tạo mới nhất
    comments = Comment.query.filter_by(product_id=product_id).order_by(Comment.created_date.desc()).all()

    return render_template('product_detail.html', product=product, comments=comments,timezone=ZoneInfo)


@app.route('/product/comment', methods=['POST'])
@login_required
def add_comment():
    # Lấy dữ liệu từ form
    id_sp = request.form.get('product_id')
    content = request.form.get('content')

    if content:
        # Tạo đối tượng Comment mới
        new_comment = Comment(
            content=content,
            user_id=current_user.id,
            product_id=id_sp
        )
        db.session.add(new_comment)
        db.session.commit()

    else:
        flash('Nội dung bình luận không được để trống.', 'danger')

    return redirect(url_for('product_detail', product_id=id_sp))
@app.route('/register', methods=['get', 'post'])
def user_register():
    err_msg = ""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        avatar_path = None

        if password.strip() == confirm.strip():

            # Check if email is in a valid format
            if not utils.is_valid_email(email):
                err_msg = "Định dạng email không hợp lệ."
            else:
                # Check if the email is already registered
                if utils.get_email(email):
                    err_msg = "Email đã được đăng ký. Vui lòng chọn email khác."
                else:
                    avatar = request.files.get('avatar')
                    if avatar:
                        res = cloudinary.uploader.upload(avatar)
                        avatar_path = res['secure_url']
                    # Add the new user to the database
                    utils.add_user(name=name, email=email, password=password, phone=phone, avatar=avatar_path)
                    return redirect(url_for('user_login'))
        else:
            err_msg = "Mật khẩu và xác nhận mật khẩu không khớp."

    return render_template('register.html', err_msg=err_msg)


@app.route('/login', methods=['get', 'post'])
def user_login():
    err_msg = ""
    if request.method.__eq__('POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        user = utils.check_login(email=email, password=password)

        if user:
            login_user(user=user)
            session['name'] = user.name
            session['user_role'] = user.user_role.value
            if user.user_role == UserRole.CUSTOMER:
                return redirect(url_for('index'))
            elif user.user_role == UserRole.EMP:
                return redirect(url_for('employee_orders'))
            elif user.user_role == UserRole.ADMIN:
                return redirect('admin')
            else:
                return redirect(url_for('index'))
        else:
            err_msg = "Email hoặc mật khẩu không chính xác."

    return render_template('login.html', err_msg=err_msg)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


@app.route('/employee/orders')
@login_required
def employee_orders():
    if current_user.user_role != UserRole.EMP:  # Giả sử vai trò là 'employee'
        return "Bạn không có quyền truy cập trang này.", 403

    # Lấy tất cả các đơn hàng có trạng thái 'Pending' và 'Processing'
    orders = Order.query.filter(Order.status.in_(['Pending', 'Processing'])).order_by(Order.order_date.asc()).all()

    return render_template('employee/index.html', orders=orders, timezone=ZoneInfo)


# Route xử lý cập nhật trạng thái đơn hàng và thanh toán
@app.route('/employee/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.user_role != UserRole.EMP:
        return "Bạn không có quyền thực hiện hành động này.", 403

    order = Order.query.get_or_404(order_id)

    # Lấy dữ liệu từ form
    new_status = request.form.get('order_status')
    new_payment_status = request.form.get('payment_status')

    # Cập nhật trạng thái nếu có thay đổi
    if new_status and new_status in [s.value for s in OrderStatus]:
        order.status = new_status

    if new_payment_status:
        order.payment_status = new_payment_status

    try:
        db.session.commit()
        flash(f"Đơn hàng #{order_id} đã được cập nhật thành công!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi: Không thể cập nhật đơn hàng. {e}", 'danger')

    return redirect(url_for('employee_orders'))


@app.route('/employee/create_order')
@login_required
def create_order():
    if current_user.user_role != UserRole.EMP:
        return "Bạn không có quyền truy cập trang này.", 403

    products = Product.query.all()
    categories = Category.query.all()

    return render_template('employee/create_order.html', products=products, categories=categories)


@app.route('/employee/submit_in_store_order', methods=['POST'])
@login_required
def submit_in_store_order():
    # Kiểm tra quyền của nhân viên
    if current_user.user_role != UserRole.EMP:  # Sử dụng .value nếu UserRole là Enum với giá trị
        flash("Bạn không có quyền thực hiện hành động này.", 'danger')
        return redirect(url_for('employee_orders'))  # Chuyển hướng về trang danh sách đơn hàng của nhân viên

    try:
        # Lấy dữ liệu giỏ hàng từ form và chuyển đổi từ JSON string sang Python dictionary
        cart_data_json = request.form.get('cart_data', '{}')
        employee_cart = json.loads(cart_data_json)

        total_amount_str = request.form.get('total_amount', '0')
        total_amount = float(total_amount_str)  # Chuyển đổi sang float để tính toán

        if not employee_cart:
            flash('Đơn hàng rỗng! Vui lòng thêm sản phẩm.', 'warning')
            return redirect(url_for('create_order'))

        # Tạo một đơn hàng mới
        new_order = Order(

            user_id=current_user.id,
            order_date=datetime.now(timezone.utc),
            total_amount=total_amount,
            status=OrderStatus.COMPLETED,
            payment_status='Paid',  # Đặt trạng thái Paid
            delivery_address="Tại quầy",  # Địa chỉ mặc định cho đơn hàng tại quầy
            delivery_fee=0.00,
            notes="Đơn hàng tại quầy",
            payment_method="Tiền mặt"  # Phương thức thanh toán mặc định tại quầy
        )
        db.session.add(new_order)
        db.session.flush()  # Để có ID của new_order trước khi thêm OrderItem

        # Thêm các mục sản phẩm vào đơn hàng
        for product_id_str, item_data in employee_cart.items():
            product = Product.query.get(item_data['id'])  # Lấy đối tượng Product
            if product:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item_data['quantity'],
                    price_at_order=product.price,  # Lưu giá tại thời điểm đặt hàng
                    item_total=product.price * item_data['quantity']
                )
                db.session.add(order_item)
            else:
                flash(f"Sản phẩm ID {item_data['id']} không tìm thấy, bỏ qua.", 'warning')

        db.session.commit()
        flash(f'Đơn hàng #{new_order.id} đã được tạo và thanh toán thành công!', 'success')

    except json.JSONDecodeError:
        db.session.rollback()
        flash('Lỗi dữ liệu giỏ hàng không hợp lệ.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Đã xảy ra lỗi khi tạo đơn hàng: {e}', 'danger')

    return redirect(url_for('create_order'))
@app.route("/profile")
def profile():
    if current_user.is_authenticated:
        user_id = current_user.id

        # Truy vấn Lịch sử mua hàng (Orders) của người dùng
        purchase_history = (db.session.query(Order)
                            .filter(Order.user_id == user_id)
                            .options(
            db.joinedload(Order.items).joinedload(OrderItem.product))  # Tải các OrderItem và Product liên quan
                            .order_by(Order.order_date.desc())  # Sắp xếp theo ngày gần nhất
                            .all())

    return render_template('profile.html', purchase_history=purchase_history)  # Truyền purchase_history vào template


# --- ROUTE CẬP NHẬT THÔNG TIN CÁ NHÂN (EDIT PROFILE) ---
@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if request.method == 'POST':
        new_name = request.form['new_name']
        new_email = request.form['new_email']
        new_phone = request.form['new_phone']
        new_address = request.form.get('new_address')
        new_avatar_file = request.files.get('new_avatar')

        # Thực hiện tìm và cập nhật thông tin người dùng trong cơ sở dữ liệu
        user_id_to_update = current_user.id  # ID của người dùng cần cập nhật, đây chỉ là ví dụ
        user = User.query.get(user_id_to_update)

        if user:
            # Cập nhật các trường thông tin cơ bản (chỉ khi chúng được cung cấp)
            if new_name:
                user.name = new_name
            if new_email:
                user.email = new_email
            if new_phone:
                user.phone = new_phone
            # Address có thể là rỗng, nên không cần if
            user.address = new_address  # Gán giá trị, có thể là None nếu không được cung cấp

            # --- Xử lý tải lên Avatar lên Cloudinary ---
            if new_avatar_file and new_avatar_file.filename != '':
                try:

                    upload_result = cloudinary.uploader.upload(
                        new_avatar_file,

                        public_id=f"user_{user.id}_avatar",  # ID công khai của ảnh (tùy chọn)
                        overwrite=True  # Ghi đè nếu có ảnh cũ với cùng public_id
                    )
                    # Lấy URL an toàn của ảnh đã tải lên
                    user.avatar = upload_result['secure_url']
                    print(f"Avatar uploaded to Cloudinary: {user.avatar}")

                except Exception as e:
                    print(f"Lỗi khi tải avatar lên Cloudinary: {e}")
                    # Trả về lỗi nếu không thể tải ảnh lên
                    return jsonify({'message': f'Lỗi khi tải ảnh đại diện: {str(e)}'}), 500
            # --- Kết thúc xử lý Cloudinary ---

            try:
                db.session.commit()
                return jsonify({'message': 'Thông tin đã được cập nhật thành công', 'success': True})
            except Exception as e:
                db.session.rollback()
                print(f"Lỗi khi cập nhật thông tin người dùng vào DB: {e}")
                return jsonify({'message': f'Lỗi khi lưu thông tin: {str(e)}', 'success': False}), 500

        return jsonify({'message': 'Không tìm thấy người dùng để cập nhật', 'success': False}), 404



@app.route("/cart")
def cart():
    cart = {
        'total_quantity': sum(item['quantity'] for item in session.get('cart', {}).values()),
        'total_amount': sum(item['price'] * item['quantity'] for item in session.get('cart', {}).values())
    }
    return render_template('cart.html', cart=cart)

@app.route('/api/add-cart', methods=['post'])
def add_to_cart():
    data = request.json

    # Kiểm tra dữ liệu đầu vào
    if 'id' not in data or 'name' not in data or 'price' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    key = app.config.get('CART_KEY')
    if not key:
        return jsonify({'error': 'CART_KEY not found'}), 500

    cart = session.get(key, {})

    id = str(data['id'])
    name = data['name']
    price = data['price']

    # Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
    if id not in cart:
        cart[id] = {
            "id": id,
            "name": name,
            "price": price,
            "quantity": 1  # Khởi tạo số lượng là 1 nếu chưa có sản phẩm
        }
    else:
        # Kiểm tra xem thuộc tính 'quantity' có tồn tại hay không
        if 'quantity' not in cart[id]:
            cart[id]['quantity'] = 1  # Nếu chưa có, khởi tạo quantity = 1
        else:
            cart[id]['quantity'] += 1  # Nếu có, tăng số lượng

    session[key] = cart

    # Kiểm tra kết quả của hàm cart_stats
    try:
        cart_stats = utils.cart_stats(cart)
    except Exception as e:
        return jsonify({'error': 'Error in cart_stats: {}'.format(str(e))}), 500

    return jsonify(cart_stats)

@app.route('/api/update-cart', methods=['PUT'])
def update_cart():
    data = request.json

    # Kiểm tra dữ liệu đầu vào
    if not data or 'id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        key = app.config.get('CART_KEY')
        if not key:
            return jsonify({'error': 'CART_KEY not found'}), 500

        # Lấy thông tin giỏ hàng từ session
        cart = session.get(key, {})
        product_id = str(data['id'])
        quantity = int(data['quantity'])

        # Kiểm tra xem sản phẩm có trong giỏ hàng không
        if product_id in cart:
            if quantity > 0:
                cart[product_id]['quantity'] = quantity  # Cập nhật số lượng
            else:
                del cart[product_id]  # Nếu quantity <= 0, xóa sản phẩm khỏi giỏ
        else:
            return jsonify({'error': 'Product not found in cart'}), 404

        # Lưu giỏ hàng cập nhật lại vào session
        session[key] = cart
        session.modified = True  # Đảm bảo session được đánh dấu là đã thay đổi

        # Cập nhật lại thông tin giỏ hàng
        cart_stats_info = utils.cart_stats(cart)

    except ValueError:
        return jsonify({'error': 'Invalid quantity value'}), 400
    except KeyError:
        return jsonify({'error': 'Product data missing in cart'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

    return jsonify(cart_stats_info)

@app.route('/api/delete-cart', methods=['POST'])
def delete_cart():
    data = request.json

    # Kiểm tra dữ liệu đầu vào
    if 'id' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    key = app.config.get('CART_KEY')
    if not key:
        return jsonify({'error': 'CART_KEY not found'}), 500

    cart = session.get(key, {})
    id = str(data['id'])

    # Kiểm tra xem sản phẩm có trong giỏ hàng không
    if id in cart:
        del cart[id]  # Xóa sản phẩm khỏi giỏ hàng
    else:
        return jsonify({'error': 'Product not found in cart'}), 404

    session[key] = cart

    # Cập nhật lại thông tin giỏ hàng
    try:
        cart_stats = utils.cart_stats(cart)
    except Exception as e:
        return jsonify({'error': 'Error in cart_stats: {}'.format(str(e))}), 500

    return jsonify(cart_stats)


@app.route('/checkout')
@login_required
def checkout():
    cart_data = session.get('cart', {})
    total_amount = sum(item['price'] * item['quantity'] for item in cart_data.values())
    total_quantity = sum(item['quantity'] for item in cart_data.values())

    cart_summary = {
        'total_amount': total_amount,
        'total_quantity': total_quantity,

        'items': list(cart_data.values())
    }

    if not cart_data:
        return redirect(url_for('cart'))
    return render_template('checkout.html', cart=cart_summary)


@app.route('/api/place-order', methods=['POST'])
@login_required
def place_order():

    data = request.json
    customer_info = data.get('customer_info')
    payment_method = data.get('payment_method')


    # Kiểm tra cơ bản các trường bắt buộc
    if not customer_info or not payment_method:
        # Nếu customer_info hoặc payment_method không tồn tại
        print("Lỗi: customer_info hoặc payment_method trống.")
        return jsonify({'success': False,
                        'message': 'Dữ liệu đơn hàng không đầy đủ (thiếu thông tin khách hàng hoặc phương thức thanh toán).'}), 400

    # Kiểm tra thêm các trường trong customer_info
    required_customer_fields = ['full_name', 'phone', 'address']
    for field in required_customer_fields:
        if field not in customer_info or not customer_info[field]:
            print(f"Lỗi: Thiếu hoặc trống trường '{field}' trong customer_info.")
            return jsonify({'success': False, 'message': f'Vui lòng điền đầy đủ {field.replace("_", " ")}.'}), 400


    cart_items = session.get('cart', {})
    if not cart_items:
        return jsonify({'success': False, 'message': 'Giỏ hàng trống, không thể đặt hàng.'}), 400
    calculated_total_amount = sum(item['price'] * item['quantity'] for item in cart_items.values())

    try:
        order = Order(


            user_id=current_user.id if current_user.is_authenticated else None,  # Xử lý khách vãng lai
            delivery_address=customer_info['address'],
            notes=customer_info.get('notes', None),  # Dùng .get() để tránh lỗi nếu notes không có
            total_amount=calculated_total_amount,
            payment_method=payment_method,
            order_date=datetime.now(timezone.utc),
            status='Pending',
            delivery_fee=0.00,  # Nếu có default trong model, không cần gán ở đây trừ khi muốn giá trị khác
            payment_status='Unpaid'  # Tương tự
        )
        db.session.add(order)
        db.session.flush()  # Rất quan trọng để có order.id

        for item_data in cart_items.values():
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['id'],
                quantity=item_data['quantity'],
                price_at_order=item_data['price'],
                item_total=item_data['quantity'] * item_data['price']
            )
            db.session.add(order_item)

        db.session.commit()
        session.pop('cart', None)  # Xóa giỏ hàng sau khi đặt thành công

        return jsonify(
            {'success': True,
             'message': 'Đặt hàng thành công!',
             'order_id': order.id}  # Trả về ID của đơn hàng
        )

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi lưu đơn hàng: {e}")  # Debug lỗi chi tiết hơn
        # Để dễ debug hơn trong môi trường dev, bạn có thể trả về lỗi chi tiết
        # return jsonify({'success': False, 'message': f'Lỗi hệ thống khi đặt hàng: {e}'}), 500
        return jsonify({'success': False, 'message': 'Lỗi hệ thống khi đặt hàng. Vui lòng thử lại.'}), 500
@app.route('/order-confirmation/<string:order_id>')
@login_required # Đảm bảo chỉ người dùng đã đăng nhập mới có thể xem đơn hàng của họ
def order_confirmation(order_id):

    try:
        order_details = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    except Exception as e:
        # Xử lý trường hợp order_id không phải là số nguyên khi cố gắng query bằng id
        print(f"Lỗi khi truy vấn đơn hàng với ID: {order_id}. Có thể ID không hợp lệ. {e}")
        return "ID đơn hàng không hợp lệ.", 400


    if not order_details:
       # Nếu không tìm thấy đơn hàng hoặc người dùng hiện tại không phải chủ sở hữu
       return "Đơn hàng không tồn tại hoặc bạn không có quyền truy cập.", 404

    # Truyền đối tượng Order thực tế từ database vào template
    # KHÔNG GIẢ LẬP DỮ LIỆU Ở ĐÂY NỮA
    return render_template('order_confirmation.html', order=order_details)


@app.route('/admin/login', methods=['post'])
def admin_login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = utils.check_login(email=email, password=password)
    if user:
        login_user(user)

    return redirect('/admin')

if __name__ == '__main__':

    from appSale.admin import *
    app.run(debug=True, port=4900)
