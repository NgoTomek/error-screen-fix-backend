# src/middleware/auth.py

import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps
from flask import request, jsonify
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK (optional for development)
cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if cred_path and os.path.exists(cred_path) and not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    # Development mode without Firebase
    db = None
    logger.warning("Firebase not initialized - running in development mode")

def verify_token():
    """Verify Firebase ID token from request headers"""
    if not db:
        # Development mode - skip token verification
        return {'uid': 'dev-user', 'email': 'dev@example.com'}
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    id_token = auth_header.split('Bearer ')[1]
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_info = verify_token()
        if not token_info:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Add user info to request context
        request.user = token_info
        request.uid = token_info.get('uid')
        request.email = token_info.get('email')
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token_info = verify_token()
            if not token_info:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get user's custom claims
            user_roles = token_info.get('roles', [])
            
            # Check if user has any of the required roles
            if not any(role in user_roles for role in roles):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            request.user = token_info
            request.uid = token_info.get('uid')
            request.email = token_info.get('email')
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def optional_auth(f):
    """Decorator for routes that work with or without authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_info = verify_token()
        if token_info:
            request.user = token_info
            request.uid = token_info.get('uid')
            request.email = token_info.get('email')
        else:
            request.user = None
            request.uid = None
            request.email = None
        
        return f(*args, **kwargs)
    
    return decorated_function

def set_custom_user_claims(uid, claims):
    """Set custom claims for a user (admin, moderator, etc.)"""
    try:
        auth.set_custom_user_claims(uid, claims)
        return True
    except Exception as e:
        logger.error(f"Error setting custom claims: {str(e)}")
        return False

def get_or_create_user_profile(uid, email=None, display_name=None):
    """Get or create user profile in Firestore"""
    if not db:
        # Development mode - return mock profile
        return {
            'uid': uid,
            'email': email or 'dev@example.com',
            'displayName': display_name or 'Dev User',
            'role': 'user',
            'subscription': 'free',
            'analysisCount': 0,
            'solutionsShared': 0,
            'reputation': 0
        }
    
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        return user_doc.to_dict()
    else:
        # Create new user profile
        user_data = {
            'uid': uid,
            'email': email,
            'displayName': display_name,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
            'role': 'user',
            'subscription': 'free',
            'analysisCount': 0,
            'solutionsShared': 0,
            'reputation': 0,
            'bio': '',
            'avatarUrl': '',
            'settings': {
                'emailNotifications': True,
                'communityNotifications': True,
                'darkMode': False
            }
        }
        
        user_ref.set(user_data)
        return user_data

