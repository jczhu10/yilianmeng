from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import sys

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_EXPIRES_IN', 7)) * 24 * 3600
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app.models import (
    User, Profile, Work, Project, ProjectApplication,
    Rating, Message, Event, EventParticipant, Wallet, Transaction,
    SkillCategory, Skill, ProfileSkill
)
from app.utils.helpers import login_required, success_response, error_response

# 注册蓝图
from app.routes.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
from app.routes.profile import bp as profile_bp
app.register_blueprint(profile_bp, url_prefix='/api/v1/profile')
from app.routes.works import bp as works_bp
app.register_blueprint(works_bp, url_prefix='/api/v1/works')

@app.route('/')
def hello():
    return {'message': '艺联萌后端已启动！'}

@app.route('/api/v1')
def api_root():
    return {'message': '艺联萌 API v1', 'status': 'running'}
