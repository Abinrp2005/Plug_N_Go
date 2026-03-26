from datetime import datetime, timedelta
from app import app
from extensions import db
from models import Admin, User, Station, Slot, Booking
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    # Admin
    admin = Admin.query.filter_by(username='arjun_admin').first()
    if not admin:
        admin = Admin(username='arjun_admin', email='arjun.menon@plugandgo.com')
    admin.password_hash = generate_password_hash('Admin@1234')
    db.session.add(admin)

    # Users
    users = [
        ('Aravind Krishnamurthy', 'aravind.krishnamurthy@gmail.com', 'Aravind@123', '9847201234', 'Car', 'Tata Nexon EV'),
        ('Divya Nair', 'divya.nair91@gmail.com', 'Divya@123', '9745312890', 'Car', 'MG ZS EV'),
        ('Suresh Babu Pillai', 'suresh.pillai@yahoo.com', 'Suresh@123', '9562109876', 'Car', 'Hyundai Kona Electric'),
        ('Meenakshi Sundaram', 'meenakshi.s@gmail.com', 'Meena@123', '9894456123', 'Scooter', 'Ola S1 Pro'),
        ('Rajesh Venkataraman', 'rajesh.venkat@gmail.com', 'Rajesh@123', '9840123456', 'Car', 'Tata Tigor EV'),
        ('Lakshmi Priya Iyer', 'lakshmip.iyer@gmail.com', 'Lakshmi@123', '9791234560', 'Scooter', 'Ather 450X'),
        ('Vishnu Prasad Menon', 'vishnu.prasad@gmail.com', 'Vishnu@123', '9746789012', 'Car', 'Kia EV6'),
        ('Ananya Ramachandran', 'ananya.rc@gmail.com', 'Ananya@123', '9500112233', 'Scooter', 'TVS iQube'),
        ('Karthikeyan Murugan', 'karthik.murugan@gmail.com', 'Karthik@123', '9843344556', 'Car', 'BYD Atto 3'),
        ('Preethi Subramanian', 'preethi.sub@gmail.com', 'Preethi@123', '9677889900', 'Car', 'Tata Nexon EV Max'),
    ]
    for name, email, pw, phone, vt, vm in users:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email, phone=phone, vehicle_type=vt, vehicle_model=vm)
        user.password_hash = generate_password_hash(pw)
        db.session.add(user)

    db.session.commit()

    # Stations
    stations_data = [
        ('Lulu Mall EV Station', 'Lulu Mall, Edapally, Kochi, Kerala', 10.0270, 76.3084, 'AC Level 2, DC Fast Charging, CCS, Type 2', 2, 'active'),
        ('Inorbit Mall Charging Hub', 'Inorbit Mall, Cyberabad, Hyderabad, Telangana', 17.4330, 78.3851, 'AC Level 2, DC Fast Charging, CHAdeMO, Type 2', 2, 'active'),
        ('Phoenix MarketCity EV Point', 'Phoenix MarketCity, Whitefield, Bengaluru, Karnataka', 12.9698, 77.7499, 'AC Level 2, CCS, Type 2, Bharat AC', 2, 'active'),
        ('Express Avenue EV Station', 'Express Avenue Mall, Royapettah, Chennai, Tamil Nadu', 13.0569, 80.2620, 'DC Fast Charging, CCS, CHAdeMO, AC Level 2', 2, 'active'),
        ('Trivandrum Central EV Hub', 'Trivandrum Central Station Road, Thiruvananthapuram, Kerala', 8.4855, 76.9492, 'AC Level 2, Type 2, Bharat AC', 1, 'active'),
        ('Coimbatore Smart EV Point', 'Brookefields Mall, Coimbatore, Tamil Nadu', 11.0043, 76.9622, 'AC Level 2, CCS, DC Fast Charging', 2, 'active'),
        ('Mangaluru EV Charging Station', 'Forum Fiza Mall, Pandeshwar, Mangaluru, Karnataka', 12.8685, 74.8426, 'AC Level 2, Type 2, Bharat AC', 1, 'active'),
        ('Vijayawada EV Hub', 'PVP Square Mall, Vijayawada, Andhra Pradesh', 16.5142, 80.6318, 'DC Fast Charging, CCS, AC Level 2', 2, 'active'),
    ]
    for name, location, lat, lon, types, total, status in stations_data:
        station = Station.query.filter_by(name=name).first()
        if not station:
            station = Station(name=name, location=location, latitude=lat, longitude=lon, charger_types=types, total_slots=total, status=status)
        else:
            station.location = location
            station.latitude = lat
            station.longitude = lon
            station.charger_types = types
            station.total_slots = total
            station.status = status
        db.session.add(station)

    db.session.commit()

    # Slots
    slots_data = [
        (1, 'KCH-01', 'AC Level 2'),
        (1, 'KCH-02', 'DC Fast Charging'),
        (2, 'HYD-01', 'AC Level 2'),
        (2, 'HYD-02', 'CHAdeMO'),
        (3, 'BLR-01', 'CCS'),
        (3, 'BLR-02', 'Type 2'),
        (4, 'CHN-01', 'DC Fast Charging'),
        (4, 'CHN-02', 'AC Level 2'),
        (5, 'TVM-01', 'Bharat AC'),
        (6, 'CBE-01', 'AC Level 2'),
        (6, 'CBE-02', 'CCS'),
        (7, 'MNG-01', 'Type 2'),
        (8, 'VJA-01', 'DC Fast Charging'),
        (8, 'VJA-02', 'AC Level 2'),
    ]
    for station_id, slot_number, charger_type in slots_data:
        slot = Slot.query.filter_by(station_id=station_id, slot_number=slot_number).first()
        if not slot:
            slot = Slot(station_id=station_id, slot_number=slot_number, charger_type=charger_type, status='available')
        else:
            slot.charger_type = charger_type
            slot.status = 'available'
        db.session.add(slot)

    db.session.commit()

    # Bookings
    now = datetime.utcnow()
    bookings_data = [
        (1, 1, 1, '2026-03-15', '10:00:00', '12:00:00', 150.00, 'confirmed'),
        (2, 3, 2, '2026-03-15', '11:00:00', '13:00:00', 180.00, 'confirmed'),
        (3, 5, 3, '2026-03-15', '09:00:00', '10:00:00', 200.00, 'confirmed'),
        (4, 7, 4, '2026-03-16', '14:00:00', '15:00:00', 160.00, 'pending'),
        (5, 9, 5, '2026-03-16', '08:00:00', '09:30:00', 120.00, 'confirmed'),
        (6, 10, 6, '2026-03-16', '16:00:00', '18:00:00', 150.00, 'pending'),
        (7, 12, 7, '2026-03-14', '10:00:00', '11:00:00', 130.00, 'cancelled'),
        (8, 13, 8, '2026-03-14', '13:00:00', '15:00:00', 175.00, 'confirmed'),
        (9, 2, 1, '2026-03-17', '09:00:00', '11:00:00', 150.00, 'pending'),
        (10, 4, 2, '2026-03-17', '15:00:00', '16:00:00', 180.00, 'confirmed'),
    ]
    for user_id, slot_id, station_id, bdate, stime, etime, price, status in bookings_data:
        booking = Booking.query.filter_by(user_id=user_id, slot_id=slot_id, station_id=station_id, booking_date=datetime.strptime(bdate, '%Y-%m-%d').date(), start_time=datetime.strptime(stime, '%H:%M:%S').time()).first()
        if not booking:
            booking = Booking(
                user_id=user_id,
                slot_id=slot_id,
                station_id=station_id,
                booking_date=datetime.strptime(bdate, '%Y-%m-%d').date(),
                start_time=datetime.strptime(stime, '%H:%M:%S').time(),
                end_time=datetime.strptime(etime, '%H:%M:%S').time(),
                price_per_hour=price,
                status=status,
                created_at=now,
                timeout_at=now + timedelta(minutes=15),
            )
        else:
            booking.start_time = datetime.strptime(stime, '%H:%M:%S').time()
            booking.end_time = datetime.strptime(etime, '%H:%M:%S').time()
            booking.price_per_hour = price
            booking.status = status
            booking.created_at = now
            booking.timeout_at = now + timedelta(minutes=15)
        db.session.add(booking)

    db.session.commit()

    # Slot status update
    for booking in Booking.query.filter(Booking.status.in_(['pending', 'confirmed'])).all():
        slot = Slot.query.get(booking.slot_id)
        if slot:
            slot.status = 'occupied'
            db.session.add(slot)
    db.session.commit()

    print('Done: Admins', Admin.query.count(), 'Users', User.query.count(), 'Stations', Station.query.count(), 'Slots', Slot.query.count(), 'Bookings', Booking.query.count())
    from sqlalchemy import text
    rows = db.session.execute(text('SELECT u.name, b.status, s.name as station FROM bookings b JOIN users u on b.user_id=u.id JOIN stations s on b.station_id=s.id')).fetchall()
    for r in rows:
        print(r)
