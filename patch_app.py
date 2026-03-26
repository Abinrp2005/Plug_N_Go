import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# STEP 1: Replace TOP SECTION
top_section = """from flask import (
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

models_section = """
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

admin_decorator = """def admin_required(f):
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

min_routes = """@app.route('/login',
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

bottom_section = """if __name__ == '__main__':
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

# ---------------------------------------------------------
# REGEX REPLACEMENTS
# ---------------------------------------------------------

# 1. Top Section
content = re.sub(r"^.*?@app\.context_processor\s+def\s+inject_globals\(\):\s+.*?return\s+dict\(\s*request=request,\s*current_user=current_user\s*\)", top_section, content, flags=re.DOTALL)

# Insert models right after inject_globals()
content = content.replace(top_section, top_section + "\\n\\n" + models_section + "\\n")

# Remove old models import
content = re.sub(r"^from models import .*?$", "", content, flags=re.MULTILINE)

# Remove old 'def admin_required'
content = re.sub(r"^def admin_required.*?return decorated_function$", admin_decorator, content, flags=re.MULTILINE | re.DOTALL)

# Remove old login route
content = re.sub(r"^@app\.route\('/login'.*?return render_template\('login\.html'\)", "", content, flags=re.MULTILINE | re.DOTALL)

# Remove old register route
content = re.sub(r"^@app\.route\('/register'.*?return render_template\('register\.html'\)", "", content, flags=re.MULTILINE | re.DOTALL)

# Remove old logout route
content = re.sub(r"^@app\.route\('/logout'.*?return redirect\(url_for\('login'\)\)", "", content, flags=re.MULTILINE | re.DOTALL)

# Remove old index route
content = re.sub(r"^@app\.route\(\"\/\"\)\s+@login_required\s+def index\(\):.*?return render_template\(\s*\"index\.html\".*?\)", "", content, flags=re.MULTILINE | re.DOTALL)

# Insert the requested routes right before the bottom section matches
# Find the start of the bottom section
bottom_idx = content.find("if __name__ == '__main__':")
content = content[:bottom_idx] + min_routes + "\\n\\n" + bottom_section + "\\n"

# Remove references to Notification in app.before_request (check_expired_bookings) and check_timeouts and bookings
content = re.sub(r"^@app\.before_request\s*def check_expired_bookings\(\):.*?pass", "", content, flags=re.MULTILINE | re.DOTALL)
content = re.sub(r"^db_initialized = False.*?db\.session\.commit\(\)", "", content, flags=re.MULTILINE | re.DOTALL)
content = re.sub(r"^def initialize_database\(\):.*?pass\s+", "", content, flags=re.MULTILINE | re.DOTALL)

# Remove any Admin.query references entirely to avoid NameError since Admin no longer exists (use User with is_admin)
content = content.replace('Admin.query', 'User.query.filter_by(is_admin=True)')

# Admin login/logout can just redirect or check User
content = content.replace('Admin.email', 'User.email')
content = content.replace('Admin.username', 'User.name') # Assuming username maps to name

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patching complete!")
