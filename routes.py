from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
from models import db, User, Course, Chapter, Question, Quiz, StudentQuizAttempt
from flask import Blueprint

app = Blueprint('routes', __name__)

@app.route('/')
def home():
    user_id = session.get('user_id')  
    user = User.query.get(user_id) if user_id else None  
    search_query = request.args.get('query', '').strip()  
    courses = []

    if user:
        if search_query:
            courses = Course.query.filter(
                Course.category == user.qualification,
                Course.name.ilike(f"%{search_query}%")
            ).all()
        else:
            courses = Course.query.filter_by(category=user.qualification).all()

    return render_template('HomePage.html', user=user, courses=courses)  


# @app.route('/')
# def home():
#     user_id = session.get('user_id')  # Get user ID from session
#     user = User.query.get(user_id) if user_id else None  # Fetch user if logged in
#     courses = []

#     if user:
#         courses = Course.query.filter_by(category=user.qualification).all()  # Fetch courses based on user's qualification

#     return render_template('HomePage.html', user=user, courses=courses)  # Pass user and courses to template

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        qualification = request.form['qualification']
        dob = request.form['dob']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('routes.register'))

        new_user = User(
            username=username,
            full_name=full_name,
            qualification=qualification,
            dob=datetime.strptime(dob, '%Y-%m-%d').date()  
        )
        new_user.set_password(password)  
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('routes.login'))

    return render_template('register.html')  

@app.route('/search_courses', methods=['GET'])
def search_courses():
    query = request.args.get('query', '').strip()
    if query:
        courses = Course.query.filter(Course.name.ilike(f"%{query}%")).all()
    else:
        courses = Course.query.all()
    
    return render_template("HomePage.html", courses=courses)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id  
            session['is_admin'] = user.is_admin  
            flash('Login successful!', 'success')
            if user.is_admin:
                return redirect(url_for('routes.admin_dashboard'))  
            return redirect(url_for('routes.home'))  
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')  

@app.route('/logout')
def logout():
    session.pop('user_id', None) 
    flash('You have been logged out.', 'success') 
    return redirect(url_for('routes.home'))  

@app.route('/courses', methods=['GET', 'POST'])
def courses():
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')

    query = Course.query
    if search_query:
        query = query.filter(Course.name.ilike(f'%{search_query}%'))
    if category_filter:
        query = query.filter(Course.category == category_filter)

    courses = query.all()
    return render_template('courses.html', courses=courses, search_query=search_query, category_filter=category_filter)

@app.route('/add_course', methods=['POST'])
def add_course():
    course_name = request.form['course_name']
    category = request.form['category']
    new_course = Course(name=course_name, category=category)
    db.session.add(new_course)
    db.session.commit()
    flash('Course added successfully!', 'success')
    return redirect(url_for('routes.admin_dashboard')) 

@app.route('/admin/dashboard', methods=['POST', 'GET'])
def admin_dashboard():
    search_query = request.form.get('search', '')

    categorized_courses = {
        'Foundation': [],
        'Diploma': [],
        'Degree': []
    }

    if search_query:
        courses = Course.query.filter(Course.name.ilike(f"%{search_query}%")).all()
    else:
        courses = Course.query.all()

    for course in courses:
        if course.category in categorized_courses:
            categorized_courses[course.category].append(course)
        else:
            categorized_courses.setdefault(course.category, []).append(course)

    return render_template('admin_dashboard.html', categorized_courses=categorized_courses, search_query=search_query)

@app.route('/chapters/<int:course_id>', methods=['GET', 'POST'])
def chapters(course_id):
    course = Course.query.get(course_id) 
    all_chapters = Chapter.query.filter_by(course_id=course_id).all()  

    search_query = request.form.get('search', '').strip().lower()

    if not search_query:
        return render_template('chapters.html', course=course, chapters=all_chapters)

    filtered_chapters = []
    
    for chapter in all_chapters:
        if search_query in chapter.name.lower():
            filtered_chapters.append(chapter)  
        else:
            matching_quizzes = [quiz for quiz in chapter.quizzes if search_query in quiz.name.lower()]
            if matching_quizzes:
                chapter_copy = Chapter(id=chapter.id, name=chapter.name, course_id=chapter.course_id)
                chapter_copy.quizzes = matching_quizzes
                filtered_chapters.append(chapter_copy)

    return render_template('chapters.html', course=course, chapters=filtered_chapters, search_query=search_query)

