from flask import render_template, request, Blueprint, current_app, flash
from flask import Flask, render_template, request, session, url_for, redirect, request, abort
from web3 import Web3, HTTPProvider
from decouple import config
import dapp.employer_form.contract_abi as contract_abi
import merkletools
import time
import json
import os
import sys
import hashlib
import base64
from web3 import Web3, HTTPProvider
from PIL import Image, ImageTk
from decouple import config
from werkzeug.utils import secure_filename
from dapp.employer_form.form import EmployerForm

employer_form = Blueprint('employer_form', __name__)

@employer_form.route('/form', methods=('GET', 'POST'))
def form():
    form = EmployerForm()

    semester_to_num = {
        'Fall': '1',
        'Winter': '2',
        'Spring': '3',
        'Summer': '4'}
    semester_value = form.semester.data
    year_value = form.year.data
    student_hash = form.hash.data

    session['semester'] = semester_value
    session['year'] = year_value
    session['hash'] = student_hash
    session['submitted_form'] = True

    if form.validate_on_submit():
        session['semester'] = semester_value
        session['year'] = year_value
        session['hash'] = student_hash
        session['submitted_form'] = True

        if semester_value and year_value and student_hash:
            try:
                uploaded_file = request.files['file']
                filename = secure_filename(uploaded_file.filename)

                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
                        abort(400)
                    uploaded_file.save(
                        os.path.join(
                            current_app.config['UPLOAD_PATH'],
                            f'merkle_proof_{student_hash}.txt'))
            except:
                abort(400)

            contract_address = Web3.toChecksumAddress(
                config('CONTRACT_ADDRESS'))

            w3 = Web3(HTTPProvider(config('WEB3_PROVIDER')))
            w3.eth.enable_unaudited_features()

            contract = w3.eth.contract(
                address=contract_address, abi=contract_abi.abi)

            converted_semester_value = semester_to_num[semester_value]
            graduating_class = int(converted_semester_value + year_value)
            merkle_root = contract.functions.getRoot(graduating_class).call()

            if merkle_root:
                mt = merkletools.MerkleTools()

                hex_merkle_root = hex(merkle_root).split('x')[-1]

                merkle_proof_file = open(
                    f'uploads/merkle_proof_{student_hash}.txt', 'r')
                merkle_proof_string = merkle_proof_file.read().replace("'", '"')
                merkle_proof = json.loads(merkle_proof_string)

                is_valid = mt.validate_proof(
                    merkle_proof,
                    student_hash,
                    hex_merkle_root)

                session['is_valid'] = is_valid

        return redirect(url_for('result.verification'))

    return render_template('form.html', form=form)
