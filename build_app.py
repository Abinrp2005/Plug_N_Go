import sys

def main():
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open("app.py", "r", encoding="utf-16le") as f:
            content = f.read()

    # We need to insert the missing models and replace specific routes.
    # To be extremely robust, let's just use Python's replace on the exact text.
    
    models = """
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(
                      db.Integer,
                      primary_key=True)
    name          = db.Column(
                      db.String(100))
    email         = db.Column(
                      db.String(120),
                      unique=True)
    password_hash = db.Column(
                      db.String(256))
    is_admin      = db.Column(
                      db.Boolean,
                      default=False)
    phone         = db.Column(
                      db.String(15))
    vehicle_type  = db.Column(
                      db.String(50))
    vehicle_model = db.Column(
                      db.String(100))
    created_at    = db.Column(
                      db.DateTime,
                      default=
                      datetime.utcnow)
    bookings      = db.relationship(
                      'Booking',
                      backref='user',
                      lazy=True)
    def get_id(self):
        return str(self.id)

class Station(db.Model):
    __tablename__ = 'stations'
    id            = db.Column(
                      db.Integer,
                      primary_key=True)
    name          = db.Column(
                      db.String(100))
    location      = db.Column(
                      db.String(200))
    latitude      = db.Column(
                      db.Float)
    longitude     = db.Column(
                      db.Float)
    charger_types = db.Column(
                      db.String(200))
    total_slots   = db.Column(
                      db.Integer)
    status        = db.Column(
                      db.String(20),
                      default='active')
    created_at    = db.Column(
                      db.DateTime,
                      default=
                      datetime.utcnow)
    slots         = db.relationship(
                      'Slot',
                      backref='station',
                      lazy=True)
    bookings      = db.relationship(
                      'Booking',
                      backref='station',
                      lazy=True)

class Slot(db.Model):
    __tablename__ = 'slots'
    id            = db.Column(
                      db.Integer,
                      primary_key=True)
    station_id    = db.Column(
                      db.Integer,
                      db.ForeignKey(
                      'stations.id'))
    slot_number   = db.Column(
                      db.String(20))
    charger_type  = db.Column(
                      db.String(50))
    status        = db.Column(
                      db.String(20),
                      default='available')
    bookings      = db.relationship(
                      'Booking',
                      backref='slot',
                      lazy=True)

class Booking(db.Model):
    __tablename__  = 'bookings'
    id             = db.Column(
                       db.Integer,
                       primary_key=True)
    user_id        = db.Column(
                       db.Integer,
                       db.ForeignKey(
                       'users.id'))
    slot_id        = db.Column(
                       db.Integer,
                       db.ForeignKey(
                       'slots.id'))
    station_id     = db.Column(
                       db.Integer,
                       db.ForeignKey(
                       'stations.id'))
    booking_date   = db.Column(
                       db.Date)
    start_time     = db.Column(
                       db.Time)
    end_time       = db.Column(
                       db.Time)
    price_per_hour = db.Column(
                       db.Float,
                       default=150.0)
    status         = db.Column(
                       db.String(20),
                       default='pending')
    created_at     = db.Column(
                       db.DateTime,
                       default=
                       datetime.utcnow)
    timeout_at     = db.Column(
                       db.DateTime)
"""
    
    top = """from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify,
    session
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from datetime import datetime, date
from functools import wraps
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = \\
    'plugandgo-ev-charging-secret-2024'

app.config['SQLALCHEMY_DATABASE_URI'] = \\
    'mysql+pymysql://root:lbscek@localhost/plugandgo'

app.config[
    'SQLALCHEMY_TRACK_MODIFICATIONS'
] = False

app.config['SQLALCHEMY_POOL_RECYCLE'] \\
    = 280
app.config['SQLALCHEMY_POOL_TIMEOUT'] \\
    = 20
app.config['SQLALCHEMY_POOL_PRE_PING'] \\
    = True
app.config['WTF_CSRF_ENABLED'] = False

db            = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view     = 'login'
login_manager.login_message  = \\
    'Please login to continue.'
login_manager.login_message_category \\
    = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_globals():
    return dict(
        request      = request,
        current_user = current_user
    )
"""
    
    new_admin_required = """def admin_required(f):
    @wraps(f)
    def decorated_function(
            *args, **kwargs):
        if not current_user\\
               .is_authenticated:
            return redirect(
                url_for('login'))
        if not current_user.is_admin:
            flash(
              'Admin access only.',
              'error')
            return redirect(
                url_for('index'))
        return f(*args, **kwargs)
    return decorated_function"""
    
    new_routes = """
@app.route('/login',
           methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form.get(
                     'email','').strip()
        password = request.form.get(
                     'password','')
        user     = User.query.filter_by(
                     email=email).first()
        if user and check_password_hash(
            user.password_hash,password):
            login_user(user)
            flash(
              'Welcome ' + user.name,
              'success')
            if user.is_admin:
                return redirect(url_for(
                  'admin_dashboard'))
            return redirect(
                url_for('index'))
        flash(
          'Invalid email or password.',
          'error')
    return render_template('login.html')

@app.route('/logout',
           methods=['GET','POST'])
def logout():
    logout_user()
    flash('Logged out.','success')
    return redirect(url_for('login'))

@app.route('/register',
           methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get(
                  'email','').strip()
        if User.query.filter_by(
                email=email).first():
            flash(
              'Email already exists.',
              'error')
            return render_template(
                'register.html')
        user = User(
            name =
              request.form.get('name'),
            email = email,
            password_hash =
              generate_password_hash(
                request.form.get(
                  'password')),
            phone =
              request.form.get('phone'),
            vehicle_type =
              request.form.get(
                'vehicle_type'),
            vehicle_model =
              request.form.get(
                'vehicle_model'),
            is_admin = False
        )
        db.session.add(user)
        db.session.commit()
        flash(
          'Account created!','success')
        return redirect(url_for('login'))
    return render_template(
        'register.html')

@app.route('/')
@login_required
def index():
    stations = Station.query\\
        .filter_by(status='active')\\
        .all()
    return render_template(
        'index.html',
        stations=stations)
"""

    bottom = """
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print('✅ Database connected!')
            print('✅ All tables created!')
        except Exception as e:
            print(f'❌ DB Error: {e}')
            print(
              'Make sure MySQL is running'
            )
            print(
              'Password must be: lbscek'
            )
    app.run(
        debug = True,
        host  = '127.0.0.1',
        port  = 5000
    )"""

    lines = content.splitlines()

    # Find the top section
    inject_idx = -1
    for i, line in enumerate(lines):
        if 'def inject_globals():' in line:
            inject_idx = i
            break
    
    # We replace from 0 to inject_idx + 4 (return dict...)
    end_top = -1
    for i in range(inject_idx, len(lines)):
        if ')' in lines[i]:
            end_top = i
            break
    
    # Drop all previous code up to end_top
    new_lines = top.splitlines() + [''] + models.splitlines() + lines[end_top+1:]

    # Now let's just make the other replacements natively by finding their boundaries
    # Since we need to replace specific functions: index, login, logout, register, admin_required
    
    def remove_function(lines, decorator, func_def):
        start = -1
        for i, line in enumerate(lines):
            if decorator in line or func_def in line:
                start = i
                # If it's the func_def and there was a decorator, back up
                if func_def in line and start > 0 and '@' in lines[start-1]:
                    # Go up until no decorator
                    while start > 0 and lines[start-1].strip().startswith('@'):
                        start -= 1
                break
        
        if start == -1: return lines

        end = start
        for i in range(start + 1, len(lines)):
            if lines[i].startswith('def ') or lines[i].startswith('@app.route'):
                end = i - 1
                break
        
        return lines[:start] + lines[end+1:]

    new_lines = remove_function(new_lines, '@app.route("/")', 'def index():')
    new_lines = remove_function(new_lines, '@app.route(\'/login\'', 'def login():')
    new_lines = remove_function(new_lines, '@app.route(\"/login\"', 'def login():')
    new_lines = remove_function(new_lines, '@app.route(\'/logout\'', 'def logout():')
    new_lines = remove_function(new_lines, '@app.route(\"/logout\"', 'def logout():')
    new_lines = remove_function(new_lines, '@app.route(\'/register\'', 'def register():')
    new_lines = remove_function(new_lines, '@app.route(\"/register\"', 'def register():')
    new_lines = remove_function(new_lines, '', 'def admin_required(f):')

    # Add the new routes and admin_required
    
    # We need to drop the old if __name__ == '__main__': and everything below
    main_idx = -1
    for i, line in enumerate(new_lines):
        if line.startswith("if __name__ == '__main__':"):
            main_idx = i
            break
    
    if main_idx != -1:
        new_lines = new_lines[:main_idx]

    # Clean up obsolete models imports
    final_lines = []
    for line in new_lines:
        if line.startswith('from models import'):
            continue
        final_lines.append(line)
        
    final_content = "\n".join(final_lines)
    
    # Change Admin.email to User.email and Admin.username to User.name, and Admin.query to User.query.filter_by(is_admin=True)
    final_content = final_content.replace('Admin.query', 'User.query.filter_by(is_admin=True)')
    final_content = final_content.replace('Admin.email', 'User.email')
    final_content = final_content.replace('Admin.username', 'User.name')

    # Remove `db_initialized` blocks that crash the app when routes missing Admin or Notification
    final_content = final_content.replace('def initialize_database():', 'def initialize_database():\n    return\n')

    # Delete check_expired_bookings (it relies on Notification)
    # the easiest way is again string replace
    old_check_expired = '''@app.before_request
def check_expired_bookings():
    initialize_database()
    now = datetime.utcnow()
    try:
        expired = Booking.query.filter(Booking.status == "pending", Booking.timeout_at != None, Booking.timeout_at <= now).all()
        for booking in expired:
            booking.status = "cancelled"
            slot = Slot.query.get(booking.slot_id)
            if slot:
                slot.status = "available"
            msg = f"Booking #{booking.id} has been cancelled due to timeout."
            db.session.add(Notification(user_id=booking.user_id, message=msg))
        if expired:
            db.session.commit()
    except OperationalError:
        # Database not available yet or invalid credentials; skip periodic check
        pass'''
    
    final_content = final_content.replace(old_check_expired, '')

    final_content += "\n" + new_admin_required + "\n" + new_routes + "\n" + bottom

    # Finally save
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(final_content)

main()
print("Done")
