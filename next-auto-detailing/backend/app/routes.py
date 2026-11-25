import secrets
from flask import Blueprint,request,jsonify,session
from sqlalchemy import select
from werkzeug.security import check_password_hash,generate_password_hash
from email_validator import validate_email,EmailNotValidError
from . import db,limiter
from .models import User,Service,Booking,QuoteRequest,Invoice,Quotation
from flask_wtf.csrf import generate_csrf
api=Blueprint('api',__name__)
def err(msg,status=400): return jsonify({'error':msg}),status
def me():
 uid=session.get('uid');return db.session.get(User,uid) if uid else None
def user_required():
 u=me()
 return (u,None) if u and u.active else (None,err('Authentication required.',401))
def roles(*allowed):
 u,e=user_required()
 if e:return None,e
 return (u,None) if u.role in allowed else (None,err('Permission denied.',403))
def email(v):
 try:return validate_email(v,check_deliverability=False).normalized.lower()
 except (EmailNotValidError,TypeError):return None
def pub(u):return {'id':u.id,'name':u.name,'email':u.email,'role':u.role,'must_change_password':u.must_change_password}
@api.get('/csrf')
def csrf_token(): return jsonify({'csrf_token':generate_csrf()})
@api.get('/public/services')
def services():
 rows=db.session.scalars(select(Service).where(Service.active.is_(True)).order_by(Service.sort_order)).all()
 return jsonify({'items':[{'id':x.id,'name':x.name,'slug':x.slug,'description':x.description,'image_url':x.image_url,'starting_price_minor':x.starting_price_minor,'currency':x.currency} for x in rows]})
@api.get('/public/gallery')
def gallery():return jsonify({'items':[]})
@api.post('/public/quote-requests')
@limiter.limit('8 per hour')
def quote_request():
 d=request.get_json(silent=True) or {};n=str(d.get('name','')).strip();e=email(d.get('email'));p=str(d.get('phone','')).strip();details=str(d.get('details','')).strip()
 if not n or not e or not p or not details:return err('Complete all fields with valid contact details.')
 if len(n)>120 or len(p)>40 or len(details)>3000:return err('A field is too long.')
 db.session.add(QuoteRequest(name=n,email=e,phone=p,details=details));db.session.commit();return jsonify({'message':'Request received.'}),201
@api.post('/auth/register')
@limiter.limit('5 per hour')
def register():
 d=request.get_json(silent=True) or {};n=str(d.get('name','')).strip();e=email(d.get('email'));p=str(d.get('phone','')).strip();pw=str(d.get('password',''))
 if not n or not e or not p:return err('Name, valid email and phone are required.')
 if len(pw)<12 or len(pw)>128:return err('Password must be 12–128 characters.')
 if db.session.scalar(select(User).where(User.email==e)):return err('Email already registered.',409)
 db.session.add(User(name=n,email=e,phone=p,role='customer',password_hash=generate_password_hash(pw,method='scrypt')));db.session.commit()
 return jsonify({'message':'Account created. Email verification must be configured before production.'}),201
@api.post('/auth/login')
@limiter.limit('10 per 15 minutes')
def login():
 d=request.get_json(silent=True) or {};e=email(d.get('email'));pw=str(d.get('password',''));u=db.session.scalar(select(User).where(User.email==e)) if e else None
 if not u or not u.active or not check_password_hash(u.password_hash,pw):return err('Invalid email or password.',401)
 session.clear();session['uid']=u.id;session.permanent=True
 return jsonify({'user':pub(u),'password_change_required':u.must_change_password})
@api.post('/auth/logout')
def logout():session.clear();return jsonify({'message':'Signed out.'})
@api.get('/auth/me')
def who():u=me();return jsonify({'user':pub(u) if u else None})
@api.post('/auth/password/change')
def change():
 u,e=user_required()
 if e:return e
 d=request.get_json(silent=True) or {};old=str(d.get('current_password',''));new=str(d.get('new_password',''))
 if not check_password_hash(u.password_hash,old):return err('Current password is incorrect.',401)
 if len(new)<12 or len(new)>128:return err('New password must be 12–128 characters.')
 u.password_hash=generate_password_hash(new,method='scrypt');u.must_change_password=False;db.session.commit();return jsonify({'message':'Password changed.'})
@api.post('/auth/password/forgot')
@limiter.limit('5 per hour')
def forgot():
 # Generic response; expiring one-use token storage and delivery must be added with configured mail provider before launch.
 return jsonify({'message':'If the account exists, reset instructions will be sent.'})
@api.get('/customer/bookings')
def my_bookings():
 u,e=user_required()
 if e:return e
 if u.role!='customer':return err('Customer account required.',403)
 rows=db.session.scalars(select(Booking).where(Booking.customer_id==u.id)).all()
 return jsonify({'items':[{'reference':b.reference,'vehicle':b.vehicle_description,'status':b.status,'preferred_at':b.preferred_at.isoformat()} for b in rows]})
@api.get('/customer/documents')
def my_docs():
 u,e=user_required()
 if e:return e
 if u.role!='customer':return err('Customer account required.',403)
 inv=db.session.scalars(select(Invoice).where(Invoice.customer_id==u.id)).all();q=db.session.scalars(select(Quotation).where(Quotation.customer_id==u.id)).all()
 return jsonify({'items':[{'type':'Invoice','reference':x.reference,'status':x.status,'total_minor':x.total_minor,'currency':x.currency} for x in inv]+[{'type':'Quotation','reference':x.reference,'status':x.status,'total_minor':x.total_minor,'currency':x.currency} for x in q]})
@api.get('/staff/overview')
def staff_overview():
 u,e=roles('owner','operations','detailer')
 if e:return e
 return jsonify({'role':u.role,'message':'Staff overview.'})
@api.get('/staff/bookings')
def staff_bookings():
 u,e=roles('owner','operations')
 if e:return e
 rows=db.session.scalars(select(Booking).order_by(Booking.preferred_at)).all()
 return jsonify({'items':[{'reference':b.reference,'customer_id':b.customer_id,'vehicle':b.vehicle_description,'status':b.status,'preferred_at':b.preferred_at.isoformat()} for b in rows]})
@api.get('/staff/employees')
def employees():
 u,e=roles('owner','operations')
 if e:return e
 rows=db.session.scalars(select(User).where(User.role.in_(['owner','operations','detailer']))).all()
 return jsonify({'items':[{'id':x.id,'name':x.name,'email':x.email,'role':x.role,'active':x.active} for x in rows]})
@api.get('/staff/payroll')
def payroll():
 u,e=roles('owner')
 if e:return e
 return jsonify({'items':[],'message':'Payroll records will appear after payroll configuration.'})
