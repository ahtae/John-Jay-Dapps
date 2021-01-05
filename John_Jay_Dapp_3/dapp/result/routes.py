from flask import render_template, request, Blueprint, session, redirect, url_for

result = Blueprint('result', __name__)

@result.route('/verification')
def verification():
    semester = session['semester']
    year = session['year']
    hash = session['hash']
    submitted_form = session['submitted_form']

    if not (semester and year and hash and submitted_form):
        return redirect(url_for('main.home'))

    return render_template('verification.html')
