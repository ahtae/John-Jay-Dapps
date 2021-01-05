import time
from database import Database
import contract_abi
import tkinter as tk
import merkletools
import os
import sys
import hashlib
import PyPDF2
import re
import mysql.connector
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox, Text
from web3 import Web3, HTTPProvider
from PIL import Image, ImageTk
from decouple import config

merkleRoot = ''
dirname = ''
files_seen = {}
emplids = []
digests = []
semester_list = ['Fall', 'Winter', 'Spring', 'Summer']
year_list = [str(year) for year in range(2021, 1899, -1)]
semester_to_num = {'Fall': '1', 'Winter': '2', 'Spring': '3', 'Summer': '4'}

contract_address = Web3.toChecksumAddress(config('CONTRACT_ADDRESS'))
wallet_private_key = config('WALLET_PRIVATE_KEY')
wallet_address = config('WALLET_ADDRESS')

w3 = Web3(HTTPProvider(config('WEB3_PROVIDER')))
w3.eth.enable_unaudited_features()

contract = w3.eth.contract(address=contract_address, abi=contract_abi.abi)

root = tk.Tk()
semester = tk.StringVar()
year = tk.StringVar()

def determine_valid_directory(dirname):
    files = os.listdir(dirname)

    if not len(files):
        messagebox.showinfo(
            'Uh Oh',
            "This directory is empty. Please select a directory isn't empty.")

        return False

    for file in files:
        is_file_a_pdf = os.path.splitext(file)[1].lower() in ('.pdf')

        if os.path.isdir(file):
            messagebox.showinfo(
                'Uh Oh',
                'This directory contains a subdirectory. Please select a directory that contains only files.')

            return False
        elif file == '.DS_Store':
            continue
        elif not is_file_a_pdf:
            messagebox.showinfo(
                'Uh Oh',
                'This directory contains a file type that is not supported. Please select a directory that contains only PDF files.')

            return False
        else:
            try:
                file_path = dirname + '/' + file
                PyPDF2.PdfFileReader(open(file_path, 'rb'))
            except PyPDF2.utils.PdfReadError:
                messagebox.showinfo(
                    'Uh Oh',
                    'Invalid PDF file!')

                return False
    return True

def get_emplids_from_pdf(dirname):
    global emplids

    files = os.listdir(dirname)

    for file in files:
        seen_file = files_seen.get(file, False)

        if file == '.DS_Store':
            continue

        if not seen_file:
            file_path = dirname + '/' + file
            emplid_regex = re.compile(r'\d\d\d\d\d\d\d\d')
            pdf_file_object = open(file_path, 'rb')
            pdf_reader = PyPDF2.PdfFileReader(pdf_file_object)
            pdf_page_object = pdf_reader.getPage(0)
            transcript = pdf_page_object.extractText()
            mo = emplid_regex.search(transcript)
            student_emplid = mo.group()
            pdf_file_object.close()
            emplids.append(student_emplid)
            files_seen[file] = True

def calculate_hashed_digests(mt, dirname):
    global emplids
    global digests

    if not dirname:
        messagebox.showinfo(
            'Uh Oh',
            "This directory is empty. Please select a directory isn't empty.")

        return

    is_a_valid_directory = determine_valid_directory(dirname)

    if is_a_valid_directory:
        get_emplids_from_pdf(dirname)
        count = 0

        for emplid in emplids:
            mt.add_leaf(emplid, True)
            digests.append(mt.get_leaf(count))
            count += 1

    return digests

def create_merkle_tree():
    global merkle_root_place_holder
    global merkleRoot
    global dirname

    mt = merkletools.MerkleTools()
    calculate_hashed_digests(mt, dirname)
    mt.make_tree()
    assert(mt.is_ready)
    root_val = mt.get_merkle_root()
    merkle_root_place_holder.configure(text=root_val)
    merkleRoot = int(mt.get_merkle_root(), 16)

def clicked():
    global dirname

    dirname = filedialog.askdirectory()

def send_ether_to_contract(graduating_class, amount_in_ether):
    amount_in_wei = w3.toWei(amount_in_ether, 'gwei')
    nonce = w3.eth.getTransactionCount(wallet_address)

    txn_dict = contract.functions.addSemester(merkleRoot, graduating_class).buildTransaction(
        {'chainId': 3, 'gas': 2000000, 'gasPrice': amount_in_wei, 'nonce': nonce, })

    signed_txn = w3.eth.account.signTransaction(txn_dict, wallet_private_key)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    txn_receipt = None

    count = 0

    while txn_receipt is None and (count < 30):
        txn_receipt = w3.eth.getTransactionReceipt(txn_hash)
        time.sleep(10)

    if txn_receipt is None:
        return {
            'status': 'failed',
            'message': 'This transaction took too long! Please try again!'}

    return {
        'status': 'added',
        'message': 'This transaction was successful!',
        'txn_receipt': txn_receipt}

