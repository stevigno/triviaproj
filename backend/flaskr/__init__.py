import os
import random
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={'/': {'origins': '*'}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
        response.headers.add(
            'Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route("/categories")
    def all_categories():
        cat = Category.query.order_by(Category.id).all()
        cat_data_format = {}
        # error data categories
        if cat is None:
            abort(400)

        for c in cat:
            cat_data_format[c.id] = c.type
        return jsonify({
            'success': True,
            'categories': cat_data_format
        }), 200

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions')
    def all_questions():
        questions = Question.query.order_by(Question.id).all()
        cat = Category.query.order_by(Category.id).all()
        current_questions = pagination(request, questions, QUESTIONS_PER_PAGE)
        cat_format = {}
        if len(current_questions) is None:
            abort(404)

        # Format category data
        for c in cat:
            cat_format[c.id] = c.type

        return jsonify({
            'success': True,
            'total_questions': len(current_questions),
            'categories': cat_format,
            'questions': current_questions,
        }), 200

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route("/questions/<int:quest_id>", methods=['DELETE'])
    def delete_questions(quest_id):
        try:
            quest = Question.query.filter(Question.id == quest_id).one_or_none()

            if quest is None:
                abort(404)

            quest.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = pagination(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": quest_id,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                }
            )
        except:
            abort(422)


    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=['POST'])
    def create_question():

        body = request.get_json()

        new_question = body.get('question')
        new_answer = body.get('answer')
        new_category = body.get('category')
        new_difficulty = body.get('difficulty')

        if (body, new_question, new_answer, new_category, new_difficulty) is None:
            abort(400)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty
            )
            question.insert()
            all_quest = Question.query.order_by(Question.id).all()
            current_questions = pagination(request, all_quest)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        data = request.get_json()
        search_term = data.get('searchTerm', " ")
        if search_term == " ":
            abort(422)

        try:
            questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
            pag_questions = pagination(request, questions, QUESTIONS_PER_PAGE)
            return jsonify({
                'success': True,
                'questions': pag_questions,
                'total_questions': len(Question.query.all())
            }), 200

        except:
            abort(500)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):
        try:
            category = Category.query.filter_by(id=id).one_or_none()
            questions = Question.query.filter_by(category=id).all()

            pg_questions = pagination(request, questions, QUESTIONS_PER_PAGE)
            return jsonify({
                'success': True,
                'questions': pg_questions,
                'total_questions': len(questions),
                'current_category': category.type
            })
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def quiz():
        global quiz
        try:
            data = request.get_json()
            prs_questions = data.get('previous_questions')
            quiz = data.get('quiz_category')

            if (quiz['id'] == 0):
                questions = Question.query.all()
            else:
                questions = Question.query.filter_by(
                    category=quiz['id']).all()

            def random_questions():
                return questions[random.randint(0, len(questions) - 1)]

            next_question = random_questions()
            found = True

            while found:
                if next_question.id in prs_questions:
                    next_question = random_questions()
                else:
                    found = False

            return jsonify({
                'success': True,
                'question': next_question.format(),
            }), 200
        except:
            if quiz is None:
                abort(400)
            else:
                abort(422)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(500)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 500, "message": "method not allowed"}),
            500,
        )

    return app


def pagination(request, selection, QUESTIONS_PER_PAGE):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_question = questions[start:end]

    return current_question
