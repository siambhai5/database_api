from flask import Flask, jsonify, Response
from urllib.parse import unquote
import sqlite3
import json

app = Flask(__name__)

# =========================
# Database Setup
# =========================
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
# Payment Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txnid TEXT,
            amount TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# =========================
# Add User API
# =========================
@app.route('/add_user/<path:username>/<path:password>')
def add_user(username, password):

    # URL Decode
    username = unquote(username)
    password = unquote(password)

    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()

        user_id = cursor.lastrowid

        conn.close()

        return jsonify({
            "status": True,
            "message": "User created successfully",
            "user": {
                "id": user_id,
                "username": username
            }
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "status": False,
            "message": "User already exists"
        })


# =========================
# Verify API
# =========================
@app.route('/verify/<path:username>/<path:password>')
def verify(username, password):

    # URL Decode
    username = unquote(username)
    password = unquote(password)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        return jsonify({
            "status": True,
            "message": "Login successful",
            "user": {
                "id": user[0],
                "username": user[1]
            }
        })

    else:

        return jsonify({
            "status": False,
            "message": "Invalid username or password"
        })


# =========================
# Home API
# =========================
@app.route('/')
def home():

    data = {
        "api": "Online",
        "developer": "Siam",
        "description": "User & Payment Management API",

        "commands": {

            "/add_user/<username>/<password>": {
                "method": "GET",
                "description": "নতুন user তৈরি করবে",
                "example": "/add_user/siam/1234"
            },

            "/verify/<username>/<password>": {
                "method": "GET",
                "description": "User login verify করবে",
                "example": "/verify/siam/1234"
            },

            "/change_pass/<username>/<old_password>/<new_password>": {
                "method": "GET",
                "description": "Password পরিবর্তন করবে",
                "example": "/change_pass/siam/1234/5678"
            },

            "/change_username/<old_username>/<old_password>/<new_username>": {
                "method": "GET",
                "description": "Username পরিবর্তন করবে",
                "example": "/change_username/siam/1234/siam123"
            },

            "/add_money/<txnid>/<amount>": {
                "method": "GET",
                "description": "Payment database এ save করবে",
                "example": "/add_money/75D48T60/300"
            },

            "/verify_payment/<txnid>/<amount>": {
                "method": "GET",
                "description": "Payment verify করবে",
                "example": "/verify_payment/75D48T60/300"
            },

            "/remove_txnid/<txnid>": {
                "method": "GET",
                "description": "Database থেকে TXNID delete করবে",
                "example": "/remove_txnid/75D48T60"
            }

        },

        "notes": [
            "সব parameter URL encoded support করে",
            "সব API JSON response return করে",
            "Username unique হতে হবে"
        ]
    }

    return Response(
        json.dumps(data, indent=4, ensure_ascii=False),
        mimetype="application/json"
    )

# =========================
# Change Password API
# =========================
@app.route('/change_pass/<path:username>/<path:old_password>/<path:new_password>')
def change_password(username, old_password, new_password):

    try:

        # URL Decode
        username = unquote(username)
        old_password = unquote(old_password)
        new_password = unquote(new_password)

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # পুরাতন username + password check
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, old_password)
        )

        user = cursor.fetchone()

        if user:

            # password update
            cursor.execute(
                "UPDATE users SET password=? WHERE username=?",
                (new_password, username)
            )

            conn.commit()

            # updated data fetch
            cursor.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            )

            updated_user = cursor.fetchone()

            conn.close()

            data = {
                "status": True,
                "message": "Password changed successfully",
                "user": {
                    "id": updated_user[0],
                    "username": updated_user[1],
                    "password": updated_user[2]
                }
            }

        else:

            conn.close()

            data = {
                "status": False,
                "message": "Invalid username or old password"
            }

        return Response(
            json.dumps(data, indent=4),
            mimetype='application/json'
        )

    except Exception as e:

        return Response(
            json.dumps({
                "status": False,
                "error": str(e)
            }, indent=4),
            mimetype='application/json'
        )
# =========================
# Change Username API
# =========================
@app.route('/change_username/<path:old_username>/<path:old_password>/<path:new_username>')
def change_username(old_username, old_password, new_username):

    # URL Decode
    old_username = unquote(old_username)
    old_password = unquote(old_password)
    new_username = unquote(new_username)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # পুরাতন username + password check
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (old_username, old_password)
    )

    user = cursor.fetchone()

    # যদি username/password সঠিক হয়
    if user:

        # নতুন username আগে থেকেই আছে কিনা check
        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (new_username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            conn.close()

            data = {
                "status": False,
                "message": "New username already exists"
            }

        else:

            # username update
            cursor.execute(
                "UPDATE users SET username=? WHERE username=?",
                (new_username, old_username)
            )

            conn.commit()

            # updated data fetch
            cursor.execute(
                "SELECT * FROM users WHERE username=?",
                (new_username,)
            )

            updated_user = cursor.fetchone()

            conn.close()

            data = {
                "status": True,
                "message": "Username changed successfully",
                "user": {
                    "id": updated_user[0],
                    "username": updated_user[1],
                    "password": updated_user[2]
                }
            }

    else:

        conn.close()

        data = {
            "status": False,
            "message": "Invalid old username or password"
        }

    return Response(
        json.dumps(data, indent=4),
        mimetype='application/json'
    )

# =========================
# Add Money API
# =========================
@app.route('/add_money/<path:txnid>/<path:amount>')
def add_money(txnid, amount):

    # URL Decode
    txnid = unquote(txnid)
    amount = unquote(amount)

    try:

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Save payment info
        cursor.execute(
            "INSERT INTO payments (txnid, amount) VALUES (?, ?)",
            (txnid, amount)
        )

        conn.commit()

        payment_id = cursor.lastrowid

        conn.close()

        return jsonify({
            "status": True,
            "message": "Payment added successfully",
            "payment": {
                "id": payment_id,
                "txnid": txnid,
                "amount": amount
            }
        })

    except Exception as e:

        return jsonify({
            "status": False,
            "error": str(e)
        })


# =========================
# Verify Payment API
# =========================
@app.route('/verify_payment/<path:txnid>/<path:amount>')
def verify_payment(txnid, amount):

    # URL Decode
    txnid = unquote(txnid)
    amount = unquote(amount)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM payments WHERE txnid=? AND amount=?",
        (txnid, amount)
    )

    payment = cursor.fetchone()

    conn.close()

    if payment:

        return jsonify({
            "status": True,
            "message": "Payment verified successfully",
            "payment": {
                "id": payment[0],
                "txnid": payment[1],
                "amount": payment[2]
            }
        })

    else:

        return jsonify({
            "status": False,
            "message": "Invalid txnid or amount"
        })

# =========================
# Remove TXNID API
# =========================
@app.route('/remove_txnid/<path:txnid>')
def remove_txnid(txnid):

    # URL Decode
    txnid = unquote(txnid)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # আগে check করবে txnid আছে কিনা
    cursor.execute(
        "SELECT * FROM payments WHERE txnid=?",
        (txnid,)
    )

    payment = cursor.fetchone()

    # txnid পাওয়া গেলে delete করবে
    if payment:

        cursor.execute(
            "DELETE FROM payments WHERE txnid=?",
            (txnid,)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "status": True,
            "message": "TXNID removed successfully",
            "txnid": txnid
        })

    else:

        conn.close()

        return jsonify({
            "status": False,
            "message": "TXNID not found"
        })

# =========================
# Run Server
# =========================
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)