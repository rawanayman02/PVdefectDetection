from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import send_from_directory
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from forms import LoginForm, ContactForm ,RegistrationForm
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer
import re
import random
from email.message import EmailMessage
import smtplib

app = Flask(__name__)
app.secret_key = 'your_secret_key_should_be_strong_and_secret'

# Configure upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                
                is_verified INTEGER DEFAULT 0
                
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS reports (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                 report TEXT,
                 pdf_path TEXT,
                original_image TEXT,
                output_image TEXT,
    
                customer_name TEXT,
                customer_email TEXT,
                 address TEXT,
    
                sample_type TEXT,
                serial_no TEXT,
                model TEXT,
                received_date TEXT,
    
                test_location TEXT,
                test_date TEXT,
                devices TEXT,
    
                f_number TEXT,
                iso TEXT,
                shutter TEXT,
    
                lab_manager TEXT,
                 reviewed_by TEXT,
                prepared_by TEXT,

                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
)''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    uploaded_image TEXT,
    output_image TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

    ''')
    conn.commit()
    conn.close()



serializer = URLSafeTimedSerializer(app.secret_key)

def generate_confirmation_token(email):
    return serializer.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=3600):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=expiration)
    except:
        return False
    return email
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.message import EmailMessage

serializer = URLSafeTimedSerializer(app.secret_key)

def generate_confirmation_token(email):
    return serializer.dumps(email, salt='email-confirm')


import sqlite3

def get_db_connection():
    conn = sqlite3.connect('users.db')  # اسم قاعدة البيانات
    conn.row_factory = sqlite3.Row         # عشان نقدر نتعامل مع النتائج بالأسماء مش بالأندكس
    return conn




def generate_verification_code():
    return str(random.randint(10000, 99999))  # يولد كود عشوائي مكون من 5 أرقام


def send_verification_code(user_email, code):
    msg = EmailMessage()
    msg.set_content(f'Your verification code is: {code}')
    msg['Subject'] = 'Confirm your account'
    msg['From'] = 'solarpanal156@gmail.com'
    msg['To'] = user_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('solarpanal156@gmail.com', 'ttti tmif fvjw qoco')  # غيّر كلمة المرور
        smtp.send_message(msg)
   
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        
        password_regex = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        if not password_regex.match(password):
            flash('Password must be at least 8 characters long, contain an uppercase letter, a number, and a special character.', 'danger')
            return render_template('register.html', form=form)

        try:
            # Check if user already exists
            with sqlite3.connect('users.db') as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM users WHERE email = ? OR name = ?", (email, name))
                existing = c.fetchone()
                if existing:
                    flash('Username or email already exists.', 'danger')
                    return render_template('register.html', form=form)

            # Generate verification code
            verification_code = generate_verification_code()
            send_verification_code(email, verification_code)

            # Store user data temporarily in session
            session['temp_user'] = {
                'name': name,
                'email': email,
                'password': generate_password_hash(password),
                'verification_code': verification_code
            }

            flash('Verification code sent to your email. Please verify to complete registration.', 'info')
            return redirect(url_for('verify_email'))

        except Exception as e:
            flash(f'Registration error: {str(e)}', 'danger')
    
    return render_template('register.html', form=form)





@app.route('/confirm/<token>', methods=['GET', 'POST'])
def confirm_email(token):
    if request.method == 'POST':
        entered_token = request.form['token']
        
        # التحقق من الرمز المدخل
        email = confirm_token(entered_token)
        if email:
            with sqlite3.connect('users.db') as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))
                conn.commit()
            flash('Your account has been verified! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('The confirmation link is invalid or has expired.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('confirm_email.html')  # استعرض نموذج إدخال الرمز


@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        entered_code = request.form['verification_code']

        temp_user = session.get('temp_user')
        if not temp_user:
            flash("Session expired or invalid access. Please register again.", "danger")
            return redirect(url_for('register'))

        if entered_code == temp_user['verification_code']:
            try:
                with sqlite3.connect('users.db') as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO users (name, email, password, is_verified) VALUES (?, ?, ?, 1)",
                              (temp_user['name'], temp_user['email'], temp_user['password']))
                    conn.commit()

                    c.execute("SELECT id FROM users WHERE email = ?", (temp_user['email'],))
                    user_id = c.fetchone()[0]

                session['user_id'] = user_id
                session['username'] = temp_user['name']
                session['email'] = temp_user['email']

                session.pop('temp_user', None)

                flash('Your account has been verified and you are now logged in!', 'success')
                return redirect(url_for('index'))  # ✅ يفتح الصفحة الرئيسية

            except sqlite3.IntegrityError:
                flash('Account already exists.', 'danger')
            except Exception as e:
                flash(f'Error verifying account: {str(e)}', 'danger')
        else:
            flash('Invalid verification code. Please try again.', 'danger')

    return render_template('verify_email.html')





@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        with sqlite3.connect('users.db') as conn:
            cursor = conn.execute("SELECT id, name, password, is_verified FROM users WHERE email = ?", (email,))

            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                if user[3] == 0:  # إذا لم يتم التحقق من البريد الإلكتروني
                    flash('Please verify your email before logging in.', 'danger')
                    return redirect(url_for('login'))
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)


# التحقق مما إذا كانت الدالة generate_report ترجع قيمتين كما هو متوقع
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
import os
from werkzeug.utils import secure_filename
from models import report_generator  # تأكد إنه موجود في models
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('You must be logged in to upload an image.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')  # 'analyze_report' or 'quick_result'
        user_id = session.get('user_id')

        image_path = None
        filename = None

        # لو جاي من الفورم الأول (رفع صورة)
        if 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            # احفظ في السيشن
            session['uploaded_image_path'] = f"uploads/{filename}"
        elif 'uploaded_image_path' in session:
            image_path = session.get('uploaded_image_path')
            filename = os.path.basename(image_path)
        else:
            flash("No image selected.", "danger")
            return redirect(url_for('upload'))

        # تحليل سريع
        if action == 'quick_result':
            image_path = session.get('uploaded_image_path')
            if not image_path:
                flash("No image found in session. Please upload an image first.", "danger")
                return redirect(url_for('upload'))

            image_full_path = os.path.join('static', image_path)

            from models import report_generator
            try:
                report_text, pdf_bytes, original_image_path, processed_image_path = report_generator.generate_report(image_full_path)
                processed_image_path = processed_image_path.replace('\\', '/')
                if 'static/' in processed_image_path:
                    processed_image_path = processed_image_path.split('static/', 1)[-1]
            except Exception as e:
                flash(f"Model error: {e}", 'danger')
                return redirect(url_for('upload'))

            with sqlite3.connect('users.db') as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO results (user_id, uploaded_image, output_image)
                    VALUES (?, ?, ?)
                ''', (
                    user_id,
                    image_path,
                    processed_image_path
                ))
                conn.commit()

            return redirect(url_for('results'))

        # تحليل كامل وتوليد تقرير
        if action == 'analyze_report':
            image_path = session.get('uploaded_image_path')
            if not image_path:
                flash("No image found in session. Please upload an image first.", "danger")
                return redirect(url_for('upload'))

            image_full_path = os.path.join('static', image_path)

            from models import report_generator
            try:
                report_text, pdf_bytes, original_image_path, processed_image_path = report_generator.generate_report(image_full_path)
                processed_image_path = processed_image_path.replace('\\', '/')
                if 'static/' in processed_image_path:
                    processed_image_path = processed_image_path.split('static/', 1)[-1]
            except Exception as e:
                flash(f"Model error: {e}", 'danger')
                return redirect(url_for('upload'))

            with sqlite3.connect('users.db') as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO results (user_id, uploaded_image, output_image)
                    VALUES (?, ?, ?)
                ''', (
                    user_id,
                    image_path,
                    processed_image_path
                ))
                conn.commit()

            # بيانات التقرير
            customer_name = request.form.get('customer_name')
            address = request.form.get('customer_address')
            customer_email = request.form.get('customer_email')
            sample_type = request.form.get('sample_type')
            serial_no = request.form.get('serial_no')
            model_name = request.form.get('model')
            received_date = request.form.get('received_date')
            test_location = request.form.get('test_location')
            test_date = datetime.now().strftime("%Y-%m-%d")
            devices = request.form.get('used_devices')
            f_number = request.form.get('f_number')
            iso = request.form.get('iso')
            shutter = request.form.get('shutter_speed')
            lab_manager = request.form.get('lab_manager')
            reviewed_by = request.form.get('reviewed_by')
            prepared_by = request.form.get('prepared_by')

            # إنشاء PDF
            pdf_filename = f"{os.path.basename(image_path).rsplit('.', 1)[0]}_report.pdf"
            pdf_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

            with open(pdf_file_path, 'wb') as f:
                f.write(pdf_bytes)

            # خزن في reports
            report_id = None
            with sqlite3.connect('users.db') as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO reports (
                        user_id, report, pdf_path, original_image, output_image, customer_name, customer_email, address,
                        sample_type, serial_no, model, received_date,
                        test_location, test_date, devices,
                        f_number, iso, shutter, lab_manager, reviewed_by, prepared_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                ''', (
                    user_id, report_text, f"uploads/{pdf_filename}", image_path, processed_image_path, customer_name, customer_email, address,
                    sample_type, serial_no, model_name, received_date,
                    test_location, test_date, devices,
                    f_number, iso, shutter, lab_manager, reviewed_by, prepared_by
                ))
                report_id = c.lastrowid

            # امسح الصورة من السيشن
            session.pop('uploaded_image_path', None)

            return render_template('report.html',
                                   report=report_text,
                                   image_path=processed_image_path,
                                   original_image_path=image_path,
                                   pdf_file_path=f"uploads/{pdf_filename}",
                                   customer_name=customer_name,
                                   address=address,
                                   customer_email=customer_email,
                                   sample_type=sample_type,
                                   serial_no=serial_no,
                                   model=model_name,
                                   received_date=received_date,
                                   test_location=test_location,
                                   test_date=test_date,
                                   devices=devices,
                                   f_number=f_number,
                                   iso=iso,
                                   shutter=shutter,
                                   lab_manager=lab_manager,
                                   reviewed_by=reviewed_by,
                                   prepared_by=prepared_by,
                                   report_id=report_id,
                                   current_date=datetime.now().strftime("%Y-%m-%d"))

    return render_template('upload.html')

