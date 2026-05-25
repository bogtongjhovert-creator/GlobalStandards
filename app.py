from flask import Flask, request, redirect, url_for, render_template_string, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qa_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    objectives = db.Column(db.Text, nullable=False)
    venue = db.Column(db.String(255), nullable=False)
    activity_date = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, nullable=False)
    participants = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email='admin@qa.com').first():
        admin = User(
            fullname='QA Administrator',
            email='admin@qa.com',
            password=generate_password_hash('admin123'),
            role='Admin'
        )
        db.session.add(admin)
        db.session.commit()

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')

    return render_template_string("""
    <h2>QA Activity Proposal System</h2>
    <form method="POST">
        <input type="email" name="email" placeholder="Email" required><br><br>
        <input type="password" name="password" placeholder="Password" required><br><br>
        <button type="submit">Login</button>
    </form>
    <p>Default Admin: admin@qa.com / admin123</p>
    """)

@app.route('/dashboard')
def dashboard():
    user = current_user()

    if not user:
        return redirect(url_for('login'))

    proposals = Proposal.query.order_by(Proposal.created_at.desc()).all()

    html = """
    <h1>Dashboard</h1>
    <a href='/create'>Create Proposal</a> | <a href='/logout'>Logout</a>
    <hr>
    <table border='1' cellpadding='10'>
    <tr>
        <th>ID</th>
        <th>Title</th>
        <th>Status</th>
        <th>Actions</th>
    </tr>
    """

    for p in proposals:
        html += f"""
        <tr>
            <td>{p.id}</td>
            <td>{p.title}</td>
            <td>{p.status}</td>
            <td>
                <a href='/approve/{p.id}'>Approve</a> |
                <a href='/reject/{p.id}'>Reject</a>
            </td>
        </tr>
        """

    html += "</table>"
    return html

@app.route('/create', methods=['GET', 'POST'])
def create_proposal():
    user = current_user()

    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        proposal = Proposal(
            title=request.form['title'],
            objectives=request.form['objectives'],
            venue=request.form['venue'],
            activity_date=request.form['activity_date'],
            budget=float(request.form['budget']),
            participants=request.form['participants'],
            user_id=user.id
        )

        db.session.add(proposal)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template_string("""
    <h2>Create Proposal</h2>
    <form method='POST'>
        <input type='text' name='title' placeholder='Title' required><br><br>
        <textarea name='objectives' placeholder='Objectives'></textarea><br><br>
        <input type='text' name='venue' placeholder='Venue'><br><br>
        <input type='date' name='activity_date'><br><br>
        <input type='number' step='0.01' name='budget' placeholder='Budget'><br><br>
        <input type='text' name='participants' placeholder='Participants'><br><br>
        <button type='submit'>Submit</button>
    </form>
    """)

@app.route('/approve/<int:id>')
def approve(id):
    proposal = Proposal.query.get_or_404(id)
    proposal.status = 'Approved'
    proposal.remarks = 'Approved by QA Office'
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/reject/<int:id>')
def reject(id):
    proposal = Proposal.query.get_or_404(id)
    proposal.status = 'Rejected'
    proposal.remarks = 'Rejected by QA Office'
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
