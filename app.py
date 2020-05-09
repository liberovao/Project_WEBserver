import os
import uuid

from flask import Flask, render_template, redirect, flash, url_for, session, send_from_directory, request
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeSerializer

from db import db, User, update_session
from loginform import LoginForm
from regform import RegForm
from config import Config


MAX_CONTENT_LENGTH_FOR_AUTH = 400 * 1024 * 1024
MAX_CONTENT_LENGTH_FOR_UNAUTH = 100 * 1024 * 1024
PATH_TO_FILES = 'files'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///converter.db'
app.config.from_object(Config())
db.app = app
db.init_app(app)
db.create_all()

mail = Mail(app)

serializer = URLSafeSerializer(app.config['SECRET_KEY'])

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.errorhandler(404)
def not_found(e):
    flash(e, category='danger')
    return render_template('not_found.html', title='Ooops...')


@app.before_request
def before_request():
    check_operation_id()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('main.html', title='Автоcервис в Москве')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('User not found', category='danger')
            return redirect(url_for('registration'))
        elif user.check_password(form.password.data) is False:
            flash('Invalid Username or password', category='danger')
            return redirect(url_for('login'))
        elif not user.confirmed:
            flash('Please, confirm your email', category='danger')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash('Logged in successfully', category='success')
            return redirect(url_for('index'))
    for errors in form.errors.values():
        for error in errors:
            flash(error, category='danger')
    return render_template('login.html', form=form, title='Authorization')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# noinspection PyArgumentList
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        flash('Already logged in', category='danger')
        return redirect(url_for('index'))
    form = RegForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first() is not None:
            flash('Username is busy', category='danger')
            return redirect(url_for('registration'))
        elif User.query.filter_by(email=form.email.data).first() is not None:
            flash('Email is busy', category='danger')
            return redirect(url_for('registration'))
        email = form.email.data
        confirmation_token = serializer.dumps(email, salt='token_email')
        user = User(username=form.username.data, email=form.email.data, status='user', confirmed=False)
        user.set_password(form.password.data)
        update_session(user)
        msg = Message('Confirm your account on converter', sender='liberovaolesya@gmail.ru',
                      recipients=[email])
        link = url_for('confirmation', token=confirmation_token, _external=True)
        msg.body = 'Click on this link: {}'.format(link)
        mail.send(msg)
        flash('Please, confirm your email.', category='primary')
        return redirect(url_for('login'))
    for errors in form.errors.values():
        for error in errors:
            flash(error, category='danger')
    return render_template('registration.html', form=form, title='Registration')


@app.route('/confirmation/<token>')
def confirmation(token):
    email = serializer.loads(token, salt='token_email')
    user = User.query.filter_by(email=email).first()
    if user is not None:
        user.confirmed = True
        update_session()
        flash('Account created successful!', category='success')
        return redirect(url_for('login'))
    else:
        flash('Error. Try again')
        return redirect(url_for('registration'))


# noinspection PyBroadException
@app.route('/download/<path:file_path>', methods=['GET', 'POST'])
def download(file_path):
    try:
        if PATH_TO_FILES in file_path and session.get('user_operation_id') in file_path:
            splited = file_path.split('/')
            filename = splited[-1]
            path = '/'.join(splited[:-1])
            return send_from_directory(path, filename, as_attachment=True)
        return redirect(url_for('index'))
    except Exception:
        flash('Sorry, an unknown error occurred while getting the link to download the file.'
              ' Please try again later', category='danger')
        return redirect(url_for('index'))


def check_operation_id():
    session['user_operation_id'] = uuid.uuid4().hex if session.get('user_operation_id') is None \
        else session.get('user_operation_id')



def check_content_length(length):
    try:
        length = int(length)
        if current_user.is_authenticated:
            if length > MAX_CONTENT_LENGTH_FOR_AUTH:
                flash('Max file size is 400 MB', category='danger')
                return 'limit'
        else:
            if length > MAX_CONTENT_LENGTH_FOR_UNAUTH:
                flash('Max file size for unauthorized users is 100 MB', category='danger')
                return 'limit'
        return None
    except Exception as e:
        return 'error', e


if __name__ == '__main__':
    app.run(port=8000, host='127.0.0.1')
