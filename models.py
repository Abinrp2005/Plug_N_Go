from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String(100),
        nullable=False
    )
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )
    password_hash = db.Column(
        db.String(256),
        nullable=False
    )

    # THIS IS THE MISSING COLUMN
    is_admin = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    phone = db.Column(
        db.String(15)
    )
    vehicle_type = db.Column(
        db.String(50)
    )
    vehicle_model = db.Column(
        db.String(100)
    )
    license_number = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )
    vehicle_number_plate = db.Column(
        db.String(20),
        nullable=True
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    bookings = db.relationship(
        'Booking',
        backref='user',
        lazy=True
    )

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        from itsdangerous import URLSafeTimedSerializer
        from config import Config
        s = URLSafeTimedSerializer(Config.SECRET_KEY)
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
        from config import Config
        s = URLSafeTimedSerializer(Config.SECRET_KEY)
        try:
            data = s.loads(token, salt='password-reset-salt', max_age=expires_sec)
        except (SignatureExpired, BadSignature):
            return None
        return User.query.get(data.get('user_id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Admin(db.Model, UserMixin):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return True

class Station(db.Model):
    __tablename__ = "stations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    charger_types = db.Column(db.String(255), nullable=False)
    total_slots = db.Column(db.Integer, nullable=False, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.Enum("active", "inactive", name="station_status"), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    slots = db.relationship("Slot", backref="station", lazy=True)
    bookings = db.relationship("Booking", backref="station", lazy=True)

class Slot(db.Model):
    __tablename__ = "slots"
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    slot_number = db.Column(db.String(50), nullable=False)
    charger_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum("available", "occupied", "maintenance", name="slot_status"), nullable=False, default="available")

    bookings = db.relationship("Booking", backref="slot", lazy=True)

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("slots.id", ondelete="CASCADE"), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum("pending", "confirmed", "cancelled", name="booking_status"), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    timeout_at = db.Column(db.DateTime, nullable=True)

class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref="notifications")