@app.route('/clear_image')
def clear_image():
    session.pop('uploaded_image_path', None)
    return '', 204  # No content


from flask import jsonify
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        image = request.files.get('image')

        # لو مفيش صورة مرفوعة لكن في صورة محفوظة في السيشن
        if not image and request.form.get('use_session_image') == '1':
            image_path = session.get('uploaded_image_path')
            if not image_path:
                return jsonify({'error': 'No image found in session.'}), 400

            full_image_path = os.path.join('static', image_path)
            if not os.path.exists(full_image_path):
                return jsonify({'error': 'Image not found on server.'}), 404

            # تحليل الصورة باستخدام الدالة السريعة
            defects, score = report_generator.quick_analysis(full_image_path)
            return jsonify({'defects': defects, 'score': score})

        # لو في صورة جديدة مرفوعة
        elif image:
            filename = secure_filename(image.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(save_path)

            # حفظ مسار الصورة في السيشن
            session['uploaded_image_path'] = f"uploads/{filename}"

            defects, score = report_generator.quick_analysis(save_path)
            return jsonify({'defects': defects, 'score': score})

        else:
            return jsonify({'error': 'No image provided.'}), 400

    except Exception as e:
        print(f"Error in /analyze: {e}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

import sqlite3
from datetime import datetime






import sqlite3
from datetime import datetime

def save_report(user_id, report, pdf_path, original_image):
    """
    Save the generated report to the database.

    :param user_id: ID of the user to whom the report belongs.
    :param report: The generated report content.
    :param pdf_path: Path to the generated PDF.
    :param original_image: Path to the original image used for report generation.
    """
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Insert the report into the reports table
    c.execute('''INSERT INTO reports (user_id, report, pdf_path, original_image)
                 VALUES (?, ?, ?, ?)''', (user_id, report, pdf_path, original_image))

    conn.commit()
    conn.close()

def get_user_reports(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    try:
        # Get report ID + info + created_at
        c.execute('''SELECT id, report, pdf_path, original_image, output_image, created_at FROM reports WHERE user_id = ?''', (user_id,))
        reports = c.fetchall()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        reports = []  # في حالة حدوث خطأ، نرجع قائمة فارغة
    
    finally:
        conn.close()
    
    return reports

@app.route('/results')
def results():
    if 'user_id' not in session:
        flash("Please login to view your results.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    with sqlite3.connect('users.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT * FROM results 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (user_id,))
        result = c.fetchone()

    return render_template('results.html', result=result)







@app.route('/view_report/<int:report_id>')
def view_report(report_id):
    if 'user_id' not in session:
        flash("Please log in to view reports.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # جلب بيانات التقرير
    c.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()

    if not report:
        conn.close()
        flash("Report not found.", "danger")
        return redirect(url_for('profile'))

  
    conn.close()

    return render_template('view_report.html',
        report=report["report"],
        image_path=report["output_image"],
        original_image_path=report["original_image"],
        pdf_file_path=report["pdf_path"],
        sample_type=report["sample_type"],
        model=report["model"],
        received_date=report["received_date"],
        test_location=report["test_location"],
        test_date=report["test_date"],
        devices=report["devices"],
        f_number=report["f_number"],
        iso=report["iso"],
        shutter=report["shutter"],
        address=report["address"],
        customer_name=report["customer_name"],
        customer_email=report["customer_email"],
        lab_manager=report["lab_manager"],
        reviewed_by=report["reviewed_by"],
        prepared_by=report["prepared_by"],
        serial_no=report["serial_no"],
         
        report_id=report_id,
        current_date=report["test_date"]  
        # نفس التاريخ كـ current_date
    )



@app.route('/delete_report/<int:report_id>', methods=['POST'])
def delete_report(report_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get the report from DB
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT user_id, pdf_path, original_image, output_image FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()

    if report and report[0] == session['user_id']:
        # Delete files
        for file_path in [report[1], report[2], report[3]]:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

        # Delete record from DB
        c.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('profile'))


@app.route('/report')
def report():

    return render_template('report.html')



@app.route('/logout')
def logout():
    session.clear()  # مسح جميع بيانات الجلسة
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))  # تحويل المستخدم إلى الصفحة الرئيسية بعد تسجيل الخروج


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/read_more')
def read_more():
    return render_template('about.html')

@app.route('/feature')
def feature():
    return render_template('feature.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        user_email = form.email.data
        subject = form.subject.data
        message = form.message.data

        # محتوى الرسالة
        email_body = f"""
        You've received a new message from the contact form:

        Name: {name}
        Email: {user_email}
        Subject: {subject}

        Message:
        {message}
        """

        try:
            msg = EmailMessage()
            msg.set_content(email_body)
            msg['Subject'] = f"[Contact Form] {subject}"
            msg['From'] = 'solarpanal156@gmail.com'  # ثابت (بريد الشركة)
            msg['To'] = 'solarpanal156@gmail.com'
            msg['Reply-To'] = user_email  # ✅ عشان لما يرد عليه يوصل للمستخدم

            # إرسال الإيميل
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('solarpanal156@gmail.com', 'كلمة_مرور_AppPassword')  # استخدمي App Password
                smtp.send_message(msg)

            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))

        except Exception as e:
            flash(f'Error sending message: {e}', 'danger')

    return render_template('contact.html', form=form)
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # إذا كان المستخدم غير مسجل دخول، يتم تحويله لتسجيل الدخول
    
    user_id = session['user_id']
    reports = get_user_reports(user_id)  # جلب تقارير المستخدم من قاعدة البيانات


    
    sort_order = request.args.get('sort', 'desc')  # default: newest first

    if sort_order == 'asc':
        order_by = 'created_at ASC'
    else:
        order_by = 'created_at DESC'

    conn = get_db_connection()
    reports = conn.execute(
        f'''
        SELECT id, report, pdf_path, original_image, output_image, created_at
        FROM reports
        WHERE user_id = ?
        ORDER BY {order_by}
        ''',
        (session['user_id'],)
    ).fetchall()
    conn.close()

    return render_template('profile.html', reports=reports)  # عرض التقارير في صفحة البروفايل





@app.route('/404')
@app.errorhandler(404)
def not_found_page(e=None):
    message = "Page not found" if e else "This is a test 404 page"
    return render_template('404.html', message=message), 404 if e else 200

@app.route('/terms')
def terms():
    return render_template('terms.html')  # Make sure you have a 'terms.html' template
@app.route('/support')
def support():
    return render_template('support.html')  # Requires support.html in templates/
if __name__ == '__main__':
    init_db()
    app.run(port=5000, debug=True)
