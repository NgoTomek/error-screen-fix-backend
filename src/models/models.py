# src/models/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

class SubscriptionTier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(128), unique=True, nullable=False)  # Firebase UID
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    display_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    subscription = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    
    # Statistics
    analysis_count = db.Column(db.Integer, default=0)
    solutions_shared = db.Column(db.Integer, default=0)
    reputation = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    analyses = db.relationship('ErrorAnalysis', backref='user', lazy='dynamic')
    shared_solutions = db.relationship('SharedSolution', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    votes = db.relationship('Vote', backref='user', lazy='dynamic')
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'email': self.email,
            'username': self.username,
            'displayName': self.display_name,
            'bio': self.bio,
            'avatarUrl': self.avatar_url,
            'role': self.role.value,
            'subscription': self.subscription.value,
            'analysisCount': self.analysis_count,
            'solutionsShared': self.solutions_shared,
            'reputation': self.reputation,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastLogin': self.last_login.isoformat() if self.last_login else None
        }

class ErrorAnalysis(db.Model):
    __tablename__ = 'error_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Error details
    error_type = db.Column(db.String(100))
    error_description = db.Column(db.Text)
    category = db.Column(db.String(50))
    severity = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    
    # Analysis data
    screenshot_url = db.Column(db.String(255))
    additional_context = db.Column(db.Text)
    solutions = db.Column(db.JSON)  # Store solutions as JSON
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysisId': self.analysis_id,
            'userId': self.user_id,
            'errorType': self.error_type,
            'errorDescription': self.error_description,
            'category': self.category,
            'severity': self.severity,
            'confidence': self.confidence,
            'screenshotUrl': self.screenshot_url,
            'additionalContext': self.additional_context,
            'solutions': self.solutions,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'isPublic': self.is_public,
            'viewCount': self.view_count
        }

class SharedSolution(db.Model):
    __tablename__ = 'shared_solutions'
    
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    analysis_id = db.Column(db.Integer, db.ForeignKey('error_analyses.id'))
    
    # Solution details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    error_type = db.Column(db.String(100))
    category = db.Column(db.String(50))
    tags = db.Column(db.JSON)  # Array of tags
    
    # Solution content
    problem_description = db.Column(db.Text)
    solution_steps = db.Column(db.JSON)  # Array of steps
    difficulty = db.Column(db.String(20))
    estimated_time = db.Column(db.String(50))
    success_rate = db.Column(db.Float)
    
    # Engagement metrics
    view_count = db.Column(db.Integer, default=0)
    upvote_count = db.Column(db.Integer, default=0)
    downvote_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    bookmark_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='solution', lazy='dynamic', cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='solution', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='solution', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_author=True):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'errorType': self.error_type,
            'category': self.category,
            'tags': self.tags or [],
            'problemDescription': self.problem_description,
            'solutionSteps': self.solution_steps or [],
            'difficulty': self.difficulty,
            'estimatedTime': self.estimated_time,
            'successRate': self.success_rate,
            'viewCount': self.view_count,
            'upvoteCount': self.upvote_count,
            'downvoteCount': self.downvote_count,
            'commentCount': self.comment_count,
            'bookmarkCount': self.bookmark_count,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_author and self.author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'displayName': self.author.display_name,
                'avatarUrl': self.author.avatar_url,
                'reputation': self.author.reputation
            }
        
        return data

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    solution_id = db.Column(db.Integer, db.ForeignKey('shared_solutions.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    
    content = db.Column(db.Text, nullable=False)
    is_edited = db.Column(db.Boolean, default=False)
    upvote_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for replies
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def to_dict(self, include_replies=False):
        data = {
            'id': self.id,
            'content': self.content,
            'isEdited': self.is_edited,
            'upvoteCount': self.upvote_count,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'displayName': self.author.display_name,
                'avatarUrl': self.author.avatar_url
            }
        }
        
        if include_replies:
            data['replies'] = [reply.to_dict() for reply in self.replies]
        
        return data

class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    solution_id = db.Column(db.Integer, db.ForeignKey('shared_solutions.id'), nullable=False)
    is_upvote = db.Column(db.Boolean, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent multiple votes
    __table_args__ = (db.UniqueConstraint('user_id', 'solution_id', name='_user_solution_vote'),)

class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    solution_id = db.Column(db.Integer, db.ForeignKey('shared_solutions.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'solution_id', name='_user_solution_bookmark'),)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tier = db.Column(db.Enum(SubscriptionTier), nullable=False)
    
    # Stripe/Payment info
    stripe_customer_id = db.Column(db.String(255))
    stripe_subscription_id = db.Column(db.String(255))
    
    # Subscription details
    status = db.Column(db.String(50))  # active, canceled, past_due
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

