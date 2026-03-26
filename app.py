from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify,
    session, g
)
from flask_login import (
    login_user, logout_user,
    login_required, current_user
)
from flask_mail import Message
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from sqlalchemy import func, case, or_, and_
from sqlalchemy.exc import OperationalError
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, timedelta, date
from functools import wraps
import os
import re
from itsdangerous import URLSafeTimedSerializer

from extensions import db, login_manager, mail
from models import User, Admin, Station, Slot, Booking, Notification

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'plugandgo-ev-charging-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://root:lbscek@localhost/plugandgo'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20
app.config['SQLALCHEMY_POOL_PRE_PING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@plugandgo.local')

db.init_app(app)
mail.init_app(app)
csrf = CSRFProtect(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to continue.'
login_manager.login_message_category = 'warning'

# Models and user_loader are now imported from models.py

# Station model moved to models.py

# Slot model moved to models.py

# Booking model moved to models.py
# Models are now in models.py




def initialize_database():
    global db_initialized
    if db_initialized:
        return
    try:
        db.create_all()
        db_initialized = True
# Seeding is handled via separate scripts
    except OperationalError:
        pass



@app.route("/stations")
@login_required
def stations():
    initialize_database()
    try:
        stations = Station.query.filter_by(status="active").all()
        stations = [
            {
                'id': s.id,
                'name': s.name,
                'location': s.location,
                'latitude': s.latitude,
                'longitude': s.longitude,
                'charger_types': s.charger_types,
                'total_slots': s.total_slots,
                'status': s.status,
            }
            for s in stations
        ]
    except OperationalError:
        stations = []
    return render_template("stations.html", stations=stations)

@app.route("/api/stations/availability")
def api_stations_availability():
    try:
        stations = Station.query.filter_by(status="active").all()
        out = []
        for station in stations:
            available = Slot.query.filter_by(station_id=station.id, status="available").count()
            out.append({
                "id": station.id,
                "name": station.name,
                "location": station.location,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "charger_types": station.charger_types,
                "total_slots": station.total_slots,
                "available_slots": available,
                "status": station.status,
            })
        return jsonify(out)
    except OperationalError:
        return jsonify([]), 503

@app.route('/api/bookings/timeout')
@login_required
def check_timeouts():
    try:
        now = datetime.utcnow()
        expired = Booking.query.filter(Booking.status == 'pending', Booking.timeout_at != None, Booking.timeout_at <= now).all()
        for booking in expired:
            booking.status = 'cancelled'
            slot = Slot.query.get(booking.slot_id)
            if slot:
                slot.status = 'available'
            db.session.add(Notification(user_id=booking.user_id, message=f"Booking #{booking.id} cancelled due to timeout"))
        if expired:
            db.session.commit()
        return jsonify({'status': 'success', 'count': len(expired)})
    except OperationalError:
        return jsonify({'status': 'error'}), 503

@app.route('/test-db')
def test_db():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'success', 'message': 'Database connected âœ…'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stations/search', methods=['GET'])
def search_stations():
    query = request.args.get('q', '').strip()
    charger_type = request.args.get('charger_type', '').strip()
    available_only = request.args.get('available_only', 'false').lower()
    try:
        stmt = db.session.query(
            Station,
            func.count(case((Slot.status == 'available', 1))).label('available_slots')
        ).outerjoin(Slot).filter(Station.status == 'active')

        if query:
            like_value = f"%{query}%"
            stmt = stmt.filter(or_(Station.name.ilike(like_value), Station.location.ilike(like_value)))

        if charger_type:
            stmt = stmt.filter(Station.charger_types.ilike(f"%{charger_type}%"))

        if available_only == 'true':
            stmt = stmt.filter(Station.slots.any(Slot.status == 'available'))

        stmt = stmt.group_by(Station.id).order_by(Station.name.asc())

        results = stmt.all()
        payload = []
        for station, available_slots in results:
            payload.append({
                'id': station.id,
                'name': station.name,
                'location': station.location,
                'latitude': station.latitude,
                'longitude': station.longitude,
                'charger_types': station.charger_types,
                'total_slots': station.total_slots,
                'available_slots': available_slots,
                'status': station.status,
            })
        return jsonify(payload)
    except OperationalError:
        return jsonify([]), 503

@app.route("/station/<int:station_id>")
def station_detail(station_id):
    station = Station.query.get_or_404(station_id)
    slots = Slot.query.filter_by(station_id=station.id).all()
    available = sum(1 for s in slots if s.status == "available")
    return render_template("station_detail.html", station=station, slots=slots, available=available)

@app.route("/book/<int:station_id>", methods=["GET", "POST"])
@login_required
def book_station(station_id):
    station = Station.query.get_or_404(station_id)
    available_slots = Slot.query.filter_by(station_id=station_id, status="available").all()
    station.available_slots = len(available_slots)

    if request.method == "POST":
        err = validate_booking_form(request.form)
        if err:
            flash(err, "danger")
            return redirect(url_for("book_station", station_id=station_id))

        slot_id = int(request.form.get("slot_id"))
        booking_date = request.form.get("booking_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        try:
            price_per_hour = float(request.form.get("price_per_hour", 20))
        except (TypeError, ValueError):
            flash("Invalid pricing", "danger")
            return redirect(url_for("book_station", station_id=station_id))

        try:
            booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
            start_time_obj = datetime.strptime(start_time, "%H:%M").time()
            end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        except ValueError:
            flash("Invalid date/time format", "danger")
            return redirect(url_for("book_station", station_id=station_id))

        today = datetime.utcnow().date()
        if booking_date_obj < today:
            flash("Bookings cannot be made for past dates", "danger")
            return redirect(url_for("book_station", station_id=station_id))

        if start_time_obj >= end_time_obj:
            flash("Start time must be before end time", "danger")
            return redirect(url_for("book_station", station_id=station_id))

        start_dt = datetime.combine(booking_date_obj, start_time_obj)
        end_dt = datetime.combine(booking_date_obj, end_time_obj)
        if start_dt <= datetime.utcnow():
            flash("Start time must be in the future", "danger")
            return redirect(url_for("book_station", station_id=station_id))

        existing = Booking.query.filter(
            Booking.slot_id == slot_id,
            Booking.booking_date == booking_date_obj,
            Booking.status.in_(["pending", "confirmed"]),
            or_(
                and_(Booking.start_time <= start_time_obj, Booking.end_time > start_time_obj),
                and_(Booking.start_time < end_time_obj, Booking.end_time >= end_time_obj),
                and_(Booking.start_time >= start_time_obj, Booking.end_time <= end_time_obj),
            )
        ).with_for_update().first()

        if existing:
            flash("Selected slot is already booked for this time", "danger")
            return redirect(url_for("book_station", station_id=station_id))

        slot = Slot.query.filter_by(id=slot_id, station_id=station_id).with_for_update().first()
        if not slot or slot.status != "available":
            flash("Slot is not available", "danger")
            return redirect(url_for("book_station", station_id=station_id))

        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        total_price = duration_hours * price_per_hour

        slot.status = "occupied"
        booking = Booking(
            user_id=current_user.id,
            slot_id=slot.id,
            station_id=station_id,
            booking_date=booking_date_obj,
            start_time=start_time_obj,
            end_time=end_time_obj,
            price_per_hour=price_per_hour,
            status="pending",
            created_at=datetime.utcnow(),
            timeout_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.session.add(booking)
        db.session.commit()

        db.session.add(Notification(user_id=current_user.id, message=f"Booking #{booking.id} pending confirmation"))
        db.session.commit()

        flash(f"Booking created as pending for {duration_hours:.2f}h at ${total_price:.2f}. Confirm within 15 minutes.", "success")
        return redirect(url_for("dashboard"))

    return render_template("book_slot.html", station=station, available_slots=available_slots)



@app.route("/booking/confirm/<int:booking_id>")
@login_required
def confirm_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    if booking.status != "pending":
        flash("Only pending bookings can be confirmed", "warning")
        return redirect(url_for("dashboard"))

    if booking.timeout_at and datetime.utcnow() > booking.timeout_at:
        booking.status = "cancelled"
        slot = Slot.query.get(booking.slot_id)
        if slot:
            slot.status = "available"
        db.session.commit()
        flash("Booking timed out and is cancelled", "danger")
        return redirect(url_for("dashboard"))

    booking.status = "confirmed"
    booking.timeout_at = None
    slot = Slot.query.get(booking.slot_id)
    if slot:
        slot.status = "occupied"

    db.session.commit()
    db.session.add(Notification(user_id=current_user.id, message=f"Booking #{booking.id} confirmed."))
    db.session.commit()
    flash("Booking confirmed successfully", "success")
    return redirect(url_for("dashboard"))

@app.route("/booking/cancel/<int:booking_id>")
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    booking_datetime = datetime.combine(booking.booking_date, booking.start_time)
    if datetime.utcnow() >= booking_datetime:
        flash("Cannot cancel booking that has started", "danger")
        return redirect(url_for("dashboard"))

    booking.status = "cancelled"
    slot = Slot.query.get(booking.slot_id)
    if slot:
        slot.status = "available"
    db.session.commit()
    db.session.add(Notification(user_id=current_user.id, message=f"Booking #{booking.id} cancelled."))
    db.session.commit()
    flash("Booking cancelled", "info")
    return redirect(url_for("dashboard"))

def validate_registration_form(form):
    required = ["name", "email", "password", "phone", "vehicle_type", "vehicle_model"]
    for field in required:
        if not form.get(field):
            return f"{field.replace('_', ' ').title()} is required"
    if len(form.get("password")) < 8:
        return "Password must be at least 8 characters"
    if User.query.filter_by(email=form.get("email")).first():
        return "Email already registered"
    return None


def validate_profile_form(form):
    errors = []
    
    # Required basic fields
    required = ["name", "phone", "vehicle_type", "vehicle_model"]
    for field in required:
        if not form.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required.")

    # New fields validation
    license_number = form.get("license_number", "").strip()
    vehicle_number_plate = form.get("vehicle_number_plate", "").strip()

    if not license_number:
        errors.append("License number is required.")

    if vehicle_number_plate and not re.match(r'^[A-Za-z0-9-]+$', vehicle_number_plate):
        errors.append("Vehicle number plate must be alphanumeric.")

    return errors


def validate_booking_form(form):
    required = ["slot_id", "booking_date", "start_time", "end_time"]
    for field in required:
        if not form.get(field):
            return f"{field.replace('_', ' ').title()} is required"
    try:
        slot_id = int(form.get("slot_id"))
    except (TypeError, ValueError):
        return "Invalid slot selected"
    if slot_id <= 0:
        return "Invalid slot selected"
    return None


def validate_station_form(form):
    required = ["name", "location", "latitude", "longitude", "charger_types", "total_slots"]
    for field in required:
        if not form.get(field):
            return f"{field.replace('_', ' ').title()} is required"
    try:
        float(form.get("latitude"))
        float(form.get("longitude"))
        int(form.get("total_slots"))
    except (TypeError, ValueError):
        return "Latitude, longitude, and total slots must be valid numbers"
    return None


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        errors = validate_profile_form(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect(url_for("profile"))

        current_user.name = request.form.get("name")
        current_user.phone = request.form.get("phone")
        current_user.vehicle_type = request.form.get("vehicle_type")
        current_user.vehicle_model = request.form.get("vehicle_model")
        current_user.license_number = request.form.get("license_number")
        current_user.vehicle_number_plate = request.form.get("vehicle_number_plate")
        
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)

@app.route("/notifications")
@login_required
def notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    return render_template("notifications.html", notifications=notes)

@app.route("/notifications/readall", methods=["POST"])
@login_required
def notifications_read_all():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("Notifications marked as read", "success")
    return redirect(url_for("notifications"))



@app.route("/dashboard")
@login_required
def dashboard():
    from datetime import datetime, date
    now = datetime.now()
    current_month = now.month

    # ---- TOTAL BOOKINGS ----
    total_bookings = Booking.query.filter_by(user_id=current_user.id).count()

    # ---- UPCOMING BOOKINGS ----
    upcoming_bookings = Booking.query.filter_by(
        user_id=current_user.id,
        status='confirmed'
    ).filter(
        Booking.booking_date >= date.today()
    ).count()

    # ---- TOTAL SPENT ----
    # Calculate in Python â€” works with both SQLite and MySQL
    user_bookings = Booking.query.filter_by(
        user_id=current_user.id,
        status='confirmed'
    ).all()

    total_spent = 0
    total_hours = 0

    for b in user_bookings:
        if b.start_time and b.end_time:
            start_mins = b.start_time.hour * 60 + b.start_time.minute
            end_mins = b.end_time.hour * 60 + b.end_time.minute
            duration_hours = (end_mins - start_mins) / 60.0
            if duration_hours > 0:
                total_spent += b.price_per_hour * duration_hours
                total_hours += duration_hours

    total_spent = int(total_spent)
    total_hours = round(total_hours, 1)

    # ---- CHARGING PROGRESS ----
    # 20 hours/month = 100%
    charging_progress = min(int((total_hours / 20) * 100), 100)

    # ---- FAVOURITE STATION ----
    from collections import Counter
    all_bookings = Booking.query.filter_by(user_id=current_user.id).all()

    station_counts = Counter(b.station_id for b in all_bookings if b.station_id)

    fav_station = None
    if station_counts:
        top_station_id = station_counts.most_common(1)[0][0]
        top_station = Station.query.get(top_station_id)
        if top_station:
            fav_station = top_station.name

    # ---- PENDING BOOKINGS ----
    pending_bookings = Booking.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).all()

    return render_template(
        'user_dashboard.html',
        total_bookings=total_bookings,
        upcoming_bookings=upcoming_bookings,
        total_spent=total_spent,
        total_hours=total_hours,
        charging_progress=charging_progress,
        fav_station=fav_station,
        pending_bookings=pending_bookings
    )

@app.route("/booking-history")
@app.route("/my-bookings")
@login_required
def booking_history():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template("booking_history.html", bookings=bookings)

def ensure_default_admin():
    # Creates a default admin on first run if none exist
    try:
        if User.query.filter_by(is_admin=True).count() == 0:
            default_admin = Admin(username="admin", email="admin@example.com")
            default_admin.set_password("AdminPass123")
            db.session.add(default_admin)
            db.session.commit()
    except OperationalError:
        pass


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    ensure_default_admin()
    if request.method == "POST":
        identifier = request.form.get("email") or request.form.get("identifier")
        password = request.form.get("password")
        if not identifier or not password:
            flash("Email/username and password are required", "danger")
            return render_template("admin_login.html")

        admin = User.query.filter_by(is_admin=True).filter(or_(User.email == identifier, User.name == identifier)).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            flash("Admin login successful", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    if current_user.is_authenticated:
        logout_user()
    flash("Admin logged out", "info")
    return redirect(url_for("admin_login"))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('Admin access only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    current_month = datetime.now().month
    current_year = datetime.now().year

    # ---- TOTAL ACTIVE STATIONS ----
    total_stations = Station.query.filter_by(status='active').count()

    # ---- BOOKINGS THIS MONTH ----
    monthly_bookings = Booking.query.filter(
        Booking.status.in_(['confirmed', 'pending'])
    ).count()

    # ---- REVENUE THIS MONTH ----
    # Calculate in Python instead of SQL
    # Works with BOTH SQLite and MySQL
    confirmed_bookings = Booking.query.filter_by(status='confirmed').all()

    monthly_revenue = 0
    for b in confirmed_bookings:
        if b.start_time and b.end_time:
            # Convert time to hours
            start_mins = b.start_time.hour * 60 + b.start_time.minute
            end_mins = b.end_time.hour * 60 + b.end_time.minute
            duration_hours = (end_mins - start_mins) / 60.0
            if duration_hours > 0:
                monthly_revenue += b.price_per_hour * duration_hours

    monthly_revenue = int(monthly_revenue)

    # ---- SLOT UTILIZATION ----
    total_slots = Slot.query.count()
    booked_slots = Slot.query.filter_by(status='occupied').count()
    available_slots = Slot.query.filter_by(status='available').count()

    utilization_percent = int((booked_slots / total_slots * 100) if total_slots > 0 else 0)

    # ---- TOTAL USERS ----
    total_users = User.query.filter_by(is_admin=False).count()

    # ---- RECENT 5 BOOKINGS ----
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    return render_template(
        'admin_dashboard.html',
        total_stations=total_stations,
        monthly_bookings=monthly_bookings,
        monthly_revenue=monthly_revenue,
        utilization_percent=utilization_percent,
        available_slots=available_slots,
        total_users=total_users,
        recent_bookings=recent_bookings
    )

@app.route("/admin/settings")
@admin_required
def admin_settings():
    flash("Admin settings feature is coming soon.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/stations")
@admin_required
def admin_stations():
    stations = Station.query.all()
    utilization = []
    for station in stations:
        total = station.total_slots
        available = Slot.query.filter_by(station_id=station.id, status="available").count()
        occupied = Slot.query.filter_by(station_id=station.id, status="occupied").count()
        utilization.append({
            "station": station,
            "total": total,
            "available": available,
            "occupied": occupied,
        })
    return render_template("admin_stations.html", utilization=utilization)

@app.route("/admin/stations/new", methods=["GET", "POST"])
@admin_required
def admin_station_new():
    if request.method == "POST":
        err = validate_station_form(request.form)
        if err:
            flash(err, "danger")
            return redirect(url_for("admin_station_new"))

        name = request.form.get("name")
        location = request.form.get("location")
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))
        charger_types = request.form.get("charger_types")
        total_slots = int(request.form.get("total_slots", 0))
        status = request.form.get("status", "active")

        station = Station(name=name, location=location, latitude=latitude, longitude=longitude, charger_types=charger_types, total_slots=total_slots, status=status)
        db.session.add(station)
        db.session.commit()

        default_type = charger_types.split(',')[0].strip() if charger_types else 'Type1'
        for i in range(1, total_slots + 1):
            slot = Slot(station_id=station.id, slot_number=str(i), charger_type=default_type, status="available")
            db.session.add(slot)
        db.session.commit()

        flash("Station added", "success")
        return redirect(url_for("admin_stations"))
    return render_template("admin_station_form.html", station=None)

@app.route("/admin/stations/edit/<int:station_id>", methods=["GET", "POST"])
@admin_required
def admin_station_edit(station_id):
    station = Station.query.get_or_404(station_id)
    if request.method == "POST":
        err = validate_station_form(request.form)
        if err:
            flash(err, "danger")
            return redirect(url_for("admin_station_edit", station_id=station_id))

        station.name = request.form.get("name")
        station.location = request.form.get("location")
        station.latitude = float(request.form.get("latitude"))
        station.longitude = float(request.form.get("longitude"))
        station.charger_types = request.form.get("charger_types")
        new_total_slots = int(request.form.get("total_slots", 0))
        status = request.form.get("status", "active")
        station.status = status

        if new_total_slots != station.total_slots:
            old_total = station.total_slots
            station.total_slots = new_total_slots
            if new_total_slots > old_total:
                default_type = station.charger_types.split(',')[0].strip() if station.charger_types else 'Type1'
                for i in range(old_total + 1, new_total_slots + 1):
                    db.session.add(Slot(station_id=station.id, slot_number=str(i), charger_type=default_type, status="available"))
            else:
                extra_slots = Slot.query.filter_by(station_id=station.id).order_by(Slot.id.desc()).limit(old_total - new_total_slots).all()
                for slot in extra_slots:
                    if slot.status != 'occupied':
                        db.session.delete(slot)

        db.session.commit()
        flash("Station updated", "success")
        return redirect(url_for("admin_stations"))
    return render_template("admin_station_form.html", station=station)

@app.route("/admin/stations/delete/<int:station_id>", methods=["POST"])
@admin_required
def admin_station_delete(station_id):
    station = Station.query.get_or_404(station_id)
    db.session.delete(station)
    db.session.commit()
    flash("Station deleted", "success")
    return redirect(url_for("admin_stations"))

@app.route("/admin/stations/toggle/<int:station_id>")
@admin_required
def admin_station_toggle(station_id):
    station = Station.query.get_or_404(station_id)
    station.status = "inactive" if station.status == "active" else "active"
    db.session.commit()
    flash("Station status toggled", "success")
    return redirect(url_for("admin_stations"))

@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    station_id = request.args.get("station_id", type=int)
    date = request.args.get("date")
    status = request.args.get("status")

    query = Booking.query
    if station_id:
        query = query.filter_by(station_id=station_id)
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter_by(booking_date=date_obj)
        except ValueError:
            pass
    if status:
        query = query.filter_by(status=status)

    bookings = query.order_by(Booking.booking_date.desc()).all()
    stations = Station.query.all()
    return render_template("admin_bookings.html", bookings=bookings, stations=stations, selected_station=station_id, selected_date=date, selected_status=status)

@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.all()
    return render_template("admin_users.html", users=users)

@app.route("/admin/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def admin_user_edit(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        err = validate_profile_form(request.form)
        if err:
            flash(err, "danger")
            return redirect(url_for("admin_user_edit", user_id=user_id))

        user.name = request.form.get("name")
        user.phone = request.form.get("phone")
        user.vehicle_type = request.form.get("vehicle_type")
        user.vehicle_model = request.form.get("vehicle_model")
        db.session.commit()
        flash("User updated", "success")
        return redirect(url_for("admin_users"))
    return render_template("admin_user_form.html", user=user)

@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted", "success")
    return redirect(url_for("admin_users"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        if not email:
            flash("Email is required", "danger")
            return redirect(url_for('forgot_password'))
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Plug and Go - Password Reset', recipients=[user.email])
            msg.body = f"To reset your password, click the link:\n\n{reset_url}\n\nIf you did not request this, ignore this email."
            try:
                if not app.config.get('MAIL_USERNAME'):
                    flash(f"SMTP not configured. Development Reset Link: {reset_url}", "info")
                else:
                    mail.send(msg)
                    flash("A password reset email has been sent.", "info")
            except Exception as e:
                flash("Unable to send email: {}. Development Reset Link: {}".format(e, reset_url), "warning")
        else:
            flash("If that email exists, a reset link will be sent.", "info")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('reset_password', token=token))
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route("/create-db")
def create_db():
    db.create_all()
    flash("Database tables created", "success")
    return redirect(url_for("index"))

# ---- 404 NOT FOUND ----
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

# ---- 500 INTERNAL SERVER ERROR ----
@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ---- 403 FORBIDDEN ----
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

# ---- 405 METHOD NOT ALLOWED ----
@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('errors/404.html'), 405

def admin_required(f):
    @wraps(f)
    def decorated_function(
            *args, **kwargs):
        if not current_user\
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
    return decorated_function

@app.route("/register-station", methods=["GET", "POST"])
@login_required
def register_station():
    if request.method == "POST":
        name = request.form.get("name")
        location = request.form.get("location")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        charger_types = request.form.get("charger_types")
        total_slots = request.form.get("total_slots")

        if not all([name, location, latitude, longitude, charger_types, total_slots]):
            flash("All fields are required", "danger")
            return redirect(url_for('register_station'))

        try:
            new_station = Station(
                name=name,
                location=location,
                latitude=float(latitude),
                longitude=float(longitude),
                charger_types=charger_types,
                total_slots=int(total_slots),
                owner_id=current_user.id,
                status='active'
            )
            db.session.add(new_station)
            db.session.commit()

            # Automatically generate slots
            for i in range(1, int(total_slots) + 1):
                # We'll use the first charger type as default for slots if multiple
                def_charger = charger_types.split(',')[0].strip()
                slot = Slot(
                    station_id=new_station.id,
                    slot_number=i,
                    charger_type=def_charger,
                    status='available'
                )
                db.session.add(slot)
            
            db.session.commit()
            flash("Station registered successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering station: {str(e)}", "danger")
            return redirect(url_for('register_station'))

    return render_template("register_station.html")

@app.route("/my-stations")
@login_required
def my_stations():
    stations = Station.query.filter_by(owner_id=current_user.id).all()
    return render_template("my_stations.html", stations=stations)

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
            name          = request.form.get('name'),
            email         = email,
            password_hash = generate_password_hash(request.form.get('password')),
            phone         = request.form.get('phone'),
            vehicle_type  = request.form.get('vehicle_type'),
            vehicle_model = request.form.get('vehicle_model'),
            connector_type= request.form.get('connector_type'),
            license_plate = request.form.get('license_plate'),
            is_admin      = False
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('login'))
    return render_template(
        'register.html')

@app.route('/')
@login_required
def index():
    stations = Station.query\
        .filter_by(status='active')\
        .all()
    return render_template(
        'index.html',
        stations=stations)


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print('[OK] Database connected!')
            print('[OK] All tables created!')
        except Exception as e:
            print(f'[ERROR] DB Error: {e}')
            print('Make sure MySQL is running and plugandgo DB exists')
    app.run(
        debug = True,
        host  = '127.0.0.1',
        port  = 5000
    )