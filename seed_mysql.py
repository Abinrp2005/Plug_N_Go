import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db, User, Station, Slot, Booking
from werkzeug.security import generate_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()
    print('Inserting test data...')

    # ---- ADMIN USER ----
    admin = User(
        name          = 'Arjun Menon',
        email         = 'arjun.menon@plugandgo.com',
        password_hash = generate_password_hash('Admin@1234'),
        phone         = '9847201234',
        vehicle_type  = 'Car',
        vehicle_model = 'Tata Nexon EV',
        is_admin      = True
    )

    # ---- REGULAR USERS ----
    users = [
        User(
            name = 'Aravind Krishnamurthy',
            email = 'aravind.krishnamurthy@gmail.com',
            password_hash = generate_password_hash('Aravind@123'),
            phone         = '9847201234',
            vehicle_type  = 'Car',
            vehicle_model = 'Tata Nexon EV',
            is_admin      = False
        ),
        User(
            name          = 'Divya Nair',
            email         = 'divya.nair91@gmail.com',
            password_hash = generate_password_hash('Divya@123'),
            phone         = '9745312890',
            vehicle_type  = 'Car',
            vehicle_model = 'MG ZS EV',
            is_admin      = False
        ),
        User(
            name          = 'Suresh Babu Pillai',
            email         = 'suresh.pillai@yahoo.com',
            password_hash = generate_password_hash('Suresh@123'),
            phone         = '9562109876',
            vehicle_type  = 'Car',
            vehicle_model = 'Hyundai Kona Electric',
            is_admin      = False
        ),
        User(
            name          = 'Meenakshi Sundaram',
            email         = 'meenakshi.s@gmail.com',
            password_hash = generate_password_hash('Meena@123'),
            phone         = '9894456123',
            vehicle_type  = 'Scooter',
            vehicle_model = 'Ola S1 Pro',
            is_admin      = False
        ),
        User(
            name          = 'Rajesh Venkataraman',
            email         = 'rajesh.venkat@gmail.com',
            password_hash = generate_password_hash('Rajesh@123'),
            phone         = '9840123456',
            vehicle_type  = 'Car',
            vehicle_model = 'Tata Tigor EV',
            is_admin      = False
        ),
        User(
            name          = 'Lakshmi Priya Iyer',
            email         = 'lakshmip.iyer@gmail.com',
            password_hash = generate_password_hash('Lakshmi@123'),
            phone         = '9791234560',
            vehicle_type  = 'Scooter',
            vehicle_model = 'Ather 450X',
            is_admin      = False
        ),
        User(
            name          = 'Vishnu Prasad Menon',
            email         = 'vishnu.prasad@gmail.com',
            password_hash = generate_password_hash('Vishnu@123'),
            phone         = '9746789012',
            vehicle_type  = 'Car',
            vehicle_model = 'Kia EV6',
            is_admin      = False
        ),
        User(
            name          = 'Ananya Ramachandran',
            email         = 'ananya.rc@gmail.com',
            password_hash = generate_password_hash('Ananya@123'),
            phone         = '9500112233',
            vehicle_type  = 'Scooter',
            vehicle_model = 'TVS iQube',
            is_admin      = False
        ),
        User(
            name          = 'Karthikeyan Murugan',
            email         = 'karthik.murugan@gmail.com',
            password_hash = generate_password_hash('Karthik@123'),
            phone         = '9843344556',
            vehicle_type  = 'Car',
            vehicle_model = 'BYD Atto 3',
            is_admin      = False
        ),
        User(
            name          = 'Preethi Subramanian',
            email         = 'preethi.sub@gmail.com',
            password_hash = generate_password_hash('Preethi@123'),
            phone         = '9677889900',
            vehicle_type  = 'Car',
            vehicle_model = 'Tata Nexon EV Max',
            is_admin      = False
        ),
    ]

    # ---- STATIONS ----
    stations = [
        Station(
            name         = 'Ather Grid - Kasaragod',
            location     = 'Nousheen Complex, Anangoor, Kasaragod, Kerala',
            latitude     = 12.5113,
            longitude    = 74.9961,
            charger_types= 'AC Level 2, CCS, Type 2',
            total_slots  = 2,
            status       = 'active'
        ),
        Station(
            name         = 'Tata Power - Taj Bekal',
            location     = 'Kappil Beach, Thekkekara, Bekal, Kasaragod, Kerala',
            latitude     = 12.4228,
            longitude    = 75.0210,
            charger_types= 'DC Fast Charging, CCS, Type 2',
            total_slots  = 2,
            status       = 'active'
        ),
        Station(
            name         = 'IOCL Top Fuels EV Station',
            location     = 'Karanthakkad, Near Fire Station, Kasaragod, Kerala',
            latitude     = 12.5150,
            longitude    = 74.9902,
            charger_types= 'DC Fast Charging, CHAdeMO, Type 2',
            total_slots  = 2,
            status       = 'active'
        ),
        Station(
            name         = 'EESL Padannakkad Charging Point',
            location     = 'Kerala Agricultural University, Padannakkad, Kasaragod, Kerala',
            latitude     = 12.2741,
            longitude    = 75.1147,
            charger_types= 'AC Level 2, Bharat AC',
            total_slots  = 2,
            status       = 'active'
        ),
    ]

    # ---- SLOTS ----
    slot_data = [
        (1, 'KSG-01', 'AC Level 2'),
        (1, 'KSG-02', 'CCS'),
        (2, 'BKL-01', 'DC Fast Charging'),
        (2, 'BKL-02', 'Type 2'),
        (3, 'IOC-01', 'DC Fast Charging'),
        (3, 'IOC-02', 'CHAdeMO'),
        (4, 'PAD-01', 'AC Level 2'),
        (4, 'PAD-02', 'Bharat AC'),
    ]

    # Add everything to database
    db.session.add(admin)
    db.session.add_all(users)
    db.session.add_all(stations)
    db.session.commit()
    print('✅ Users and stations added!')

    for station_id, number, charger in slot_data:
        slot = Slot(
            station_id   = station_id,
            slot_number  = number,
            charger_type = charger,
            status       = 'available'
        )
        db.session.add(slot)

    db.session.commit()
    print('✅ Slots added!')
    
    # ---- BOOKINGS ----
    from datetime import datetime, timedelta, date, time
    now = datetime.utcnow()
    today = date.today()
    bookings = [
        Booking(
            user_id = 2,
            station_id = 1,
            slot_id = 1,
            booking_date = today,
            start_time = time(10, 0),
            end_time = time(12, 0),
            price_per_hour = 150.00,
            status = 'confirmed',
            created_at = now,
            timeout_at = now + timedelta(minutes=15)
        ),
        Booking(
            user_id = 3,
            station_id = 2,
            slot_id = 3,
            booking_date = today,
            start_time = time(13, 0),
            end_time = time(14, 0),
            price_per_hour = 120.00,
            status = 'pending',
            created_at = now,
            timeout_at = now + timedelta(minutes=60)
        ),
        Booking(
            user_id = 4,
            station_id = 3,
            slot_id = 5,
            booking_date = today - timedelta(days=1),
            start_time = time(9, 0),
            end_time = time(11, 0),
            price_per_hour = 180.00,
            status = 'completed',
            created_at = now - timedelta(days=1),
            timeout_at = now - timedelta(days=1, minutes=-15)
        ),
        Booking(
            user_id = 5,
            station_id = 4,
            slot_id = 7,
            booking_date = today + timedelta(days=1),
            start_time = time(15, 0),
            end_time = time(16, 30),
            price_per_hour = 130.00,
            status = 'confirmed',
            created_at = now,
            timeout_at = now + timedelta(minutes=15)
        ),
        Booking(
            user_id = 2,
            station_id = 2,
            slot_id = 4,
            booking_date = today - timedelta(days=2),
            start_time = time(11, 0),
            end_time = time(12, 0),
            price_per_hour = 120.00,
            status = 'cancelled',
            created_at = now - timedelta(days=2),
            timeout_at = now - timedelta(days=2, minutes=-15)
        ),
    ]
    db.session.add_all(bookings)
    db.session.commit()
    print('✅ Bookings added!')
    
    # Update slots as occupied for pending/confirmed bookings
    for b in bookings:
        if b.status in ['pending', 'confirmed']:
            s = Slot.query.get(b.slot_id)
            if s:
                s.status = 'occupied'
                db.session.add(s)
    db.session.commit()
    print('✅ Slot statuses updated!')

    print()
    print('=== LOGIN CREDENTIALS ===')
    print()
    print('ADMIN:')
    print('  Email   : arjun.menon@plugandgo.com')
    print('  Password: Admin@1234')
    print()
    print('USER:')
    print('  Email   : aravind.krishnamurthy@gmail.com')
    print('  Password: Aravind@123')
    print()
    print('✅ All done! Visit:')
    print('   http://127.0.0.1:5000/login')
