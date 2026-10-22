# Groczy — Smart Grocery Recommendation System

Groczy is a Flask and MySQL grocery shopping application. It includes customer accounts, database-backed product search, rule-based recommendations, persistent carts and wishlists, back-in-stock notifications, COD demonstration orders, and a role-protected admin workspace.

## Stack and payment status

- Python 3.10+ and Flask, Flask-SQLAlchemy, Flask-WTF, PyMySQL
- MySQL 8 / XAMPP MySQL with phpMyAdmin
- Server-rendered HTML templates, CSS, vanilla JavaScript, Bootstrap 5 and Font Awesome
- `payments.py` documents the provider interface and blocks payment creation. Online payments cannot charge money; COD orders are stored as **Not Paid**.

## Install on Windows with XAMPP

1. Install Python from [python.org](https://www.python.org/downloads/) and select **Add Python to PATH**.
2. Install XAMPP from [apachefriends.org](https://www.apachefriends.org/). Apache is optional for Groczy; Flask serves the application.
3. Open XAMPP Control Panel and click **Start** beside MySQL.
4. Open `http://localhost/phpmyadmin/`.
5. Select **Import**, choose this project's `groczy.sql`, then click **Import**. This creates `groczy_db`, tables, indexes, and grocery categories. The seed command below inserts sample products.
6. Open PowerShell in the project directory and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

7. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

8. Copy the environment example and edit the connection string and secret:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

   Set `DATABASE_URL` to `mysql+pymysql://root:YOUR_MYSQL_PASSWORD@127.0.0.1:3306/groczy_db?charset=utf8mb4`. If your XAMPP root user has no password, leave the password section empty (`root:@`). Set `SECRET_KEY` to a long random value. The app loads `.env` through Flask's dotenv support when running `flask`; for direct `python app.py`, PowerShell environment variables can be set for the current shell with `$env:DATABASE_URL='...'` and `$env:SECRET_KEY='...'`.

9. Seed sample catalog products (repeatable; existing named products are left intact):

   ```powershell
   python scripts/seed_data.py
   ```

10. Create an administrator. The password is entered interactively and hashed; it is never stored in the script:

   ```powershell
   python scripts/create_admin.py
   ```

11. Start the web application:

   ```powershell
   python app.py
   ```

12. Open `http://127.0.0.1:5000/`. phpMyAdmin remains at `http://localhost/phpmyadmin/`.

The app uses its Flask development server. XAMPP Apache does not execute the Python app. Keep MySQL running while using Groczy.

## Useful pages

- Catalog and search: `/products`
- Customer registration/sign in: `/register`, `/login`
- Cart, wishlist, orders and notifications: `/cart`, `/wishlist`, `/orders`, `/notifications`
- Administrator workspace: `/admin` after signing in as an administrator
- JSON product API: `/api/products?q=milk`

## Recommendation logic

The transparent recommendation endpoint first finds the customer's most frequently ordered product category and returns available active products in that category. If the customer has no order history (or that category has no available products), the service returns available active featured/recent products. Guests receive general popular picks. This is a rule-based approach, not machine learning. No location data is collected, and the interface does not claim area-specific recommendations.

## Back-in-stock flow

Wishlist rows double as availability subscriptions. On an admin stock update from zero to a positive number, the backend creates one unread notification per wishlist customer, with a unique event key. Customers can view and mark messages read in `/notifications`. No external email/SMS/WhatsApp provider is configured.

## API and security notes

All writes are protected by Flask-WTF CSRF validation (forms use a hidden token; JavaScript sends the token in `X-CSRFToken`). Passwords use Werkzeug's password hashing. Sessions are server-signed, cookies are HTTP-only and SameSite=Lax, and `COOKIE_SECURE=1` should be used behind HTTPS. Admin authorization is checked in Flask routes, not only in the UI. Product price and stock are always read server-side. Order creation rechecks stock and uses row locks/one SQLAlchemy transaction; for strong concurrent inventory locking use MySQL/InnoDB. Customer order queries are scoped to the signed-in account. Payment status stays **Not Paid**.

Product photos use Unsplash URLs and a placeholder fallback when unavailable. Product management accepts image URLs; local image upload is not currently exposed.

## Tests

With the virtual environment active, run:

```powershell
python -m pytest -q
```

Tests use an isolated in-memory SQLite database and do not require XAMPP. To check actual MySQL integration, configure `.env`, start XAMPP MySQL, then run the app and exercise the documented workflows. No real payment test exists because online payments are deliberately blocked.

## Troubleshooting

- **Can't connect / MySQL connection refused:** Start MySQL in XAMPP and check port 3306. If another MySQL server is using it, adjust XAMPP or the URL port.
- **Access denied:** Set the correct XAMPP root password in `DATABASE_URL`.
- **Unknown database:** Import `groczy.sql` in phpMyAdmin before starting the app.
- **Missing table or column:** Reimport the SQL schema into a clean `groczy_db`; `scripts/init_db.py` can create ORM tables for development but does not add SQL indexes or seed categories.
- **PowerShell blocks activation:** Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.
- **Port 5000 busy:** Stop the other process or change the port in the `app.run` line at the bottom of `app.py`.

## Project layout

`app.py` holds the SQLAlchemy models and route/service logic, `templates/` holds shared Jinja pages, `static/` contains the CSS and vanilla JS, `scripts/` contains database initialization, sample seed, and secure admin creation commands, `groczy.sql` is the MySQL schema, and `tests/` contains application workflow tests.
