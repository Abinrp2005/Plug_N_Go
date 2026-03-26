import requests

base = 'http://127.0.0.1:5000'
routes = [
    '/', '/register', '/login', '/profile', '/dashboard', '/booking-history',
    '/notifications', '/forgot-password', '/reset-password/sometoken',
    '/admin/login', '/admin/dashboard', '/admin/stations', '/admin/bookings',
    '/admin/users', '/api/stations/availability',
]
print('checking', len(routes), 'routes')
for r in routes:
    try:
        resp = requests.get(base + r, timeout=5)
        print(r, resp.status_code)
    except Exception as e:
        print(r, 'ERROR', e)
