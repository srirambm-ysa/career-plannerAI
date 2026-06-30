from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from app.extensions import db
from app.models.assessment import Assessment, Task, RoadmapItem
from app.services.ai_service import generate_tasks, score_tasks, generate_roadmap

assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessment')

INDUSTRIES = sorted([
    'Technology & Software', 'Healthcare & Pharmaceuticals', 'Finance & Banking',
    'Manufacturing & Engineering', 'Retail & E-commerce', 'Education & Training',
    'Media & Entertainment', 'Telecommunications', 'Energy & Utilities',
    'Transportation & Logistics', 'Real Estate & Construction', 'Agriculture',
    'Hospitality & Tourism', 'Legal & Professional Services', 'Government & Public Sector',
    'Nonprofit & NGO', 'Aerospace & Defense', 'Automotive',
    'Insurance', 'Consulting',
])


def _get_active_assessment():
    assessment = Assessment.query.filter_by(
        user_id=current_user.id, status='draft'
    ).order_by(Assessment.created_at.desc()).first()
    return assessment


def _create_or_get_assessment():
    assessment = _get_active_assessment()
    if not assessment:
        Assessment.query.filter(
            Assessment.user_id == current_user.id,
            Assessment.status == 'draft',
            Assessment.industry == ''
        ).delete()
        db.session.commit()
        assessment = Assessment(
            user_id=current_user.id,
            industry='',
            step=1
        )
        db.session.add(assessment)
        db.session.commit()
    return assessment


@assessment_bp.route('/')
@login_required
def wizard():
    return redirect(url_for('assessment.wizard_step1'))


@assessment_bp.route('/step/1', methods=['GET', 'POST'])
@login_required
def wizard_step1():
    assessment = _create_or_get_assessment()

    if request.method == 'POST':
        industry = request.form.get('industry', '').strip()

        if not industry:
            flash('Please select an industry.', 'danger')
            return render_template('assessment/step1.html', assessment=assessment, industries=INDUSTRIES)

        assessment.industry = industry
        assessment.step = 2
        current_user.last_industry = industry
        db.session.commit()

        return redirect(url_for('assessment.wizard_step2'))

    return render_template('assessment/step1.html', assessment=assessment, industries=INDUSTRIES)


@assessment_bp.route('/step/2', methods=['GET', 'POST'])
@login_required
def wizard_step2():
    assessment = _get_active_assessment()
    if not assessment or assessment.step < 2:
        return redirect(url_for('assessment.wizard_step1'))

    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        years_exp = request.form.get('years_exp', 0, type=int)

        if not job_title:
            flash('Please enter a job title.', 'danger')
            return render_template('assessment/step2.html', assessment=assessment)

        assessment.job_title = job_title
        assessment.years_exp = years_exp

        task_descriptions = request.form.getlist('task_desc')
        task_descriptions = [d.strip() for d in task_descriptions if d.strip()]

        if not task_descriptions:
            flash('Please add at least one task.', 'danger')
            return render_template('assessment/step2.html', assessment=assessment)

        Task.query.filter_by(assessment_id=assessment.id).delete()
        db.session.commit()

        for desc in task_descriptions:
            task = Task(assessment_id=assessment.id, description=desc, category='')
            db.session.add(task)
        db.session.commit()

        try:
            tasks_list = list(assessment.tasks.all())
            risk_results = score_tasks([{'description': t.description} for t in tasks_list])
            scored = risk_results.get('tasks', [])
            for i, task in enumerate(tasks_list):
                if i < len(scored):
                    task.risk_score = scored[i]['risk_score']
                    task.explanation = scored[i].get('explanation', '')
            assessment.step = 3
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'AI scoring failed: {e}')
            for task in assessment.tasks.all():
                task.risk_score = task.id % 10 + 1
                task.explanation = 'Auto-generated score.'
            assessment.step = 3
            db.session.commit()

        return redirect(url_for('assessment.wizard_step3'))

    return render_template('assessment/step2.html', assessment=assessment)


@assessment_bp.route('/step/2/suggest-tasks', methods=['POST'])
@login_required
def suggest_tasks():
    assessment = _get_active_assessment()
    if not assessment:
        return jsonify({'tasks': []}), 400

    data = request.get_json(silent=True) or {}
    job_title = data.get('job_title', assessment.job_title or '').strip()
    industry = data.get('industry', assessment.industry or '').strip()
    years_exp = data.get('years_exp', assessment.years_exp or 0)

    if not job_title:
        return jsonify({'error': 'Job title is required'}), 400

    try:
        result = generate_tasks(job_title, industry, years_exp)
        return jsonify({'tasks': result.get('tasks', [])})
    except Exception as e:
        current_app.logger.error(f'AI suggest-tasks failed: {e}')
        mock_tasks = [
            {'description': 'Write and review reports', 'category': 'Analytical'},
            {'description': 'Attend team meetings and take minutes', 'category': 'Interpersonal'},
            {'description': 'Manage project timelines and deadlines', 'category': 'Administrative'},
            {'description': 'Communicate with stakeholders via email', 'category': 'Interpersonal'},
            {'description': 'Analyze data and prepare presentations', 'category': 'Analytical'},
            {'description': 'Research industry trends and best practices', 'category': 'Strategic'},
            {'description': 'Train and mentor junior team members', 'category': 'Interpersonal'},
            {'description': 'Create and maintain documentation', 'category': 'Administrative'},
            {'description': 'Develop strategic plans for the department', 'category': 'Strategic'},
            {'description': 'Handle customer inquiries and resolve issues', 'category': 'Interpersonal'},
            {'description': 'Design and implement process improvements', 'category': 'Creative'},
            {'description': 'Prepare and manage budgets', 'category': 'Administrative'},
        ]
        return jsonify({'tasks': mock_tasks})


