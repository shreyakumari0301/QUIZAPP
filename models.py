
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False) 
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    is_admin = db.Column(db.Boolean, default=False) 


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(80))
    chapters = db.relationship('Chapter', back_populates='related_course')
    quizzes = db.relationship('Quiz', back_populates='related_course')

class Chapter(db.Model):
    __tablename__ = "chapters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    related_course = db.relationship('Course', back_populates='chapters')
    questions = db.relationship('Question', back_populates='chapter')
    quizzes = db.relationship('Quiz', back_populates='chapter')

class Quiz(db.Model):
    __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.String(10))  # Format: hh:mm
    remarks = db.Column(db.String(255))
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)

    related_course = db.relationship('Course', back_populates='quizzes')
    chapter = db.relationship('Chapter', back_populates='quizzes')
    questions = db.relationship('Question', back_populates='quiz', lazy=True)

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    question_statement = db.Column(db.String(255), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100))
    option4 = db.Column(db.String(100))
    correct_answer = db.Column(db.String(100), nullable=False)

    quiz = db.relationship('Quiz', back_populates='questions')
    chapter = db.relationship('Chapter', back_populates='questions')

class StudentQuizAttempt(db.Model):
    __tablename__ = 'student_quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    student_answers = db.Column(db.JSON)  
    
    student = db.relationship('User', backref=db.backref('quiz_attempts', lazy=True))
    quiz = db.relationship('Quiz', backref=db.backref('student_attempts', lazy=True))

def init_db(app):
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username='admin@example.com').first() is None:
            admin = User(
                username='admin@example.com',  
                full_name='Quiz Master',       
                qualification='Admin',          
                dob=datetime.strptime('2000-01-01', '%Y-%m-%d').date(),
                is_admin=True                   
            )
            admin.set_password('20210')  
            db.session.add(admin)
            db.session.commit()