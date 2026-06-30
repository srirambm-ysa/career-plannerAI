from datetime import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.assessment import Assessment

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    query = Assessment.query.filter_by(user_id=current_user.id, status='completed')

    search_industry = request.args.get('industry', '').strip()
    search_job_title = request.args.get('job_title', '').strip()
    sort = request.args.get('sort', 'newest')

    if search_industry:
        query = query.filter(Assessment.industry.ilike(f'%{search_industry}%'))
    if search_job_title:
        query = query.filter(Assessment.job_title.ilike(f'%{search_job_title}%'))

    if sort == 'oldest':
        query = query.order_by(Assessment.created_at.asc())
    elif sort == 'industry':
        query = query.order_by(Assessment.industry.asc(), Assessment.created_at.desc())
    else:
        query = query.order_by(Assessment.created_at.desc())

    assessments = query.all()
    return render_template('dashboard.html', assessments=assessments,
                           search_industry=search_industry,
                           search_job_title=search_job_title,
                           sort=sort, datetime=datetime)