@assessment_bp.route('/step/3', methods=['GET', 'POST'])
@login_required
def wizard_step3():
    assessment = _get_active_assessment()
    if not assessment or assessment.step < 3:
        return redirect(url_for('assessment.wizard_step1'))

    tasks = Task.query.filter_by(assessment_id=assessment.id).order_by(
        Task.risk_score.desc().nullslast()
    ).all()

    if request.method == 'POST':
        tasks_data = [
            {'description': t.description, 'risk_score': t.risk_score,
             'explanation': t.explanation}
            for t in tasks
        ]

        try:
            roadmap_data = generate_roadmap(tasks_data)
            RoadmapItem.query.filter_by(assessment_id=assessment.id).delete()
            db.session.commit()

            for item in roadmap_data.get('roadmap', []):
                r = RoadmapItem(
                    assessment_id=assessment.id,
                    skill_name=item['skill_name'],
                    priority=item['priority'],
                    timeline=item['timeline'],
                    description=item.get('description', ''),
                    category=item.get('category', 'General'),
                    resources=item.get('resources', []),
                )
                db.session.add(r)

            assessment.step = 4
            assessment.status = 'completed'
            from datetime import datetime
            assessment.completed_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'AI roadmap failed: {e}')
            mock_roadmap = [
                {'skill_name': 'Prompt Engineering', 'priority': 1, 'timeline': 'short', 'description': 'Learn to craft effective prompts for AI tools.', 'category': 'AI Literacy', 'resources': ['OpenAI Prompt Guide']},
                {'skill_name': 'Data Analysis', 'priority': 2, 'timeline': 'short', 'description': 'Build skills in Python, SQL, and visualization.', 'category': 'Technical', 'resources': ['DataCamp']},
                {'skill_name': 'Strategic Thinking', 'priority': 3, 'timeline': 'medium', 'description': 'Develop higher-level strategic skills.', 'category': 'Strategic', 'resources': ['Harvard Business Review']},
                {'skill_name': 'AI Tool Proficiency', 'priority': 4, 'timeline': 'short', 'description': 'Master AI-powered development tools.', 'category': 'Technical', 'resources': ['GitHub Copilot']},
                {'skill_name': 'Communication', 'priority': 5, 'timeline': 'medium', 'description': 'Enhance stakeholder communication skills.', 'category': 'Soft Skill', 'resources': ['Crucial Conversations']},
                {'skill_name': 'Machine Learning Basics', 'priority': 6, 'timeline': 'long', 'description': 'Understand ML fundamentals and applications.', 'category': 'Technical', 'resources': ['Fast.ai']},
            ]
            for item in mock_roadmap:
                r = RoadmapItem(
                    assessment_id=assessment.id,
                    skill_name=item['skill_name'],
                    priority=item['priority'],
                    timeline=item['timeline'],
                    description=item['description'],
                    category=item['category'],
                    resources=item['resources'],
                )
                db.session.add(r)
            assessment.step = 4
            assessment.status = 'completed'
            from datetime import datetime
            assessment.completed_at = datetime.utcnow()
            db.session.commit()

        return redirect(url_for('assessment.wizard_step4'))

    return render_template('assessment/step3.html', assessment=assessment, tasks=tasks)


@assessment_bp.route('/step/4')
@login_required
def wizard_step4():
    assessment = _get_active_assessment()
    if not assessment or assessment.step < 4:
        return redirect(url_for('assessment.wizard_step1'))
    return render_template('assessment/step4.html', assessment=assessment)


@assessment_bp.route('/<int:assessment_id>')
@login_required
def view_assessment(assessment_id):
    assessment = Assessment.query.filter_by(
        id=assessment_id, user_id=current_user.id
    ).first_or_404()
    return render_template('assessment/step4.html', assessment=assessment)


@assessment_bp.route('/<int:assessment_id>/pdf')
@login_required
def download_pdf(assessment_id):
    assessment = Assessment.query.filter_by(
        id=assessment_id, user_id=current_user.id
    ).first_or_404()
    return render_template('assessment/pdf.html', assessment=assessment)


@assessment_bp.route('/<int:assessment_id>/json')
@login_required
def export_json(assessment_id):
    assessment = Assessment.query.filter_by(
        id=assessment_id, user_id=current_user.id
    ).first_or_404()
    return jsonify({
        'id': assessment.id,
        'job_title': assessment.job_title,
        'industry': assessment.industry,
        'years_exp': assessment.years_exp,
        'status': assessment.status,
        'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None,
        'tasks': [{'description': t.description, 'risk_score': t.risk_score,
                    'explanation': t.explanation, 'category': t.category}
                  for t in assessment.tasks.all()],
        'roadmap': [{'skill_name': r.skill_name, 'priority': r.priority,
                      'timeline': r.timeline, 'description': r.description,
                      'category': r.category, 'resources': r.resources}
                    for r in assessment.roadmap_items.all()],
    })


@assessment_bp.route('/<int:assessment_id>/notes', methods=['POST'])
@login_required
def save_notes(assessment_id):
    assessment = Assessment.query.filter_by(
        id=assessment_id, user_id=current_user.id
    ).first_or_404()
    assessment.notes = request.form.get('notes', '').strip()
    db.session.commit()
    flash('Notes saved.', 'success')
    return redirect(url_for('assessment.view_assessment', assessment_id=assessment_id))


@assessment_bp.route('/<int:assessment_id>/delete', methods=['POST'])
@login_required
def delete_assessment(assessment_id):
    assessment = Assessment.query.filter_by(
        id=assessment_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(assessment)
    db.session.commit()
    flash('Assessment deleted.', 'success')
    return redirect(url_for('main.dashboard'))
