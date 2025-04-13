from flask import Flask, request, jsonify, send_from_directory
from app.linkedin.client import LinkedInClient
from app.ai.content_generator import ContentGenerator
from app.models import PostStatus
from app.scheduler.publisher import PostPublisher
from datetime import datetime
import asyncio
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Initialize services
content_generator = ContentGenerator()
post_publisher = PostPublisher()

@app.route('/', methods=['GET'])
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/generate-content', methods=['POST'])
async def generate_content():
    try:
        data = request.json
        source_type = data.get('source_type')
        source_data = data.get('source_data')
        tone = data.get('tone')
        
        content = await content_generator.generate_content(
            source_type=source_type,
            source_data=source_data,
            tone=tone
        )
        
        return jsonify({
            'status': 'success',
            'content': content
        })
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/publish', methods=['POST'])
async def publish_post():
    try:
        data = request.json
        content = data.get('content')
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        token_expires_at = data.get('token_expires_at')
        
        if not content or not access_token:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        # Create LinkedIn client
        linkedin_client = LinkedInClient(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=datetime.fromisoformat(token_expires_at) if token_expires_at else None
        )
        
        # Publish post
        post_id = await linkedin_client.publish_post(content)
        
        return jsonify({
            'status': 'success',
            'post_id': post_id,
            'access_token': linkedin_client.access_token,
            'refresh_token': linkedin_client.refresh_token,
            'token_expires_at': linkedin_client.token_expires_at.isoformat() if linkedin_client.token_expires_at else None,
            'token_refreshed': linkedin_client.token_refreshed
        })
    except Exception as e:
        logger.error(f"Error publishing post: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/schedule', methods=['POST'])
def schedule_post():
    try:
        data = request.json
        content = data.get('content')
        scheduled_time = data.get('scheduled_time')
        linkedin_account = data.get('linkedin_account')
        
        if not all([content, scheduled_time, linkedin_account]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        # Convert scheduled_time string to datetime
        scheduled_time = datetime.fromisoformat(scheduled_time)
        
        # Start publisher if not running
        if not post_publisher.is_running:
            asyncio.create_task(post_publisher.start())
        
        return jsonify({
            'status': 'success',
            'message': 'Post scheduled successfully',
            'scheduled_time': scheduled_time.isoformat()
        })
    except Exception as e:
        logger.error(f"Error scheduling post: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)