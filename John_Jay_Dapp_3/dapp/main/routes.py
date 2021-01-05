from flask import render_template, request, Blueprint, session

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    session['semester'] = None
    session['year'] = None
    session['hash'] = None
    session['submitted_form'] = False
    session['is_valid'] = False

    return render_template('home.html')
