from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    from database.models import User, db  # ✅ Move import inside function to avoid circular import

    data = request.get_json()
    name, email, phone, password = data.get("name"), data.get("email"), data.get("phone"), data.get("password")

    if not all([name, email, phone, password]):
        return jsonify({"success": False, "message": "All fields are required!"})

    if User.query.filter((User.email == email) | (User.phone == phone)).first():
        return jsonify({"success": False, "message": "Email or Phone already registered!"})

    try:
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(name=name, email=email, phone=phone, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"success": True, "message": "Signup successful!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "An error occurred."})

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from database.models import User, db  # ✅ Move import inside function to avoid circular import
    
    data = request.get_json()
    email_or_phone, password = data.get('email_or_phone'), data.get('password')

    user = User.query.filter((User.email == email_or_phone) | (User.phone == email_or_phone)).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        print(f"Session after login: {session}")
        return jsonify({"success": True, "message": "Login successful!",
            "user": {"id": user.id, "name": user.name, "email": user.email}}), 200
    
    return jsonify({"success": False, "message": "Invalid credentials."}), 401

# In auth.py
@auth_bp.route("/get-user", methods=["GET"])
def get_user():
    from database.models import User
    
    user_id = session.get("user_id")
    print("Session contents:", session)
    print(f"Retrieved user_id from session: {user_id}")
    if not user_id:
        return jsonify({"success": False, "message": "User not logged in."}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
    
    return jsonify({"success": True, "user": {"id": user.id, "name": user.name, "email": user.email}}), 200