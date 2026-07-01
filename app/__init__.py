from flask import Flask, render_template
from app.config import Config
from app.extensions import db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    migrate.init_app(app, db)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.assessment import assessment_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(assessment_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    if app.config.get('GOOGLE_OAUTH_CLIENT_ID'):
        _setup_google_oauth(app)

    with app.app_context():
        from app.models import User, OAuthAccount, Assessment, Task, RoadmapItem
        db.create_all()
        try:
            from sqlalchemy import inspect
            insp = inspect(db.engine)
            cols = [c['name'] for c in insp.get_columns('assessments')]
            for col in ('notes', 'country', 'salary_range', 'salary_source', 'salary_confidence'):
                if col not in cols:
                    db.session.execute(db.text(f'ALTER TABLE assessments ADD COLUMN {col} TEXT'))
                    db.session.commit()
            ucols = [c['name'] for c in insp.get_columns('users')]
            if 'last_country' not in ucols:
                db.session.execute(db.text('ALTER TABLE users ADD COLUMN last_country VARCHAR(100)'))
                db.session.commit()
        except Exception:
            db.session.rollback()

    return app


def _setup_google_oauth(app):
    from flask_dance.contrib.google import make_google_blueprint
    from flask_dance.consumer import oauth_authorized
    from flask import redirect, url_for, flash
    from flask_login import login_user, current_user
    from app.extensions import db
    from app.models.user import User, OAuthAccount

    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
        client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
        scope=['openid', 'https://www.googleapis.com/auth/userinfo.email',
               'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_to='assessment.wizard_step1'
    )
    app.register_blueprint(google_bp, url_prefix='/login')

    @oauth_authorized.connect_via(google_bp)
    def google_logged_in(blueprint, token):
        if not token:
            flash('Failed to log in with Google.', 'danger')
            return False

        resp = blueprint.session.get('/oauth2/v1/userinfo')
        if not resp.ok:
            flash('Failed to get user info from Google.', 'danger')
            return False

        google_info = resp.json()
        google_user_id = str(google_info['id'])
        google_email = google_info.get('email')
        google_name = google_info.get('name')
        google_avatar = google_info.get('picture')

        oauth_account = OAuthAccount.query.filter_by(
            provider='google',
            provider_user_id=google_user_id
        ).first()

        if oauth_account:
            user = oauth_account.user
        else:
            user = User.query.filter_by(email=google_email).first()
            if not user:
                user = User(
                    email=google_email,
                    name=google_name,
                    avatar_url=google_avatar
                )
                db.session.add(user)
                db.session.flush()

            oauth_account = OAuthAccount(
                user_id=user.id,
                provider='google',
                provider_user_id=google_user_id,
                provider_email=google_email
            )
            db.session.add(oauth_account)

        user.name = google_name or user.name
        user.avatar_url = google_avatar or user.avatar_url
        db.session.commit()

        login_user(user)
        flash('Logged in with Google successfully!', 'success')
        return redirect(url_for('assessment.wizard_step1'))
