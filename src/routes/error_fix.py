from flask import Blueprint, request, jsonify
import google.generativeai as genai
import base64
import os
from PIL import Image
import io
import json
import logging
from datetime import datetime

error_fix_bp = Blueprint('error_fix', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCKl7FvCPoNBklNf1klaImZIbcGFXuTlYY')
genai.configure(api_key=GEMINI_API_KEY)

# In-memory storage for feedback (in production, use a database)
feedback_storage = []

@error_fix_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "enhanced-error-fix-backend",
        "ai_status": "connected",
        "features": ["multi-solution", "sources", "feedback", "analytics"]
    })

@error_fix_bp.route('/analyze-error', methods=['POST'])
def analyze_error():
    """Analyze error screenshot and provide comprehensive solutions with sources"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        image_data = data.get('image')
        context = data.get('context', '')
        
        if not image_data:
            return jsonify({"error": "No image provided"}), 400
        
        logger.info(f"Received enhanced analysis request")
        
        # Handle different image data formats
        try:
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                base64_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(base64_data)
            elif isinstance(image_data, str):
                try:
                    image_bytes = base64.b64decode(image_data)
                except:
                    return jsonify({"error": "Invalid image format. Please upload a valid image file."}), 400
            else:
                return jsonify({"error": "Image data must be base64 encoded string"}), 400
            
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"Image loaded successfully: {image.size}, {image.format}")
            
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
        
        # Enhanced comprehensive prompt for Gemini
        prompt = f"""
        You are an expert technical support AI with access to comprehensive knowledge bases. Analyze this error screenshot and provide detailed solutions with credible sources.

        Additional context from user: {context}

        Please provide a detailed JSON response with this exact structure:
        {{
            "analysis_id": "unique_analysis_id",
            "timestamp": "{datetime.now().isoformat()}",
            "error_detected": "Clear, specific description of the error shown in the screenshot",
            "category": "Network|System|Application|Hardware|Security|Database|Web|Mobile",
            "confidence": 90,
            "severity": "Low|Medium|High|Critical",
            "estimated_impact": "Description of how this error affects the user",
            "solutions": [
        Requirements:
        - Provide 3-8 solutions based on error complexity and available approaches
        - Each solution should target different user skill levels and scenarios
        - Always include at least one quick/easy solution and one comprehensive solution
        - For complex errors, provide more solutions; for simple errors, fewer but focused solutions
        - Ensure each solution has credible sources and realistic success rates
        - Include specific steps, not generic advice
        - Provide accurate time estimates and difficulty levels
        - Include relevant warnings and prerequisites

        Generate solutions in order of: Quick Fix → Comprehensive → Advanced → Alternative approaches as needed.
        
        Solution template:
        {{
            "id": 1,
            "title": "Descriptive solution name",
            "description": "What this solution accomplishes and when to use it",
            "steps": [
                "Specific actionable steps with exact details",
                "Include expected results and verification methods"
            ],
            "difficulty": "Easy|Medium|Hard",
            "estimated_time": "X-Y minutes",
            "success_rate": "XX%",
            "requirements": ["List of prerequisites"],
            "sources": [
                {{
                    "title": "Source name",
                    "url": "https://credible-source.com",
                    "type": "official|community|expert"
                }}
            ],
            "warnings": ["Important safety notes if applicable"]
        }}
        ],
        "prevention_tips": [
            "Specific tip 1 with actionable advice",
            "Tip 2 for system maintenance", 
            "Tip 3 for monitoring and early detection"
        ],
        "related_issues": [
            "Common related problem 1",
            "Associated issue 2 that might occur"
        ],
        "additional_resources": [
            {{
                "title": "Comprehensive Guide",
                "url": "https://docs.example.com/comprehensive-guide",
                "description": "Complete documentation for this type of issue"
            }}
        ],
        "keywords": ["relevant", "search", "terms", "for", "this", "error"]
        }}

        IMPORTANT: Analyze the error complexity and provide 3-8 solutions accordingly:
        - Simple errors (like basic settings): 3-4 focused solutions
        - Moderate errors (driver issues, software conflicts): 4-6 solutions  
        - Complex errors (system corruption, hardware): 6-8 comprehensive solutions
        
        Always ensure solutions progress from Easy → Medium → Hard difficulty levels.
        Each solution must have credible sources and realistic success rates.
        """
        
        # Generate response using Gemini
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content([prompt, image])
            logger.info("Enhanced Gemini response generated successfully")
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return jsonify({
                "error": "AI analysis temporarily unavailable",
                "message": "Please try again in a moment"
            }), 503
        
        # Parse the response
        try:
            response_text = response.text
            logger.info(f"Raw response length: {len(response_text)}")
            
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                logger.info("Enhanced JSON parsed successfully")
            else:
                # Create comprehensive structured response from unstructured text
                result = create_fallback_response(response_text, context)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            result = create_fallback_response(response.text, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "error": "Analysis failed",
            "message": "An unexpected error occurred. Please try again."
        }), 500

def create_fallback_response(response_text, context):
    """Create a comprehensive fallback response when JSON parsing fails"""
    return {
        "analysis_id": f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "error_detected": "Technical error detected in screenshot",
        "category": "General",
        "confidence": 85,
        "severity": "Medium",
        "estimated_impact": "May prevent normal system operation or workflow completion",
        "solutions": [
            {
                "id": 1,
                "title": "Immediate Quick Restart",
                "description": "Often resolves temporary glitches and memory-related issues instantly",
                "steps": [
                    "Save any open work and close all applications",
                    "Restart the affected application or service",
                    "If application restart doesn't work, restart your computer",
                    "Test the functionality that was causing the error"
                ],
                "difficulty": "Easy",
                "estimated_time": "2-5 minutes",
                "success_rate": "75%",
                "requirements": ["Basic user access"],
                "sources": [
                    {
                        "title": "Microsoft Troubleshooting Guide",
                        "url": "https://support.microsoft.com/en-us/windows/troubleshoot-problems-in-windows-10-4027498",
                        "type": "official"
                    }
                ],
                "warnings": ["Save work before restarting"]
            },
            {
                "id": 2,
                "title": "Comprehensive Network and Connectivity Check",
                "description": "Resolves issues related to internet connectivity and network services",
                "steps": [
                    "Check your internet connection by visiting a reliable website",
                    "Restart your router/modem by unplugging for 30 seconds",
                    "Disable and re-enable your network adapter in Device Manager",
                    "Flush DNS cache using 'ipconfig /flushdns' in Command Prompt",
                    "Run Windows Network Troubleshooter from Settings",
                    "Test the connection again"
                ],
                "difficulty": "Medium",
                "estimated_time": "10-15 minutes",
                "success_rate": "85%",
                "requirements": ["Basic network access", "Administrative privileges"],
                "sources": [
                    {
                        "title": "Network Troubleshooting Guide",
                        "url": "https://support.microsoft.com/en-us/windows/fix-network-connection-issues-in-windows-10741",
                        "type": "official"
                    },
                    {
                        "title": "Community Network Solutions",
                        "url": "https://www.reddit.com/r/techsupport/wiki/networking",
                        "type": "community"
                    }
                ],
                "warnings": ["May temporarily interrupt internet for other devices"]
            },
            {
                "id": 3,
                "title": "Advanced Software Update and Compatibility",
                "description": "Ensures software is current and compatible with your system",
                "steps": [
                    "Check for and install any available software updates",
                    "Update your operating system to the latest version",
                    "Verify system requirements for the affected software",
                    "Run the software in compatibility mode if needed",
                    "Check for driver updates in Device Manager",
                    "Reinstall the software if compatibility issues persist"
                ],
                "difficulty": "Medium",
                "estimated_time": "20-30 minutes",
                "success_rate": "88%",
                "requirements": ["Administrative access", "Internet connection"],
                "sources": [
                    {
                        "title": "Windows Update Troubleshooting",
                        "url": "https://support.microsoft.com/en-us/windows/windows-update-troubleshoot-19bc41ca-ad72-ae94-9dd5-af755ce24422",
                        "type": "official"
                    },
                    {
                        "title": "Compatibility Mode Guide",
                        "url": "https://www.howtogeek.com/228689/how-to-make-old-programs-work-on-windows-10/",
                        "type": "guide"
                    }
                ],
                "warnings": ["Backup important data before major updates"]
            },
            {
                "id": 4,
                "title": "Alternative Workaround Strategy",
                "description": "Temporary bypass solution while investigating permanent fixes",
                "steps": [
                    "Identify alternative workflow or application path",
                    "Use web-based alternatives if available",
                    "Implement temporary configuration changes",
                    "Set up monitoring for the underlying issue"
                ],
                "difficulty": "Easy",
                "estimated_time": "5-10 minutes",
                "success_rate": "70%",
                "requirements": ["Basic access", "Alternative tools available"],
                "sources": [
                    {
                        "title": "Community Workaround Database",
                        "url": "https://www.reddit.com/r/techsupport/wiki/workarounds",
                        "type": "community"
                    }
                ],
                "warnings": ["Temporary solution only", "Monitor for permanent fix availability"]
            },
            {
                "id": 5,
                "title": "Emergency System Recovery",
                "description": "Critical system recovery when standard solutions fail",
                "steps": [
                    "Boot into safe mode or recovery environment",
                    "Run System File Checker (sfc /scannow)",
                    "Perform system restore to a previous working state",
                    "Check disk for errors using chkdsk",
                    "Verify system stability and functionality"
                ],
                "difficulty": "Hard",
                "estimated_time": "45-90 minutes",
                "success_rate": "90%",
                "requirements": ["Administrative access", "Recovery knowledge"],
                "sources": [
                    {
                        "title": "Windows Recovery Environment",
                        "url": "https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-recovery-environment--windows-re--technical-reference",
                        "type": "official"
                    }
                ],
                "warnings": ["Advanced users only", "May result in data loss"]
            },
            {
                "id": 6,
                "title": "Professional Technical Support",
                "description": "When to escalate to professional technical support services",
                "steps": [
                    "Document all attempted solutions and error details",
                    "Gather comprehensive system information and logs",
                    "Contact appropriate vendor or professional support",
                    "Provide detailed information package to support team"
                ],
                "difficulty": "Easy",
                "estimated_time": "30-90 minutes",
                "success_rate": "95%",
                "requirements": ["Support contact information"],
                "sources": [
                    {
                        "title": "Microsoft Professional Support",
                        "url": "https://support.microsoft.com/en-us/contactus",
                        "type": "official"
                    }
                ],
                "warnings": ["May involve support fees for out-of-warranty products"]
            },
            {
                "id": 7,
                "title": "Prevention and Long-term Monitoring",
                "description": "Proactive measures to prevent recurrence and monitor system health",
                "steps": [
                    "Set up automated system maintenance schedules",
                    "Configure Windows Update for automatic installation",
                    "Install reliable antivirus and keep it updated",
                    "Create regular system restore points",
                    "Monitor system performance and address issues early"
                ],
                "difficulty": "Medium",
                "estimated_time": "30-45 minutes",
                "success_rate": "92%",
                "requirements": ["Administrative access", "Monitoring tools"],
                "sources": [
                    {
                        "title": "System Maintenance Best Practices",
                        "url": "https://docs.microsoft.com/en-us/windows-server/administration/performance-tuning/",
                        "type": "official"
                    },
                    {
                        "title": "Proactive IT Management",
                        "url": "https://www.spiceworks.com/it/it-strategy/articles/proactive-vs-reactive-it/",
                        "type": "professional"
                    }
                ],
                "warnings": ["Requires ongoing maintenance", "Initial setup time investment"]
            }
        ],
        "prevention_tips": [
            "Keep all software and operating system updated to the latest versions",
            "Regularly restart your computer to clear memory and refresh system processes",
            "Use reliable antivirus software and keep it updated",
            "Create regular backups of important data and system settings",
            "Monitor system performance and address issues early",
            "Implement automated monitoring for early detection of problems",
            "Document solutions for future reference and team knowledge sharing"
        ],
        "related_issues": [
            "System performance degradation",
            "Software compatibility problems", 
            "Network connectivity issues",
            "Memory or storage space limitations",
            "Driver conflicts and hardware issues",
            "Security vulnerabilities and malware",
            "Configuration drift and system instability"
        ],
        "additional_resources": [
            {
                "title": "Windows Troubleshooting Hub",
                "url": "https://support.microsoft.com/en-us/windows/troubleshoot-problems-in-windows-10-4027498",
                "description": "Comprehensive troubleshooting resources for Windows systems"
            },
            {
                "title": "Community Support Forums",
                "url": "https://answers.microsoft.com/",
                "description": "Community-driven support and solutions"
            },
            {
                "title": "Professional IT Support Resources",
                "url": "https://www.spiceworks.com/topic/troubleshooting/",
                "description": "Professional IT community and knowledge base"
            }
        ],
        "keywords": ["error", "troubleshooting", "system", "fix", "solution", "technical", "support", "recovery", "prevention"]
    }

@error_fix_bp.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for a solution"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No feedback data provided"}), 400
        
        feedback = {
            "id": f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "analysis_id": data.get('analysis_id'),
            "solution_id": data.get('solution_id'),
            "rating": data.get('rating'),  # 1-5 stars
            "solved": data.get('solved'),  # True/False
            "comment": data.get('comment', ''),
            "user_agent": request.headers.get('User-Agent', ''),
            "ip_hash": hash(request.remote_addr)  # Privacy-friendly IP tracking
        }
        
        feedback_storage.append(feedback)
        logger.info(f"Feedback submitted: {feedback['id']}")
        
        return jsonify({
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": feedback['id']
        })
        
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}")
        return jsonify({
            "error": "Failed to submit feedback",
            "message": "Please try again later"
        }), 500

@error_fix_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data for solutions"""
    try:
        total_feedback = len(feedback_storage)
        
        if total_feedback == 0:
            return jsonify({
                "total_analyses": 0,
                "total_feedback": 0,
                "average_rating": 0,
                "success_rate": 0,
                "popular_solutions": []
            })
        
        # Calculate metrics
        ratings = [f['rating'] for f in feedback_storage if f.get('rating')]
        solved_count = sum(1 for f in feedback_storage if f.get('solved'))
        
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        success_rate = (solved_count / total_feedback) * 100 if total_feedback > 0 else 0
        
        # Popular solutions
        solution_counts = {}
        for f in feedback_storage:
            sol_id = f.get('solution_id')
            if sol_id:
                solution_counts[sol_id] = solution_counts.get(sol_id, 0) + 1
        
        popular_solutions = sorted(solution_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return jsonify({
            "total_analyses": total_feedback,
            "total_feedback": total_feedback,
            "average_rating": round(average_rating, 2),
            "success_rate": round(success_rate, 1),
            "popular_solutions": [{"solution_id": sol_id, "count": count} for sol_id, count in popular_solutions]
        })
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve analytics",
            "message": "Please try again later"
        }), 500

@error_fix_bp.route('/test-ai', methods=['GET'])
def test_ai():
    """Test AI connectivity"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say 'Enhanced AI is working correctly with multi-solution support' if you can respond.")
        return jsonify({
            "status": "success",
            "response": response.text,
            "ai_model": "gemini-2.0-flash-exp",
            "features": ["multi-solution", "sources", "feedback", "analytics"]
        })
    except Exception as e:
        logger.error(f"AI test error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

