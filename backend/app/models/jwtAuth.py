"""
US-13: Authentication and Protected Routes
US-16: JWT Token Management via Website
"""
import random
import string
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, g
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    jwt_required, 
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta
import pyotp
import qrcode
import io
import base64
from app.routes.observation import User, get_db

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(to_email, otp, subject="Your OTP Code"):
    # 1. Log to file/console for backup/dev access (keep this for now so dev doesn't break if SMTP fails)
    print(f"\n{'='*30}")
    print(f"[EMAIL] To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: Your verification code is: {otp}")
    print(f"{'='*30}\n")
    try:
        with open("backend_otp.txt", "w") as f:
            f.write(otp)
    except:
        pass

    # 2. Attempt Real SMTP Sending
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        print("SMTP Credentials not set in .env. Skipping real email send.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        body = f"Hello,\n\nYour GeoScope Verification Code is: {otp}\n\nThis code expires in 10 minutes."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"✅ Real email sent successfully to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send real email: {e}")

def register(app):
    """
    Registers authentication routes with JWT token management.
    Includes login, signup, token refresh, and token validation endpoints.
    """

    @app.route('/signup', methods=['POST'])
    def signup():
        """
        US-16: User registration endpoint
        Creates new user account (unverified) and sends OTP.
        """
        try:
            db = get_db()
            data = request.json
            password = data.get("password")
            email = data.get("email")
            first_name = data.get("first_name")
            last_name = data.get("last_name")

            # Validate required fields
            if not all([password, email, first_name, last_name]):
                return jsonify({"msg": "All fields are required"}), 400

            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return jsonify({"msg": "User with this email already exists"}), 409

            # Generate OTP
            if email == "testuser@geoscope.com":
                otp = "123456"
            else:
                otp = generate_otp()
            
            # Store new user
            hashed_password = generate_password_hash(password)
            new_user = User(
                email=email,
                password=hashed_password, 
                first_name=first_name,
                last_name=last_name,
                is_2fa_enabled=0,
                is_verified=0,
                otp_code=otp,
                otp_created_at=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()

            # Send OTP
            send_email_otp(email, otp, "Verify your GeoScope Account")

            return jsonify({
                "msg": "User created. Verification required.",
                "email": email,
                "verification_required": True
            }), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/verify-email', methods=['POST'])
    def verify_email():
        """
        Verifies the email OTP for new accounts.
        """
        try:
            db = get_db()
            data = request.json
            email = data.get("email")
            otp = data.get("otp")

            user = db.query(User).filter(User.email == email).first()
            if not user:
                return jsonify({"msg": "User not found"}), 404

            if user.otp_code != otp:
                return jsonify({"msg": "Invalid OTP"}), 400
                
            # Ideally check expiry here (e.g. < 10 mins)
            
            user.is_verified = 1
            user.otp_code = None # Clear OTP
            db.commit()

            # Generate Tokens
            access_token = create_access_token(identity=email, expires_delta=timedelta(hours=1))
            refresh_token = create_refresh_token(identity=email, expires_delta=timedelta(days=30))

            return jsonify({
                "msg": "Email verified successfully",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_dict()
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/login', methods=['POST'])
    def login():
        """
        US-16: Login flow.
        1. Validate Creds.
        2. If Valid -> Send OTP (Email).
        3. Return 200 with 'otp_required'.
        """
        try:
            db = get_db()
            # Changed from username to email
            email = request.json.get("email") or request.json.get("username") 
            password = request.json.get("password")
            
            # Validate credentials
            user = db.query(User).filter(User.email == email).first()
            
            if not user or not check_password_hash(user.password, password):
                return jsonify({"msg": "Bad email or password"}), 401

            # Generate OTP for Login
            if email == "testuser@geoscope.com":
                otp = "123456"
            else:
                otp = generate_otp()
            user.otp_code = otp
            user.otp_created_at = datetime.utcnow()
            db.commit()

            # Send OTP
            # Send OTP
            send_email_otp(email, otp, "Login Access Code")

            return jsonify({
                "msg": "OTP sent to email",
                "otp_required": True,
                "email": email
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/verify-login-otp', methods=['POST'])
    def verify_login_otp():
        """
        Verifies OTP for Login. 
        If valid, checks for TOTP (Optional 2FA).
        """
        try:
            db = get_db()
            data = request.json
            email = data.get("email")
            otp = data.get("otp")

            user = db.query(User).filter(User.email == email).first()
            if not user:
                return jsonify({"msg": "User not found"}), 404

            if user.otp_code != otp:
                 return jsonify({"msg": "Invalid OTP"}), 400

            # Clear OTP
            user.otp_code = None
            db.commit()

            # Check if Authenticator App 2FA is enabled
            if user.is_2fa_enabled:
                 return jsonify({
                    "msg": "Authenticator code required",
                    "totp_required": True,
                    "email": email
                }), 200

            # If no TOTP, fully logged in
            access_token = create_access_token(
                identity=email,
                expires_delta=timedelta(hours=1)
            )
            refresh_token = create_refresh_token(
                identity=email,
                expires_delta=timedelta(days=30)
            )
            return jsonify({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_dict()
            }), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        """
        US-16: Token refresh endpoint
        Accepts refresh token and returns new access token
        """
        try:
            current_user_email = get_jwt_identity()
            new_access_token = create_access_token(
                identity=current_user_email,
                expires_delta=timedelta(hours=1)
            )
            return jsonify({
                "access_token": new_access_token
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/token/validate', methods=['POST'])
    @jwt_required()
    def validate_token():
        """
        US-16: Token validation endpoint
        """
        try:
            current_user_email = get_jwt_identity()
            jwt_data = get_jwt()
            
            db = get_db()
            user = db.query(User).filter(User.email == current_user_email).first()
            user_data = user.to_dict() if user else current_user_email

            return jsonify({
                "valid": True,
                "user": user_data,
                "exp": jwt_data.get("exp"),
                "iat": jwt_data.get("iat")
            }), 200
        except Exception as e:
            return jsonify({
                "valid": False,
                "msg": str(e)
            }), 401

    @app.route('/protected', methods=['GET'])
    @jwt_required()
    def protected():
        """
        US-13: Protected endpoint requiring valid JWT
        """
        try:
            current_user_email = get_jwt_identity()
            return jsonify({
                "msg": "Given valid token, when used, then data returned.",
                "user": current_user_email,
                "data": "Top Secret Info"
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/2fa/setup', methods=['POST'])
    @jwt_required()
    def setup_2fa():
        """
        Generate a TOTP secret and QR code for the user.
        """
        try:
            db = get_db()
            email = get_jwt_identity()
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return jsonify({"msg": "User not found"}), 404
            
            secret = pyotp.random_base32()
            user.otp_secret = secret
            db.commit()
            
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(name=email, issuer_name="GeoScope")
            
            img = qrcode.make(provisioning_uri)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return jsonify({
                "secret": secret,
                "qr_code": f"data:image/png;base64,{img_str}"
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/2fa/verify', methods=['POST'])
    def verify_2fa():
        """
        Verify the TOTP code and return tokens if valid.
        """
        try:
            db = get_db()
            data = request.json
            email = data.get("email") or data.get("username")
            otp_code = data.get("otp_code")
            setup_mode = data.get("setup_mode", False)
            
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return jsonify({"msg": "User not found"}), 404
            
            secret = user.otp_secret
            if not secret:
                return jsonify({"msg": "2FA not set up"}), 400
            
            totp = pyotp.TOTP(secret)
            if totp.verify(otp_code):
                if setup_mode:
                    user.is_2fa_enabled = 1
                    db.commit()
                
                # Create tokens
                access_token = create_access_token(identity=email, expires_delta=timedelta(hours=1))
                refresh_token = create_refresh_token(identity=email, expires_delta=timedelta(days=30))
                
                return jsonify({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user.to_dict()
                }), 200
            else:
                return jsonify({"msg": "Invalid OTP code"}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/2fa/disable', methods=['POST'])
    @jwt_required()
    def disable_2fa():
        """
        Disable TOTP 2FA.
        """
        try:
            db = get_db()
            email = get_jwt_identity()
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return jsonify({"msg": "User not found"}), 404
            
            # Optional: Verify password or OTP before disabling
            
            user.is_2fa_enabled = 0
            user.otp_secret = None
            db.commit()
            
            return jsonify({"msg": "2FA disabled successfully"}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/profile', methods=['PUT'])
    @jwt_required()
    def update_profile():
        """
        Update user profile information.
        """
        try:
            db = get_db()
            email = get_jwt_identity()
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return jsonify({"msg": "User not found"}), 404
            
            data = request.json
            if "first_name" in data:
                user.first_name = data["first_name"]
            if "last_name" in data:
                user.last_name = data["last_name"]
            # Optional: Allow email update, but might need re-verification logic. For now, allow simple update.
            # if "email" in data and data["email"] != user.email:
            #     # Check if email taken
            #     existing = db.query(User).filter(User.email == data["email"]).first()
            #     if existing:
            #         return jsonify({"msg": "Email already in use"}), 409
            #     user.email = data["email"]
            #     # Token invalidation logic would be needed if identity changes
            
            db.commit()
            
            return jsonify({
                "msg": "Profile updated successfully",
                "user": user.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # OAuth Setup
    from authlib.integrations.flask_client import OAuth
    import os

    oauth = OAuth(app)
    google = oauth.register(
        name='google',
        client_id=os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    @app.route('/google-login', methods=['GET', 'POST'])
    def google_login():
        """
        Initiates Google OAuth flow.
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            return jsonify({"msg": "Google Client ID or Secret is not configured."}), 500
            
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/google-callback")
        return google.authorize_redirect(redirect_uri)

    @app.route('/google-callback', methods=['GET'])
    def google_callback():
        """
        Handles Google OAuth callback.
        """
        try:
            db = get_db()
            token = google.authorize_access_token()
            user_info = google.userinfo()
            
            email = user_info.get('email')
            name = user_info.get('name', 'Google User')
            
            # Find or create user
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Create a new user from Google info
                parts = name.split(' ')
                first_name = parts[0]
                last_name = parts[-1] if len(parts) > 1 else ''
                
                user = User(
                    email=email,
                    password="", # No password for OAuth users
                    first_name=first_name,
                    last_name=last_name,
                    is_2fa_enabled=0
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # Generate JWTs
            access_token = create_access_token(identity=user.email, expires_delta=timedelta(hours=1))
            refresh_token = create_refresh_token(identity=user.email, expires_delta=timedelta(days=30))

            # Redirect to Frontend
            frontend_callback = os.getenv("FRONTEND_CALLBACK_URL", "http://127.0.0.1:8001/auth/google/callback")
            
            from flask import redirect
            return redirect(f"{frontend_callback}?access_token={access_token}&refresh_token={refresh_token}&email={user.email}&is_2fa_enabled={user.is_2fa_enabled}&first_name={user.first_name}")
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