# @app.route('/chapters/<int:course_id>')
# def chapters(course_id):
#     course = Course.query.get(course_id)  # Fetch the course by ID
#     chapters = Chapter.query.filter_by(course_id=course_id).all()  
#     # Fetch chapters for the selected course
#     questions = Question.query.filter(Question.chapter_id.in_([c.id for c in chapters])).all()
    
#     return render_template('chapters.html', course=course, chapters=chapters, questions = questions)

@app.route('/add_chapter', methods=['POST'])
def add_chapter():
    chapter_name = request.form['chapter_name']
    course_id = request.form['course_id']
    new_chapter = Chapter(name=chapter_name, course_id=course_id)
    db.session.add(new_chapter)
    db.session.commit()
    flash('Chapter added successfully!', 'success')
    return redirect(url_for('routes.chapters', course_id=course_id))

@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    course = Course.query.get_or_404(chapter.course_id) 
    
    if request.method == 'POST':
        try:
            chapter_name = request.form.get('chapter_name')
            if not chapter_name:
                flash('Chapter name is required!', 'danger')
            else:
                chapter.name = chapter_name
                db.session.commit()
                flash('Chapter updated successfully!', 'success')
                return redirect(url_for('routes.chapters', course_id=chapter.course_id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating chapter. Please try again.', 'danger')
            print(f"Error: {str(e)}")
    
    return render_template('chapters.html', edit_chapter=chapter, course=course, chapters=course.chapters)

@app.route('/chapters/<int:chapter_id>/delete', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    try:
        quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        
        for quiz in quizzes:
            StudentQuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
            
            Question.query.filter_by(quiz_id=quiz.id).delete()
            
            db.session.delete(quiz)
        
        db.session.delete(chapter)
        db.session.commit()
        flash('Chapter and all associated content deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting chapter. Please try again.', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('routes.chapters', course_id=chapter.course_id))
    
@app.route('/add_question', methods=['POST'])
def add_question():
    try:
        question_statement = request.form['question_statement']
        quiz_id = request.form['quiz_id']
        chapter_id = request.form['chapter_id']
        
        print(f"Received chapter_id: {chapter_id}")
        
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_answer = request.form.get('correct_answer')

        new_question = Question(
            question_statement=question_statement,
            quiz_id=quiz_id,
            chapter_id=chapter_id,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_answer=correct_answer
        )
        
        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        
    except Exception as e:
        print(f"Error: {str(e)}") 
        flash('Error adding question. Please try again.', 'error')
        db.session.rollback()
        
    return redirect(url_for('routes.view_questions', quiz_id=quiz_id))

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!', 'success')
    else:
        flash('Question not found!', 'danger')
    return redirect(url_for('routes.view_questions', quiz_id=question.quiz_id))

@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get(course_id)
    if request.method == 'POST':
        course.name = request.form['course_name']
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('routes.admin_dashboard'))
    return render_template('edit_course.html', course=course)

@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    try:
        chapters = Chapter.query.filter_by(course_id=course_id).all()
        
        for chapter in chapters:
            quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
            
            for quiz in quizzes:
                StudentQuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
                
                Question.query.filter_by(quiz_id=quiz.id).delete()
                
                db.session.delete(quiz)
            
            db.session.delete(chapter)
        
        db.session.delete(course)
        db.session.commit()
        flash('Course and all associated content deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting course. Please try again.', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('routes.admin_dashboard'))

@app.route('/quizzes/<int:quiz_id>/questions', methods=['GET'])
def view_questions(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash('Quiz not found!', 'danger')
        return redirect(url_for('routes.chapters', course_id=quiz.chapter.course_id))
    
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    chapter_id = quiz.chapter.id if quiz.chapter else None 

    return render_template('view_questions.html', quiz=quiz, questions=questions, chapter_id = chapter_id)



# @app.route('/questions/<int:chapter_id>')
# def view_questions(chapter_id):
#     chapter = Chapter.query.get(chapter_id)
#     questions = Question.query.filter_by(chapter_id=chapter_id).all()  # Fetch questions for the selected chapter
#     return render_template('view_questions.html', chapter=chapter, questions=questions)


@app.route('/chapters/<int:chapter_id>/quizzes/add', methods=['POST'])
def add_quiz(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    quiz_name = request.form.get('quiz_name')
    date_of_quiz_str = request.form.get('date_of_quiz')
    time_duration = request.form.get('time_duration')
    remarks = request.form.get('remarks')

    if quiz_name and date_of_quiz_str:
        try:
            date_of_quiz = datetime.fromisoformat(date_of_quiz_str)
            current_time = datetime.utcnow()

            if date_of_quiz < current_time:
                flash('Quiz date cannot be in the past!', 'danger')
                return redirect(url_for('routes.chapters', course_id=chapter.course_id))

            new_quiz = Quiz(
                name=quiz_name,
                chapter_id=chapter_id,
                course_id=chapter.course_id,
                date_of_quiz=date_of_quiz,
                time_duration=time_duration,
                remarks=remarks
            )
            db.session.add(new_quiz)
            db.session.commit()
            flash('Quiz added successfully!', 'success')
        except ValueError:
            flash('Invalid date format!', 'danger')
    else:
        flash('Quiz name and date are required!', 'danger')
    
    return redirect(url_for('routes.chapters', course_id=chapter.course_id))

@app.route('/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name')
        date_of_quiz_str = request.form.get('date_of_quiz')
        time_duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')

        if quiz_name:
            date_of_quiz = datetime.fromisoformat(date_of_quiz_str) if date_of_quiz_str else None
            
            quiz.name = quiz_name
            quiz.date_of_quiz = date_of_quiz
            quiz.time_duration = int(time_duration) if time_duration else None
            quiz.remarks = remarks
            
            db.session.commit()
            flash('Quiz updated successfully!', 'success')
            return redirect(url_for('routes.chapters', course_id=quiz.chapter.course_id))
    return render_template('edit_quiz.html', quiz=quiz)

@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    
    if quiz:
        course_id = quiz.chapter.course_id
        
        db.session.delete(quiz)
        db.session.commit()
        
        return redirect(url_for('routes.chapters', course_id=course_id))
    
    return redirect(url_for('routes.chapters', course_id=None))  

@app.route('/chapters/<int:chapter_id>', methods=['GET'])
def view_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        flash('Chapter not found!', 'danger')
        return redirect(url_for('routes.home'))

    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()  
    return render_template('view_chapter.html', chapter=chapter, quizzes=quizzes)

@app.route('/quizzes/<int:quiz_id>/take_test', methods=['GET'])
def take_test(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash('Quiz not found!', 'danger')
        return redirect(url_for('routes.home'))

    questions = Question.query.filter_by(quiz_id=quiz_id).all() 
    due_date = quiz.date_of_quiz  
    return render_template('take_test.html', quiz=quiz, questions=questions, due_date=due_date)

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(question.quiz_id) 

    if request.method == 'POST':
        try:
            question_statement = request.form.get('question_statement')
            option1 = request.form.get('option1')
            option2 = request.form.get('option2')
            option3 = request.form.get('option3')
            option4 = request.form.get('option4')
            correct_answer = request.form.get('correct_answer')

            if not all([question_statement, option1, option2, option3, option4, correct_answer]):
                flash('All fields are required!', 'danger')
            else:
                question.question_statement = question_statement
                question.option1 = option1
                question.option2 = option2
                question.option3 = option3
                question.option4 = option4
                question.correct_answer = correct_answer

                db.session.commit()
                flash('Question updated successfully!', 'success')
                return redirect(url_for('routes.view_questions', quiz_id=quiz.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating question. Please try again.', 'danger')
            print(f"Error: {str(e)}")

    return render_template('view_questions.html', edit_question=question, quiz=quiz, questions=quiz.questions)

@app.route('/submit_test/<int:quiz_id>', methods=['POST'])
def submit_test(quiz_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to submit the test', 'warning')
        return redirect(url_for('routes.login'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    score = 0
    responses = {}
    
    for question in questions:
        selected_answer = request.form.get(f'question_{question.id}')
        responses[str(question.id)] = {
            'question_text': question.question_statement,
            'selected_option': selected_answer,
            'correct_option': question.correct_answer,
            'options': {
                '1': question.option1,
                '2': question.option2,
                '3': question.option3,
                '4': question.option4
            }
        }
        if selected_answer == question.correct_answer:
            score += 1
    
    attempt = StudentQuizAttempt(
        student_id=user_id,
        quiz_id=quiz_id,
        score=score,
        total_questions=len(questions),
        student_answers=responses,
        attempt_date=datetime.utcnow()
    )
    
    db.session.add(attempt)

    db.session.commit()
    
    flash(f'Quiz submitted! Your score: {score}/{len(questions)}', 'success')
    return redirect(url_for('routes.view_attempt', attempt_id=attempt.id))


@app.route('/view_attempt/<int:attempt_id>')
def view_attempt(attempt_id):
    attempt = StudentQuizAttempt.query.get(attempt_id)

    if not attempt:
        return "Attempt not found", 404

    quiz = Quiz.query.get(attempt.quiz_id)
    questions = Question.query.filter_by(quiz_id=attempt.quiz_id).all()

    return render_template('view_attempt.html', attempt=attempt, quiz=quiz, questions=questions)

@app.route('/student/chapters/<int:course_id>')
def student_chapters(course_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view chapters', 'warning')
        return redirect(url_for('routes.login'))
    
    user = User.query.get(user_id)
    course = Course.query.get_or_404(course_id)
    
    search_query = request.args.get('query', '').strip().lower()
    
    chapters = Chapter.query.filter_by(course_id=course_id).all()

    current_time = datetime.utcnow()

    student_attempts = StudentQuizAttempt.query.filter_by(student_id=user_id).all()
    attempted_quiz_ids = {attempt.quiz_id for attempt in student_attempts}

    last_attempts = {}
    for attempt in student_attempts:
        if attempt.quiz_id not in last_attempts or attempt.attempt_date > last_attempts[attempt.quiz_id].attempt_date:
            last_attempts[attempt.quiz_id] = attempt

    filtered_chapters = []
    for chapter in chapters:
        matching_quizzes = []
        for quiz in chapter.quizzes:
            quiz.attempted = quiz.id in attempted_quiz_ids
            if quiz.attempted:
                last_attempt = last_attempts[quiz.id]
                quiz.score = last_attempt.score
                quiz.total_questions = last_attempt.total_questions
                quiz.last_attempt_id = last_attempt.id

            if quiz.date_of_quiz:
                quiz_datetime = quiz.date_of_quiz
                if isinstance(quiz_datetime, date):
                    quiz_datetime = datetime.combine(quiz_datetime, datetime.min.time())

                quiz.is_available = current_time <= quiz_datetime
                quiz.is_deadline_close = (quiz_datetime - current_time).total_seconds() <= 86400 and quiz.is_available
            else:
                quiz.is_available = True
                quiz.is_deadline_close = False

            if search_query and search_query in quiz.name.lower():
                matching_quizzes.append(quiz)

        if search_query and search_query in chapter.name.lower():
            filtered_chapters.append(chapter)
        elif matching_quizzes:
            chapter.quizzes = matching_quizzes
            filtered_chapters.append(chapter)

    chapters_to_display = filtered_chapters if search_query else chapters

    return render_template('student_chapters.html', 
                           course=course,
                           chapters=chapters_to_display,
                           user=user,
                           search_query=search_query)


# @app.route('/student/chapters/<int:course_id>')
# def student_chapters(course_id):
#     # Get user from session
#     user_id = session.get('user_id')
#     if not user_id:
#         flash('Please log in to view chapters', 'warning')
#         return redirect(url_for('routes.login'))
    
#     user = User.query.get(user_id)
#     course = Course.query.get_or_404(course_id)
#     chapters = Chapter.query.filter_by(course_id=course_id).all()
    
#     # Get current time for date comparison
#     current_time = datetime.utcnow()
    
#     # Get all quiz attempts by the student
#     student_attempts = StudentQuizAttempt.query.filter_by(student_id=user_id).all()
#     attempted_quiz_ids = {attempt.quiz_id for attempt in student_attempts}
    
#     # Create a dictionary of last attempts for each quiz
#     last_attempts = {}
#     for attempt in student_attempts:
#         if attempt.quiz_id not in last_attempts or attempt.attempt_date > last_attempts[attempt.quiz_id].attempt_date:
#             last_attempts[attempt.quiz_id] = attempt
    
#     # Process quiz information for each chapter
#     for chapter in chapters:
#         for quiz in chapter.quizzes:
#             # Check if quiz has been attempted
#             quiz.attempted = quiz.id in attempted_quiz_ids
#             if quiz.attempted:
#                 last_attempt = last_attempts[quiz.id]
#                 quiz.score = last_attempt.score
#                 quiz.total_questions = last_attempt.total_questions
#                 quiz.last_attempt_id = last_attempt.id
            
#             # Check if quiz is available based on date_of_quiz
#             if quiz.date_of_quiz:
#                 quiz_datetime = quiz.date_of_quiz
#                 if isinstance(quiz_datetime, date):
#                     quiz_datetime = datetime.combine(quiz_datetime, datetime.min.time())
                
#                 quiz.is_available = current_time <= quiz_datetime
#                 quiz.is_deadline_close = (quiz_datetime - current_time).total_seconds() <= 86400 and quiz.is_available
#             else:
#                 quiz.is_available = True
#                 quiz.is_deadline_close = False
    
#     return render_template('student_chapters.html', 
#                          course=course,
#                          chapters=chapters,
#                          user=user)
    


@app.route('/admin/stats')
def admin_stats():
    foundation_count = User.query.filter_by(qualification='Foundation').count()
    diploma_count = User.query.filter_by(qualification='Diploma').count()
    degree_count = User.query.filter_by(qualification='Degree').count()

    attempts = StudentQuizAttempt.query.all()
    score_data = {
        'foundations': [],
        'diplomas': [],
        'degrees': []
    }

    for attempt in attempts:
        if attempt.student.qualification == 'Foundation':
            score_data['foundations'].append(attempt.score)
        elif attempt.student.qualification == 'Diploma':
            score_data['diplomas'].append(attempt.score)
        elif attempt.student.qualification == 'Degree':
            score_data['degrees'].append(attempt.score)

    avg_scores = {
        'foundation': (sum(score_data['foundations']) / len(score_data['foundations'])) if score_data['foundations'] else 0,
        'diploma': (sum(score_data['diplomas']) / len(score_data['diplomas'])) if score_data['diplomas'] else 0,
        'degree': (sum(score_data['degrees']) / len(score_data['degrees'])) if score_data['degrees'] else 0
    }

    return render_template('admin_stats.html', 
                           foundation_count=foundation_count, 
                           diploma_count=diploma_count, 
                           degree_count=degree_count,
                           avg_scores=avg_scores)


@app.route('/student/stats')
def user_stats():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your stats', 'warning')
        return redirect(url_for('routes.login'))
    
    user = User.query.get(user_id)  
    
    attempts = StudentQuizAttempt.query.filter_by(student_id=user_id).all()

    total_quizzes_taken = len(attempts)

    total_score = sum(attempt.score for attempt in attempts)
    average_score = total_score / total_quizzes_taken if total_quizzes_taken > 0 else 0

    submitted_count = sum(1 for attempt in attempts if attempt.attempt_date is not None)
    in_progress_count = sum(1 for attempt in attempts if attempt.attempt_date is None and attempt.score < attempt.total_questions)

    return render_template('student_stats.html', 
                           user=user,  
                           total_quizzes_taken=total_quizzes_taken,
                           average_score=average_score,
                           submitted_count=submitted_count,
                           in_progress_count=in_progress_count)




@app.route('/contact')
def contact():
    user_id = session.get('user_id')
    user = None
    
    if user_id:
        user = User.query.get(user_id)  
    
    return render_template('contact.html', user=user)