def submit():
    global dirname

    answer = messagebox.askyesno(
        'Question', 'Is the graduating class correct?')

    if(answer):
        create_merkle_tree()
        add_a_semester()
    else:
        return 'Please fix the graduating class!'

def add_a_semester():
    global semester
    global year

    semester_value = semester.get()
    year_value = year.get()

    if not (merkleRoot == '' or semester_value == '' or year_value == ''):
        sem = semester_to_num[semester_value]
        year = year.get()
        graduating_class = int(sem + year)

        transaction_receipt = send_ether_to_contract(graduating_class, '40')
        transaction_status = transaction_receipt['status']
        transaction_message = transaction_receipt['message']

        if transaction_status == 'failed':
            messagebox.showinfo(
                'Uh Oh',
                f"This transaction failed. {transaction_message}")
        else:
            processed_receipt = transaction_receipt['txn_receipt']

            db = Database(
                config('DATABASE'),
                config('USER'),
                config('PASSWORD'),
                config('HOST'),
                config('PORT'))
            db_cursor = db.cursor

            create_table_command = f"CREATE TABLE gc{graduating_class} (id SERIAL PRIMARY KEY, emplid VARCHAR(8) NOT NULL, hash TEXT NOT NULL)"

            db_cursor.execute(create_table_command)

            for i in range(0, len(emplids)):
                insert_information_command = f"INSERT INTO gc{graduating_class} (emplid, hash) VALUES (%s, %s)"

                current_student_record = (emplids[i], digests[i])

                db_cursor.execute(
                    insert_information_command,
                    current_student_record)

            db.close()

            transaction_block = processed_receipt.transactionHash

            messagebox.showinfo(
                'Successful!',
                f"This transaction was successful. Your transaction was {transaction_block}.")
    else:
        messagebox.showinfo(
            'Uh Oh',
            'Submitted form is not completely filled out! Please fill it out completely before submitting!')

def quit():
    exit()

def restart():
    python3 = sys.executable
    os.execl(python3, python3, *sys.argv)

root.title('Welcome to JJay Dapp1!')
root.geometry('900x400')
root.configure(background='white')

frame = tk.Frame(root, bg='gray')
frame.place(relx=0, rely=0.2, relwidth=1, relheight=1)

logo = tk.PhotoImage(file='./assets/images/diploma_logo.gif')
diploma_logo = logo.subsample(4, 4)
tk.Label(root, image=diploma_logo).place(x=170, y=0)

title_label = tk.Label(root, text='JJay Dapp1', font='Verdana 24 bold')
title_label.place(x=270, y=20)

semester_label = tk.Label(root, text='Semester')
semester_label.config(bg='gray')
semester_label.place(x=170, y=115)

semester_drop_list = tk.OptionMenu(root, semester, *semester_list)
semester_drop_list.config(width=17, bg='gray')
semester.set('Select the semester')
semester_drop_list.place(x=267, y=110)

year_label = tk.Label(root, text='Year')
year_label.config(bg='gray')
year_label.place(x=200, y=150)

year_drop_list = tk.OptionMenu(root, year, *year_list)
year_drop_list.config(width=14, bg='gray')
year.set('Select the year')
year_drop_list.place(x=267, y=150)

select_directory_label = tk.Label(root, text='Directory of Graduating Class')
select_directory_label.config(bg='gray')
select_directory_label.place(x=40, y=195)

select_directory_button = tk.Button(
    root, text='Select Directory', command=clicked)
select_directory_button.config(highlightbackground='gray')
select_directory_button.place(x=267, y=190)

merkle_root_label = tk.Label(root, text='Merkle Root', width=14)
merkle_root_label.config(bg='gray')
merkle_root_label.place(x=130, y=235)

merkle_root_place_holder = tk.Label(root, text='')
merkle_root_place_holder.config(width=60)
merkle_root_place_holder.place(x=270, y=230)

restart_button = tk.Button(root, text='Restart', command=restart)
restart_button.config(highlightbackground='gray')
restart_button.place(x=160, y=310)

quit_button = tk.Button(root, text='Quit', command=quit)
quit_button.config(highlightbackground='gray')
quit_button.place(x=270, y=310)

submit_button = tk.Button(root, text='Submit', command=submit)
submit_button.config(highlightbackground='gray')
submit_button.place(x=360, y=310)

root.resizable(False, False)
root.mainloop()
