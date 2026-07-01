from datetime import datetime
from app.extensions import db


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_title = db.Column(db.String(255), nullable=True, default='')
    industry = db.Column(db.String(255), nullable=False)
    years_exp = db.Column(db.Integer, nullable=True, default=0)
    country = db.Column(db.String(100), nullable=True, default='US')
    step = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    salary_range = db.Column(db.String(100), nullable=True)
    salary_source = db.Column(db.String(50), nullable=True)
    salary_confidence = db.Column(db.String(50), nullable=True)

    tasks = db.relationship('Task', backref='assessment', lazy='dynamic',
                            cascade='all, delete-orphan',
                            order_by='Task.id')
    roadmap_items = db.relationship('RoadmapItem', backref='assessment', lazy='dynamic',
                                    cascade='all, delete-orphan',
                                    order_by='RoadmapItem.priority')


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Float, nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)


class RoadmapItem(db.Model):
    __tablename__ = 'roadmap_items'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    skill_name = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    timeline = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    resources = db.Column(db.JSON, nullable=True)
