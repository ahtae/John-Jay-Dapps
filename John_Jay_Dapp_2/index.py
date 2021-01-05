import time
import contract_abi
from database import Database
import tkinter as tk
import merkletools
import os
import sys
import hashlib
import base64
from web3 import Web3, HTTPProvider
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox, Text
from PIL import Image, ImageTk
from decouple import config

merkleRoot = ''
graduating_class = None
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
student_hash = tk.StringVar()

def submit():
    answer = messagebox.askyesno(
        'Question', 'Is the graduating class correct?')

    if(answer):
        getMerkleRoot()
        proof()
    else:
        return 'Please fix the graduating class!'

def getMerkleRoot():
    global semester
    global year
    global graduating_class
    global merkleRoot

    semester_value = semester.get()
    year_value = year.get()
    student_hash_value = student_hash.get()

    if not (student_hash_value == '' or semester_value ==
            '' or year_value == ''):
        converted_semester_value = semester_to_num[semester_value]
        graduating_class = int(converted_semester_value + year_value)
        merkleRoot = contract.functions.getRoot(graduating_class).call()
    else:
        messagebox.showinfo(
            'Uh Oh',
            'Submitted form is not completely filled out! Please fill out the form completely before submitting, thank you!')

def proof():
    mt = merkletools.MerkleTools()

    if not merkleRoot:
        messagebox.showinfo(
            'Uh Oh',
            f'This graduating class does not exist!')
        return

    db = Database(
        config('DATABASE'),
        config('USER'),
        config('PASSWORD'),
        config('HOST'),
        config('PORT'))
    db_cursor = db.cursor

    select_hashes_command = f'SELECT hash FROM gc{graduating_class}'

    db_cursor.execute(select_hashes_command)
    index = None
    count = 0

    rows = db_cursor.fetchall()

    db.close()

    for row in rows:
        hash = row[0]
        if hash == student_hash.get():
            index = count
        count += 1
        mt.add_leaf(hash)

    mt.make_tree()

    if index is None:
        messagebox.showinfo(
            'Uh Oh',
            f'This hash is not part of the graduating class.')
        return

    hex_merkle_root = hex(merkleRoot).split('x')[-1]
    merkle_proof = mt.get_proof(index)

    is_valid = mt.validate_proof(
        merkle_proof,
        student_hash.get(),
        hex_merkle_root)

    if index is None or not is_valid:
        messagebox.showinfo(
            'Uh Oh',
            f'This hash is not part of the graduating class.')
        return
    else:
        answer = messagebox.askyesno(
            'Question', 'Would you like to send this to your employer?')

        if(answer):
            send_link_to_employer(str(merkle_proof))

def send_link_to_employer(merkle_proof):
    file = open('merkle_proof.txt', 'w+')
    file.write(merkle_proof)
    file.close()

    import send_email

def quit():
    exit()

def restart():
    python3 = sys.executable
    os.execl(python3, python3, *sys.argv)

root.title('Welcome to JJay Dapp2')
root.geometry('900x400')
root.configure(background='white')

frame = tk.Frame(root, bg='pale green')
frame.place(relx=0, rely=0.2, relwidth=1, relheight=1)

logo = tk.PhotoImage(file='./assets/images/diploma_logo.gif')
diploma_logo = logo.subsample(15, 15)
tk.Label(root, image=diploma_logo).place(x=190, y=0)

title_label = tk.Label(root, text='JJay Dapp2', font='Verdana 24 bold')
title_label.place(x=270, y=20)

semester_label = tk.Label(root, text='Semester')
semester_label.config(bg='pale green')
semester_label.place(x=170, y=115)

semester_drop_list = tk.OptionMenu(root, semester, *semester_list)
semester_drop_list.config(width=17, bg='pale green')
semester.set('Select the semester')
semester_drop_list.place(x=267, y=110)

year_label = tk.Label(root, text='Year')
year_label.config(bg='pale green')
year_label.place(x=200, y=150)

year_drop_list = tk.OptionMenu(root, year, *year_list)
year_drop_list.config(width=14, bg='pale green')
year.set('Select the year')
year_drop_list.place(x=267, y=150)

hash_label = tk.Label(root, text='Hash', width=3)
hash_label.config(bg='pale green')
hash_label.place(x=195, y=190)

hash_entry = tk.Entry(root, textvariable=student_hash, width=60)
hash_entry.place(x=270, y=190)

restart_button = tk.Button(root, text='Restart', command=restart)
restart_button.config(highlightbackground='pale green')
restart_button.place(x=160, y=310)

quit_button = tk.Button(root, text='Quit', command=quit)
quit_button.config(highlightbackground='pale green')
quit_button.place(x=270, y=310)

submit_button = tk.Button(root, text='Submit', command=submit)
submit_button.config(highlightbackground='pale green')
submit_button.place(x=360, y=310)

root.resizable(False, False)
root.mainloop()
