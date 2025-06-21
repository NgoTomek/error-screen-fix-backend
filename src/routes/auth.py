# src/routes/auth.py

from flask import Blueprint, request, jsonify
from src.models.models import db, User, UserRole, SubscriptionTier
from src.middleware.auth import require_auth, verify_token, get_or_create_user_profile
from datetime import datetime
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user after Firebase authentication"""
    try:
        token_info = verify_token()
        if not token_info:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        uid = token_info.get('uid')
        email = token_info.get('email')
        
        # Check if user already exists
        existing_user = User.query.filter_by(uid=uid).first()
        if existing_user:
            existing_user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'message': 'User already registered',
                'user': existing_user.to_dict()
            }), 200
        
        # Get additional data from request
        data = request.get_json()
        username = data.get('username')
        display_name = data.get('displayName', token_info.get('name', ''))
        
        # Validate username uniqueness
        if username:
            username_exists = User.query.filter_by(username=username).first()
            if username_exists:
                return jsonify({'error': 'Username already taken'}), 400
        
        # Create new user
        new_user = User(
            uid=uid,
            email=email,
            username=username,
            display_name=display_name,
            role=UserRole.USER,
            subscription=SubscriptionTier.FREE,
            last_login=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create Firestore profile
        get_or_create_user_profile(uid, email, display_name)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Verify token and update last login"""
    try:
        token_info = verify_token()
        if not token_info:
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        uid = token_info.get('uid')
        
        # Get or create user
        user = User.query.filter_by(uid=uid).first()
        if not user:
            # Auto-register user if not exists
            email = token_info.get('email')
            user = User(
                uid=uid,
                email=email,
                display_name=token_info.get('name', ''),
                role=UserRole.USER,
                subscription=SubscriptionTier.FREE
            )
            db.session.add(user)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Get Firestore profile
        profile = get_or_create_user_profile(uid, user.email, user.display_name)
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user's profile"""
    try:
        user = User.query.filter_by(uid=request.uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500

@auth_bp.route('/auth/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        user = User.query.filter_by(uid=request.uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'username' in data and data['username'] != user.username:
            # Check username availability
            username_exists = User.query.filter_by(username=data['username']).first()
            if username_exists:
                return jsonify({'error': 'Username already taken'}), 400
            user.username = data['username']
        
        if 'displayName' in data:
            user.display_name = data['displayName']
        
        if 'bio' in data:
            user.bio = data['bio']
        
        if 'avatarUrl' in data:
            user.avatar_url = data['avatarUrl']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/auth/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        exists = User.query.filter_by(username=username).first() is not None
        
        return jsonify({
            'available': not exists
        }), 200
        
    except Exception as e:
        logger.error(f"Username check error: {str(e)}")
        return jsonify({'error': 'Failed to check username'}), 500

@auth_bp.route('/auth/subscription', methods=['GET'])
@require_auth
def get_subscription():
    """Get user's subscription details"""
    try:
        user = User.query.filter_by(uid=request.uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get subscription limits based on tier
        limits = {
            'free': {
                'analysesPerMonth': 5,
                'features': ['basic_analysis', 'export_json']
            },
            'pro': {
                'analysesPerMonth': -1,  # unlimited
                'features': ['advanced_analysis', 'export_all', 'priority_support', 'community_access']
            },
            'enterprise': {
                'analysesPerMonth': -1,
                'features': ['advanced_analysis', 'export_all', 'priority_support', 'community_access', 
                           'team_collaboration', 'api_access', 'custom_integrations']
            }
        }
        
        return jsonify({
            'tier': user.subscription.value,
            'limits': limits.get(user.subscription.value, limits['free']),
            'analysisCount': user.analysis_count
        }), 200
        
    except Exception as e:
        logger.error(f"Subscription fetch error: {str(e)}")
        return jsonify({'error': 'Failed to fetch subscription'}), 500

