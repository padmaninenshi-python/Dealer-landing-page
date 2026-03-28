from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'car_dealer_secret_key_2024'

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'car_dealer.db')
INSPECTION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inspection_reports')
os.makedirs(INSPECTION_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS dealers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            mobile TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            business_name TEXT,
            city TEXT,
            password TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            verification_step INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS business_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id INTEGER UNIQUE,
            business_name TEXT,
            gst_number TEXT,
            business_address TEXT,
            FOREIGN KEY(dealer_id) REFERENCES dealers(id)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id INTEGER UNIQUE,
            pan_number TEXT,
            id_proof_type TEXT,
            id_proof_number TEXT,
            FOREIGN KEY(dealer_id) REFERENCES dealers(id)
        );
        CREATE TABLE IF NOT EXISTS bank_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id INTEGER UNIQUE,
            account_holder TEXT,
            account_number TEXT,
            ifsc_code TEXT,
            bank_name TEXT,
            FOREIGN KEY(dealer_id) REFERENCES dealers(id)
        );
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            year INTEGER,
            fuel_type TEXT,
            km_driven INTEGER,
            price REAL,
            location TEXT,
            image_url TEXT,
            status TEXT DEFAULT 'available',
            inspection_report TEXT,
            description TEXT,
            condition_score INTEGER DEFAULT 8,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER,
            start_price REAL,
            current_bid REAL,
            highest_bidder_id INTEGER,
            status TEXT DEFAULT 'live',
            end_time TIMESTAMP,
            bid_count INTEGER DEFAULT 0,
            is_featured INTEGER DEFAULT 0,
            FOREIGN KEY(car_id) REFERENCES cars(id)
        );
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auction_id INTEGER,
            dealer_id INTEGER,
            bid_amount REAL,
            bid_status TEXT DEFAULT 'registered',
            bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(auction_id) REFERENCES auctions(id),
            FOREIGN KEY(dealer_id) REFERENCES dealers(id)
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id INTEGER,
            car_id INTEGER,
            price REAL,
            status TEXT DEFAULT 'processing',
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dealer_id) REFERENCES dealers(id),
            FOREIGN KEY(car_id) REFERENCES cars(id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id INTEGER,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dealer_id) REFERENCES dealers(id)
        );
    ''')

    # Add missing columns if upgrading
    try:
        c.execute("ALTER TABLE cars ADD COLUMN description TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE cars ADD COLUMN condition_score INTEGER DEFAULT 8")
    except: pass
    try:
        c.execute("ALTER TABLE cars ADD COLUMN added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except: pass
    try:
        c.execute("ALTER TABLE auctions ADD COLUMN bid_count INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE auctions ADD COLUMN is_featured INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE bids ADD COLUMN bid_status TEXT DEFAULT 'registered'")
    except: pass

    # Seed sample data
    c.execute("SELECT COUNT(*) FROM cars")
    if c.fetchone()[0] == 0:
        cars_data = [
            ('Maruti Swift VXI', 'Maruti', 2021, 'Petrol', 25000, 520000, 'Mumbai',
             'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=600', 'available',
             'swift_inspection.pdf', 'Well maintained single owner Swift. All service records available.', 8),
            ('Hyundai Creta SX', 'Hyundai', 2022, 'Diesel', 18000, 1250000, 'Delhi',
             'https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=600', 'available',
             'creta_inspection.pdf', 'Top variant with sunroof, ventilated seats. Like new condition.', 9),
            ('Honda City ZX', 'Honda', 2020, 'Petrol', 32000, 890000, 'Bangalore',
             'https://images.unsplash.com/photo-1590362891991-f776e747a588?w=600', 'available',
             'city_inspection.pdf', 'Fully loaded ZX variant. Honda Sensing safety suite included.', 8),
            ('Tata Nexon XZ+', 'Tata', 2023, 'Petrol', 8000, 1100000, 'Pune',
             'https://images.unsplash.com/photo-1609521263047-f8f205293f24?w=600', 'available',
             'nexon_inspection.pdf', 'Almost new 5-star safety rated Nexon. Under warranty.', 10),
            ('Kia Seltos HTX', 'Kia', 2021, 'Diesel', 28000, 1350000, 'Chennai',
             'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=600', 'available',
             'seltos_inspection.pdf', 'Premium HTX+ with panoramic sunroof and BOSE sound system.', 9),
            ('Toyota Fortuner', 'Toyota', 2022, 'Diesel', 15000, 3500000, 'Hyderabad',
             'https://images.unsplash.com/photo-1606611013016-969c19ba27a6?w=600', 'available',
             'fortuner_inspection.pdf', 'Iconic Fortuner in pristine condition. Full service history at Toyota.', 9),
            ('MG Hector Plus', 'MG', 2022, 'Petrol', 20000, 1580000, 'Ahmedabad',
             'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=600', 'available',
             'hector_inspection.pdf', '6-seater with panoramic sunroof and connected car tech.', 8),
            ('Mahindra Thar LX', 'Mahindra', 2023, 'Diesel', 12000, 1750000, 'Jaipur',
             'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?w=600', 'available',
             'thar_inspection.pdf', 'Hard top 4x4. Weekend warrior in absolutely mint condition.', 9),
        ]
        c.executemany("""INSERT INTO cars (name, brand, year, fuel_type, km_driven, price, location,
            image_url, status, inspection_report, description, condition_score) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", cars_data)

        # Auctions — mark one as featured (bid of the day)
        c.execute("INSERT INTO auctions (car_id, start_price, current_bid, status, end_time, bid_count, is_featured) VALUES (1, 480000, 495000, 'live', '2026-04-15 18:00:00', 7, 0)")
        c.execute("INSERT INTO auctions (car_id, start_price, current_bid, status, end_time, bid_count, is_featured) VALUES (2, 1150000, 1210000, 'live', '2026-04-16 18:00:00', 12, 1)")
        c.execute("INSERT INTO auctions (car_id, start_price, current_bid, status, end_time, bid_count, is_featured) VALUES (4, 1000000, 1025000, 'live', '2026-04-17 18:00:00', 5, 0)")
        c.execute("INSERT INTO auctions (car_id, start_price, current_bid, status, end_time, bid_count, is_featured) VALUES (6, 3200000, 3350000, 'live', '2026-04-18 18:00:00', 9, 0)")
        c.execute("INSERT INTO auctions (car_id, start_price, current_bid, status, end_time, bid_count, is_featured) VALUES (8, 1600000, 1650000, 'live', '2026-04-19 18:00:00', 4, 0)")

    conn.commit()
    conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'dealer_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Landing Page ───
@app.route('/')
def index():
    conn = get_db()
    # Featured auction (bid of the day)
    bid_of_day = conn.execute("""
        SELECT a.*, c.name as car_name, c.brand, c.year, c.fuel_type, c.km_driven,
               c.image_url, c.location, c.description, c.condition_score
        FROM auctions a JOIN cars c ON a.car_id=c.id
        WHERE a.status='live' AND a.is_featured=1 LIMIT 1
    """).fetchone()

    # Featured cars (latest 6)
    featured_cars = conn.execute(
        "SELECT * FROM cars WHERE status='available' ORDER BY id DESC LIMIT 6"
    ).fetchall()

    # Live auctions for ticker
    live_auctions = conn.execute("""
        SELECT a.*, c.name as car_name, c.brand, c.year, c.image_url, c.location
        FROM auctions a JOIN cars c ON a.car_id=c.id WHERE a.status='live' LIMIT 5
    """).fetchall()

    # Stats
    stats = {
        'total_cars': conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0],
        'live_auctions': conn.execute("SELECT COUNT(*) FROM auctions WHERE status='live'").fetchone()[0],
        'total_dealers': conn.execute("SELECT COUNT(*) FROM dealers").fetchone()[0],
        'total_bids': conn.execute("SELECT COUNT(*) FROM bids").fetchone()[0],
    }
    conn.close()
    return render_template('index.html', bid_of_day=bid_of_day, featured_cars=featured_cars,
                           live_auctions=live_auctions, stats=stats)

# ─── Register ───
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        mobile = request.form['mobile']
        email = request.form['email']
        business_name = request.form.get('business_name','')
        city = request.form.get('city','')
        password = hash_password(request.form['password'])
        conn = get_db()
        try:
            conn.execute("INSERT INTO dealers (full_name, mobile, email, business_name, city, password) VALUES (?,?,?,?,?,?)",
                         (full_name, mobile, email, business_name, city, password))
            conn.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Mobile or Email already registered.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# ─── Login ───
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])
        conn = get_db()
        dealer = conn.execute("SELECT * FROM dealers WHERE email=? AND password=?", (email, password)).fetchone()
        conn.close()
        if dealer:
            session['dealer_id'] = dealer['id']
            session['dealer_name'] = dealer['full_name']
            if dealer['verification_step'] < 4:
                return redirect(url_for('onboarding'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

# ─── Logout ───
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── Onboarding ───
@app.route('/onboarding', methods=['GET','POST'])
@login_required
def onboarding():
    dealer_id = session['dealer_id']
    conn = get_db()
    dealer = conn.execute("SELECT * FROM dealers WHERE id=?", (dealer_id,)).fetchone()
    step = dealer['verification_step']

    if request.method == 'POST':
        current_step = int(request.form.get('step', 0))
        if current_step == 1:
            conn.execute("INSERT OR REPLACE INTO business_details (dealer_id, business_name, gst_number, business_address) VALUES (?,?,?,?)",
                         (dealer_id, request.form['business_name'], request.form['gst_number'], request.form['business_address']))
            conn.execute("UPDATE dealers SET verification_step=1 WHERE id=?", (dealer_id,))
        elif current_step == 2:
            conn.execute("INSERT OR REPLACE INTO documents (dealer_id, pan_number, id_proof_type, id_proof_number) VALUES (?,?,?,?)",
                         (dealer_id, request.form['pan_number'], request.form['id_proof_type'], request.form['id_proof_number']))
            conn.execute("UPDATE dealers SET verification_step=2 WHERE id=?", (dealer_id,))
        elif current_step == 3:
            conn.execute("INSERT OR REPLACE INTO bank_details (dealer_id, account_holder, account_number, ifsc_code, bank_name) VALUES (?,?,?,?,?)",
                         (dealer_id, request.form['account_holder'], request.form['account_number'], request.form['ifsc_code'], request.form['bank_name']))
            conn.execute("UPDATE dealers SET verification_step=3 WHERE id=?", (dealer_id,))
        elif current_step == 4:
            conn.execute("UPDATE dealers SET verification_step=4, is_verified=1 WHERE id=?", (dealer_id,))
            conn.execute("INSERT INTO notifications (dealer_id, message) VALUES (?, ?)",
                         (dealer_id, 'Your documents have been submitted for verification. You can now browse and bid on cars!'))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        conn.commit()
        conn.close()
        return redirect(url_for('onboarding'))

    conn.close()
    return render_template('onboarding.html', step=step)

# ─── Dashboard ───
@app.route('/dashboard')
@login_required
def dashboard():
    dealer_id = session['dealer_id']
    conn = get_db()
    dealer = conn.execute("SELECT * FROM dealers WHERE id=?", (dealer_id,)).fetchone()
    if dealer['verification_step'] < 4:
        conn.close()
        return redirect(url_for('onboarding'))

    cars = conn.execute("SELECT * FROM cars WHERE status='available' ORDER BY id DESC").fetchall()
    auctions = conn.execute("""
        SELECT a.*, c.name as car_name, c.brand, c.year, c.fuel_type, c.km_driven,
               c.image_url, c.location, c.inspection_report, c.condition_score, c.description
        FROM auctions a JOIN cars c ON a.car_id=c.id WHERE a.status='live'
        ORDER BY a.is_featured DESC, a.bid_count DESC
    """).fetchall()
    bid_of_day = conn.execute("""
        SELECT a.*, c.name as car_name, c.brand, c.year, c.fuel_type, c.km_driven,
               c.image_url, c.location, c.inspection_report, c.condition_score, c.description
        FROM auctions a JOIN cars c ON a.car_id=c.id
        WHERE a.status='live' AND a.is_featured=1 LIMIT 1
    """).fetchone()
    purchases = conn.execute("""
        SELECT p.*, c.name as car_name, c.brand, c.year, c.image_url
        FROM purchases p JOIN cars c ON p.car_id=c.id WHERE p.dealer_id=?
    """, (dealer_id,)).fetchall()
    notifications = conn.execute(
        "SELECT * FROM notifications WHERE dealer_id=? ORDER BY created_at DESC LIMIT 20", (dealer_id,)
    ).fetchall()
    # My bids with auction info
    my_bids = conn.execute("""
        SELECT b.*, a.current_bid, a.status as auction_status, c.name as car_name,
               c.image_url, c.brand, c.year,
               CASE WHEN a.highest_bidder_id=? THEN 1 ELSE 0 END as is_winning
        FROM bids b
        JOIN auctions a ON b.auction_id=a.id
        JOIN cars c ON a.car_id=c.id
        WHERE b.dealer_id=?
        ORDER BY b.bid_time DESC
    """, (dealer_id, dealer_id)).fetchall()

    conn.close()
    return render_template('dashboard.html', dealer=dealer, cars=cars, auctions=auctions,
                           bid_of_day=bid_of_day, purchases=purchases, notifications=notifications,
                           my_bids=my_bids)

# ─── Car Detail Page ───
@app.route('/car/<int:car_id>')
@login_required
def car_detail(car_id):
    conn = get_db()
    dealer_id = session['dealer_id']
    dealer = conn.execute("SELECT * FROM dealers WHERE id=?", (dealer_id,)).fetchone()
    car = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    conn.close()
    if not car:
        flash('Car not found.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('car_detail.html', car=car, is_auction=False,
                           auction=None, is_verified=bool(dealer['is_verified']))

# ─── Auction Car Detail Page ───
@app.route('/auction/<int:auction_id>')
@login_required
def auction_detail(auction_id):
    conn = get_db()
    dealer_id = session['dealer_id']
    dealer = conn.execute("SELECT * FROM dealers WHERE id=?", (dealer_id,)).fetchone()
    row = conn.execute("""
        SELECT a.*, c.name, c.brand, c.year, c.fuel_type, c.km_driven,
               c.price, c.location, c.image_url, c.description,
               c.condition_score, c.inspection_report
        FROM auctions a JOIN cars c ON a.car_id=c.id
        WHERE a.id=?
    """, (auction_id,)).fetchone()
    conn.close()
    if not row:
        flash('Auction not found.', 'error')
        return redirect(url_for('dashboard'))
    # Build car-like object for the template
    from collections import namedtuple
    car_data = dict(row)
    # Make it behave like a car object for the template
    class CarObj:
        def __init__(self, d):
            self.__dict__.update(d)
            self.id = d['car_id']
    car = CarObj(car_data)
    return render_template('car_detail.html', car=car, is_auction=True,
                           auction=row, is_verified=bool(dealer['is_verified']))

# ─── API: Live Auction Data (for auto-refresh) ───
@app.route('/api/auctions')
@login_required
def api_auctions():
    conn = get_db()
    auctions = conn.execute("""
        SELECT a.id, a.current_bid, a.bid_count, a.end_time, a.status,
               c.name as car_name, c.image_url
        FROM auctions a JOIN cars c ON a.car_id=c.id WHERE a.status='live'
    """).fetchall()
    conn.close()
    return jsonify([dict(row) for row in auctions])

# ─── API: Cars (for live updates) ───
@app.route('/api/cars')
@login_required
def api_cars():
    conn = get_db()
    cars = conn.execute("SELECT id, name, brand, price, status FROM cars ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in cars])

# ─── Bid Status Helper ───
def get_bid_status(bid_amount, start_price):
    """Status based on how much bid exceeds the auction start price."""
    inc = bid_amount - start_price
    if inc >= 100000:   return 'win'      # +₹1L    → Win
    elif inc >= 70000:  return 'on_bid'   # +₹70K   → On Bid
    elif inc >= 50000:  return 'pending'  # +₹50K   → Pending
    elif inc >= 20000:  return 'waiting'  # +₹20K   → Waiting
    else:               return 'registered'

# ─── Place Bid ───
@app.route('/bid/<int:auction_id>', methods=['POST'])
@login_required
def place_bid(auction_id):
    dealer_id = session['dealer_id']
    conn = get_db()
    dealer = conn.execute("SELECT * FROM dealers WHERE id=?", (dealer_id,)).fetchone()
    if not dealer['is_verified']:
        flash('Complete document verification before bidding.', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    bid_amount = float(request.form['bid_amount'])
    auction = conn.execute("SELECT * FROM auctions WHERE id=?", (auction_id,)).fetchone()

    if not auction:
        flash('Auction not found.', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    # ── Check 45-minute timer ──
    from datetime import datetime as dt
    end_time = dt.strptime(str(auction['end_time'])[:19], '%Y-%m-%d %H:%M:%S')
    now = dt.utcnow()
    minutes_left = (end_time - now).total_seconds() / 60
    # If auction ends within 45 min, do NOT set a new 45-min window — just validate remaining time
    if now > end_time:
        flash('This auction has already ended.', 'error')
        conn.close()
        return redirect(url_for('auction_detail', auction_id=auction_id))

    if bid_amount > auction['current_bid']:
        # Determine bid status
        bid_status = get_bid_status(bid_amount, auction['start_price'])
        conn.execute("UPDATE auctions SET current_bid=?, highest_bidder_id=?, bid_count=bid_count+1 WHERE id=?",
                     (bid_amount, dealer_id, auction_id))
        conn.execute("INSERT INTO bids (auction_id, dealer_id, bid_amount, bid_status) VALUES (?,?,?,?)",
                     (auction_id, dealer_id, bid_amount, bid_status))
        status_labels = {'waiting': 'Waiting ⏳', 'pending': 'Pending 🕐', 'on_bid': 'On Bid 🔥', 'win': 'Winning! 🏆', 'registered': 'Registered'}
        label = status_labels.get(bid_status, bid_status)
        conn.execute("INSERT INTO notifications (dealer_id, message) VALUES (?, ?)",
                     (dealer_id, f'Bid ₹{bid_amount:,.0f} placed  on auction #{auction_id}!'))
        conn.commit()
        flash(f'Bid placed!', 'success')
    else:
        flash('Bid must be higher than the current bid.', 'error')
    conn.close()
    return redirect(url_for('auction_detail', auction_id=auction_id))

# ─── Edit Profile ───
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    dealer_id = session['dealer_id']
    conn = get_db()
    dealer = conn.execute("SELECT * FROM dealers WHERE id=?", (dealer_id,)).fetchone()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip()
        business_name = request.form.get('business_name', '').strip()
        city = request.form.get('city', '').strip()
        new_password = request.form.get('new_password', '').strip()
        if full_name:
            updates = "full_name=?, mobile=?, email=?, business_name=?, city=?"
            params = [full_name, mobile, email, business_name, city]
            if new_password:
                hashed = hashlib.sha256(new_password.encode()).hexdigest()
                updates += ", password=?"
                params.append(hashed)
            params.append(dealer_id)
            conn.execute(f"UPDATE dealers SET {updates} WHERE id=?", params)
            conn.commit()
            session['dealer_name'] = full_name
            flash('Profile updated successfully! ✅', 'success')
            conn.close()
            return redirect(url_for('edit_profile'))
    conn.close()
    return render_template('edit_profile.html', dealer=dealer)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
