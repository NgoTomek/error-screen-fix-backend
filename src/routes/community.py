# src/routes/community.py

from flask import Blueprint, request, jsonify
from src.models.models import db, User, SharedSolution, Comment, Vote, Bookmark
from src.middleware.auth import require_auth, optional_auth
from sqlalchemy import desc, or_, and_, func
from datetime import datetime
import logging

community_bp = Blueprint('community', __name__)
logger = logging.getLogger(__name__)

@community_bp.route('/community/solutions', methods=['GET'])
@optional_auth
def get_solutions():
    """Get shared solutions with filtering and pagination"""
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('perPage', 20, type=int)
        
        # Filters
        category = request.args.get('category')
        error_type = request.args.get('errorType')
        difficulty = request.args.get('difficulty')
        search = request.args.get('search')
        sort_by = request.args.get('sortBy', 'recent')  # recent, popular, top
        
        # Build query
        query = SharedSolution.query
        
        if category:
            query = query.filter_by(category=category)
        
        if error_type:
            query = query.filter_by(error_type=error_type)
        
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    SharedSolution.title.ilike(search_pattern),
                    SharedSolution.description.ilike(search_pattern),
                    SharedSolution.problem_description.ilike(search_pattern)
                )
            )
        
        # Sorting
        if sort_by == 'popular':
            query = query.order_by(desc(SharedSolution.view_count))
        elif sort_by == 'top':
            query = query.order_by(desc(SharedSolution.upvote_count))
        else:  # recent
            query = query.order_by(desc(SharedSolution.created_at))
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Check user's votes and bookmarks if authenticated
        solutions_data = []
        for solution in paginated.items:
            solution_dict = solution.to_dict()
            
            if request.uid:
                # Get user from database
                user = User.query.filter_by(uid=request.uid).first()
                if user:
                    # Check if user voted
                    vote = Vote.query.filter_by(
                        user_id=user.id,
                        solution_id=solution.id
                    ).first()
                    
                    solution_dict['userVote'] = {
                        'voted': vote is not None,
                        'isUpvote': vote.is_upvote if vote else None
                    }
                    
                    # Check if user bookmarked
                    bookmark = Bookmark.query.filter_by(
                        user_id=user.id,
                        solution_id=solution.id
                    ).first()
                    
                    solution_dict['isBookmarked'] = bookmark is not None
            
            solutions_data.append(solution_dict)
        
        return jsonify({
            'solutions': solutions_data,
            'pagination': {
                'page': page,
                'perPage': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'hasNext': paginated.has_next,
                'hasPrev': paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching solutions: {str(e)}")
        return jsonify({'error': 'Failed to fetch solutions'}), 500

@community_bp.route('/community/solutions/<int:solution_id>', methods=['GET'])
@optional_auth
def get_solution(solution_id):
    """Get a specific solution with full details"""
    try:
        solution = SharedSolution.query.get_or_404(solution_id)
        
        # Increment view count
        solution.view_count += 1
        db.session.commit()
        
        solution_data = solution.to_dict()
        
        # Add user interaction data if authenticated
        if request.uid:
            user = User.query.filter_by(uid=request.uid).first()
            if user:
                vote = Vote.query.filter_by(
                    user_id=user.id,
                    solution_id=solution.id
                ).first()
                
                solution_data['userVote'] = {
                    'voted': vote is not None,
                    'isUpvote': vote.is_upvote if vote else None
                }
                
                bookmark = Bookmark.query.filter_by(
                    user_id=user.id,
                    solution_id=solution.id
                ).first()
                
                solution_data['isBookmarked'] = bookmark is not None
        
        return jsonify(solution_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching solution: {str(e)}")
        return jsonify({'error': 'Failed to fetch solution'}), 500

@community_bp.route('/community/solutions', methods=['POST'])
@require_auth
def create_solution():
    """Share a new solution"""
    try:
        user = User.query.filter_by(uid=request.uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'solutionSteps']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create solution
        solution = SharedSolution(
            author_id=user.id,
            title=data['title'],
            description=data['description'],
            error_type=data.get('errorType'),
            category=data.get('category'),
            tags=data.get('tags', []),
            problem_description=data.get('problemDescription'),
            solution_steps=data['solutionSteps'],
            difficulty=data.get('difficulty'),
            estimated_time=data.get('estimatedTime'),
            success_rate=data.get('successRate')
        )
        
        # Link to analysis if provided
        if 'analysisId' in data:
            from src.models.models import ErrorAnalysis
            analysis = ErrorAnalysis.query.filter_by(
                analysis_id=data['analysisId'],
                user_id=user.id
            ).first()
            if analysis:
                solution.analysis_id = analysis.id
        
        db.session.add(solution)
        
        # Update user stats
        user.solutions_shared += 1
        user.reputation += 10  # Award reputation for sharing
        
        db.session.commit()
        
        return jsonify({
            'message': 'Solution shared successfully',
            'solution': solution.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating solution: {str(e)}")
        return jsonify({'error': 'Failed to share solution'}), 500

@community_bp.route('/community/solutions/<int:solution_id>/vote', methods=['POST'])
@require_auth
def vote_solution(solution_id):
    """Vote on a solution"""
    try:
        user = User.query.filter_by(uid=request.uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        solution = SharedSolution.query.get_or_404(solution_id)
        
        data = request.get_json()
        is_upvote = data.get('isUpvote', True)
        
        # Check existing vote
        existing_vote = Vote.query.filter_by(
            user_id=user.id,
            solution_id=solution.id
        ).first()
        
        if existing_vote:
            if existing_vote.is_upvote == is_upvote:
                # Remove vote (toggle off)
                db.session.delete(existing_vote)
                
                if is_upvote:
                    solution.upvote_count -= 1
                else:
                    solution.downvote_count -= 1
                
                # Update author reputation
                solution.author.reputation -= 5 if is_upvote else 2
                
                db.session.commit()
                
                return jsonify({
                    'message': 'Vote removed',
                    'upvoteCount': solution.upvote_count,
                    'downvoteCount': solution.downvote_count
                }), 200
            else:
                # Change vote
                existing_vote.is_upvote = is_upvote
                
                if is_upvote:
                    solution.upvote_count += 1
                    solution.downvote_count -= 1
                    solution.author.reputation += 7  # +5 for upvote, +2 to cancel downvote
                else:
                    solution.upvote_count -= 1
                    solution.downvote_count += 1
                    solution.author.reputation -= 7  # -2 for downvote, -5 to cancel upvote
        else:
            # New vote
            vote = Vote(
                user_id=user.id,
                solution_id=solution.id,
                is_upvote=is_upvote
            )
            db.session.add(vote)
            
            if is_upvote:
                solution.upvote_count += 1
                solution.author.reputation += 5
            else:
                solution.downvote_count += 1
                solution.author.reputation -= 2
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vote recorded',
            'upvoteCount': solution.upvote_count,
            'downvoteCount': solution.downvote_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error voting: {str(e)}")
        return jsonify({'error': 'Failed to vote'}), 500

@community_bp.route('/community/solutions/<int:solution_id>/bookmark', methods=['POST'])
@require_auth
def toggle_bookmark(solution_id):
    """Toggle bookmark on a solution"""
    try:
        user = User.query.filter_by(uid=request.uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        solution = SharedSolution.query.get_or_404(solution_id)
        
        # Check existing bookmark
        bookmark = Bookmark.query.filter_by(
            user_id=user.id,
            solution_id=solution.id
        ).first()
        
        if bookmark:
            # Remove bookmark
            db.session.delete(bookmark)
            solution.bookmark_count -= 1
            is_bookmarked = False
        else:
            # Add bookmark
            bookmark = Bookmark(
                user_id=user.id,
                solution_id=solution.id
            )
            db.session.add(bookmark)
            solution.bookmark_count += 1
            is_bookmarked = True
        
        db.session.commit()
        
        return jsonify({
            'isBookmarked': is_bookmarked,
            'bookmarkCount': solution.bookmark_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error toggling bookmark: {str(e)}")
        return jsonify({'error': 'Failed to toggle bookmark'}), 500

@community_bp.route('/community/solutions/<int:solution_id>/comments', methods=['GET'])
def get_comments(solution_id):
    """Get comments for a solution"""
    try:
        solution = SharedSolution.query.get_or_404(solution_id)
        
        # Get top-level comments
        comments = Comment.query.filter_by(
            solution_id=solution.id,
            parent_id=None
        ).order_by(desc(Comment.created_at)).all()
        
        return jsonify({
            'comments': [comment.to_dict(include_replies=True) for comment in comments]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching comments: {str(e)}")
        return jsonify({'error': 'Failed to fetch comments'}), 500

@community_bp.route('/community/solutions/<int:solution_id>/comments', methods=['POST'])
@require_auth
def add_comment(solution_id):
    """Add a comment to a solution"""
    try:
        user = User.query.filter_by(uid=request.uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        solution = SharedSolution.query.get_or_404(solution_id)
        
        data = request.get_json()
        content = data.get('content')
        parent_id = data.get('parentId')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Create comment
        comment = Comment(
            author_id=user.id,
            solution_id=solution.id,
            content=content,
            parent_id=parent_id
        )
        
        db.session.add(comment)
        
        # Update comment count
        solution.comment_count += 1
        
        # Award reputation for engagement
        user.reputation += 2
        
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        return jsonify({'error': 'Failed to add comment'}), 500

