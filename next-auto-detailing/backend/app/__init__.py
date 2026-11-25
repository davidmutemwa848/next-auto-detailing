import os
from datetime import timedelta
from flask import Flask,jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
load_dotenv()
db=SQLAlchemy();migrate=Migrate();csrf=CSRFProtect();limiter=Limiter(key_func=get_remote_address,default_limits=['300 per hour'])
def create_app(test_config=None):
 app=Flask(__name__)
 app.config.update(SECRET_KEY=os.getenv('SECRET_KEY','unsafe-dev-secret-change-me'),SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///nextauto.sqlite3').replace('postgres://','postgresql://',1),SQLALCHEMY_TRACK_MODIFICATIONS=False,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','true').lower()=='true',SESSION_COOKIE_SAMESITE='Lax',PERMANENT_SESSION_LIFETIME=timedelta(hours=8),MAX_CONTENT_LENGTH=8*1024*1024)
 if test_config: app.config.update(test_config)
 db.init_app(app);migrate.init_app(app,db);csrf.init_app(app);limiter.init_app(app)
 origins=[x.strip() for x in os.getenv('FRONTEND_ORIGIN','http://localhost:5173').split(',') if x.strip()]
 CORS(app,origins=origins,supports_credentials=True,allow_headers=['Content-Type','X-CSRFToken'])
 from . import models
 from .routes import api
 app.register_blueprint(api,url_prefix='/api')
 @app.after_request
 def headers(r):
  r.headers['X-Content-Type-Options']='nosniff';r.headers['X-Frame-Options']='DENY';r.headers['Referrer-Policy']='strict-origin-when-cross-origin';r.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
  if app.config['SESSION_COOKIE_SECURE']: r.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
  return r
 @app.get('/health')
 def health(): return jsonify({'status':'ok'})
 @app.cli.command('init-db')
 def init_db(): db.create_all();print('Development tables initialized. Use migrations in production.')
 @app.cli.command('provision-owner')
 def provision_owner():
  from .models import User
  from werkzeug.security import generate_password_hash
  from sqlalchemy import select
  email=os.getenv('OWNER_EMAIL','').strip().lower();pw=os.getenv('OWNER_INITIAL_PASSWORD','')
  if not email or len(pw)<12: raise SystemExit('Set OWNER_EMAIL and a private initial password of at least 12 characters.')
  if db.session.scalar(select(User).where(User.email==email)): raise SystemExit('Owner already exists.')
  db.session.add(User(name='Business Owner',email=email,role='owner',password_hash=generate_password_hash(pw,method='scrypt'),must_change_password=True,email_verified=True));db.session.commit();print('Owner created; change password at first login.')
 return app
