# DealerHub — India's Premier Car Auction Platform

A full-stack Flask web application for car dealers to browse inventory, bid in live auctions, and manage purchases.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://127.0.0.1:5000
```

## ✨ What's New (Enhanced Version)

### 🏠 Landing Page
- **Stunning hero section** with animated background and live stats
- **Bid of the Day** spotlight — featured auction prominently displayed
- **Live auction ticker** scrolling across the page
- **Featured inventory grid** showing latest 6 cars
- **How It Works** timeline (5 steps)
- Responsive design, sticky navbar with scroll effect

### 📊 Dashboard
- **Auto-refreshing auctions** — live bid amounts update every 30 seconds via `/api/auctions`
- **Bid of the Day banner** — always shows the featured auction at the top
- **My Bids tab** — track all your bids with winning/outbid status
- **Condition score bars** on car and auction cards
- **Car descriptions** displayed in cards

### ➕ Add Car (Manual Addition)
- Navigate to **Dashboard → Add Car** (top-right button, verified dealers only)
- Fill in: name, brand, year, fuel type, km driven, price, location, image URL, description, condition score
- **Optional: Create auction** — toggle to instantly set up a live auction
- **Bid of the Day** checkbox — mark the new auction as the featured one

### 🔌 APIs
- `GET /api/auctions` — returns live auction data (JSON) for auto-refresh
- `GET /api/cars` — returns all car data (JSON)
- `POST /set-featured/<auction_id>` — sets a specific auction as Bid of the Day

## 📁 Project Structure

```
dealerhub/
├── app.py                  # Flask backend
├── car_dealer.db           # SQLite database (auto-created)
├── requirements.txt
├── inspection_reports/     # Place PDF reports here
├── templates/
│   ├── index.html          # Landing page
│   ├── dashboard.html      # Main dealer dashboard
│   ├── add_car.html        # Manual car addition form
│   ├── login.html
│   ├── register.html
│   └── onboarding.html
└── static/
    ├── style.css
    └── script.js
```

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `dealers` | Registered dealers with verification status |
| `cars` | Vehicle inventory |
| `auctions` | Live auctions linked to cars |
| `bids` | All bids placed |
| `purchases` | Completed purchases |
| `notifications` | Dealer notifications |
| `business_details` | GST, address |
| `documents` | PAN, ID proof |
| `bank_details` | Bank account info |

## 🔑 Key Features

- **4-step KYC onboarding** (Business → Documents → Bank → Confirm)
- **Live bidding** with real-time price tracking
- **Inspection report downloads** (PDFs in `/inspection_reports/`)
- **Bid of the Day** — featured auction on landing page and dashboard
- **Auto-refresh** — auction prices update without page reload
- **Condition scores** — visual health bars for each vehicle
