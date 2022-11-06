from flask import Flask, render_template,redirect, url_for, request, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import random
# from models import Blog, User, db
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

base_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(base_dir, 'blogga.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret"

login_manager = LoginManager()
login_manager.init_app(app)

class Blog(db.Model):
    __tablename__ = "Blog"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_published = db.Column(db.DateTime)
    author = db.Column(db.String, default="Iniobong Benson")
    
    def __repr__(self):
        return f"<Blog {self.id}"


class User(db.Model, UserMixin):
    __tablename__ = "User"

    id = db.Column(db.Integer(), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return f"{self.first_name}"

db.create_all()

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)

@app.route('/', methods=['GET'])
def index():
    posts = Blog.query.all()
    return render_template('index.html', posts=posts)

@app.route('/blog')
def blog():
    if current_user.is_authenticated:
        blog = Blog.query.filter_by(author=str(current_user)).all()
        return render_template('blog/blog.html', user_posts=blog)
    else:
        return redirect(url_for('login'))

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    if request.method == "POST":
        title = request.form.get('title')
        content = request.form.get('content')
        date_published = datetime.now()
        author = current_user.first_name
        new_post = Blog(title=title, content=content, date_published=date_published, author=author)
        if new_post is None:
            flash("Error - Your post title or content is empty")
            return redirect(url_for('post'))
        else:
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('blog'))
    return render_template('blog/create.html')

@app.route('/post/<int:id>')
def get_post(id):
    post = Blog.query.filter_by(id=id).first()
    other_posts = random.sample(Blog.query.all(), 3)
    if post:
        return render_template('blog/post_detail.html', post=post, other_posts=other_posts)
    else:
        flash('That post no longer exists or was never created')
        return redirect(url_for('index'))

@app.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Blog.query.get_or_404(id)
    if post.author != current_user.first_name:
        flash("You don't have permission to edit this post")
        return redirect(url_for('get_post', id=post.id))
        
        # abort(403, "<h1>You don't have permission to edit this post</h1>")
        
    if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            post.title = title
            post.content = content
            db.session.commit()
            return redirect(url_for('get_post', id=post.id))
    else:

        return render_template('blog/edit_post.html', post=post)
   
    
    
@app.route('/post/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    post = Blog.query.get_or_404(id)
    if post.author != current_user.first_name:
        abort(403)
    else:
        
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully')
        return redirect(url_for('blog'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
    if request.method == 'POST':
        message = Mail(
            from_email=request.form.get('email'),
            to_emails='linibensojr@example.com',
            subject=request.form.get('subject'),
            html_content=request.form.get('message'))
        flash('Message sent successfully')
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
            flash('Message sent successfully')
        except Exception as e:
            pass
    return render_template('contact.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        flash('You were successfully logged in')
        return redirect(url_for('blog'))
    else:
        flash('Invalid username or password')
        return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash("Account already exists")
            return redirect(url_for('signup'))

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash("Email already taken")
            return redirect(url_for('signup'))

        password_hash = generate_password_hash(password)

        new_user = User(first_name=first_name, last_name=last_name, username=username, email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('auth/signup.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)