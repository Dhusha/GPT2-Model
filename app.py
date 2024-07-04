import streamlit as st
import mysql.connector
import bcrypt
import datetime
import re
import json
import torch
import pytz
import base64
import os
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# STreamlit:

col1, col2 = st.columns([1, 2])

with col1:
    st.image("gpt2-chatbot-launched.jpg")

with col2:
    st.markdown('<h1 style="font-family: Arial, sans-serif; color: #B22222; text-align: left;">Guvi Genius GPT🚀</h1>', unsafe_allow_html=True)

# Sql Connection:

connection = mysql.connector.connect(
    host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port = 4000,
    user = ".....................",
    password = "..................")

mycursor = connection.cursor(buffered=True)

mycursor.execute("CREATE DATABASE IF NOT EXISTS GuviGpt")
mycursor.execute('USE GuviGpt')

mycursor.execute('''CREATE TABLE IF NOT EXISTS User_data
                    (id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        registered_date TIMESTAMP,
                        last_login TIMESTAMP)''')

def username_exists(username):
    mycursor.execute("SELECT * FROM User_data WHERE username = %s", (username,))
    return mycursor.fetchone() is not None

def email_exists(email):
    mycursor.execute("SELECT * FROM User_data WHERE email = %s", (email,))
    return mycursor.fetchone() is not None

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_user(username, password, email, registered_date):
    if username_exists(username):
        return 'username_exists'
    
    if email_exists(email):
        return 'email_exists'
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    mycursor.execute(
        "INSERT INTO User_data (username, password, email, registered_date) VALUES (%s, %s, %s, %s)",
        (username, hashed_password, email, registered_date)
    )
    connection.commit()
    return 'success'

def verify_user(username, password):
    mycursor.execute("SELECT password FROM User_data WHERE username = %s", (username,))
    record = mycursor.fetchone()
    if record and bcrypt.checkpw(password.encode('utf-8'), record[0].encode('utf-8')):
        mycursor.execute("UPDATE User_data SET last_login = %s WHERE username = %s", (datetime.datetime.now(pytz.timezone('Asia/Kolkata')), username))
        connection.commit()
        return True
    return False

def reset_password(username, new_password):
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    mycursor.execute(
        "UPDATE User_data SET password = %s WHERE username = %s",
        (hashed_password, username)
    )
    connection.commit()

# Load the fine-tuned model and tokenizer
model_name_or_path = "fine_tuned_model"
model = GPT2LMHeadModel.from_pretrained(model_name_or_path)

token_name_or_path = "fine_tuned_model" 
tokenizer = GPT2Tokenizer.from_pretrained(token_name_or_path)

# Set the pad_token to eos_token if it's not already set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Move the model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Define the text generation function
def generate_text(model, tokenizer, seed_text, max_length=100, temperature=1.0, num_return_sequences=1):
    # Tokenize the input text with padding
    inputs = tokenizer(seed_text, return_tensors='pt', padding=True, truncation=True)

    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    # Generate text
    with torch.no_grad():
        output = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=max_length,
            temperature=temperature,
            num_return_sequences=num_return_sequences,
            do_sample=True,
            top_k=50,
            top_p=0.01,
            pad_token_id=tokenizer.eos_token_id  # Ensure padding token is set to eos_token_id
        )

    # Decode the generated text
    generated_texts = []
    for i in range(num_return_sequences):
        generated_text = tokenizer.decode(output[i], skip_special_tokens=True)
        generated_texts.append(generated_text)

    return generated_texts

# Session state management
if 'sign_up_successful' not in st.session_state:
    st.session_state.sign_up_successful = False
if 'login_successful' not in st.session_state:
    st.session_state.login_successful = False
if 'reset_password' not in st.session_state:
    st.session_state.reset_password = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

# Page functions
def home_page():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        .container {
            font-family: 'Roboto', sans-serif;
            max-width: 800px;
            margin: auto;
        }
        
        .welcome-header {
            font-size: 2.5em;
            font-weight: 700;
            color: #2C3E50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #3498DB;
            padding-bottom: 10px;
        }
        
        .disclaimer {
            background-color: #1a1a1a;
            color: #ffffff;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        
        .disclaimer h2 {
            color: #3498DB;
            font-size: 1.3em;
            margin-bottom: 10px;
        }
        
        .disclaimer p {
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .highlight {
            font-weight: 700;
            color: #E74C3C;
        }
        
        .input-section {
            background-color: #1a1a1a;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            color: #ffffff;
        }
        
        .output-box {
            background-color: #1a1a1a;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
            color: #ffffff;
        }
        .stTextArea textarea {
            background-color: #2a2a2a;
            color: #ffffff;
            border: 1px solid #444;
        }
        .stTextArea textarea:focus {
            border-color: #3498DB;
        }
        .stButton > button {
            background-color: #3498DB;
            color: #ffffff;
        }
        .stButton > button:hover {
            background-color: #2980B9;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="container">', unsafe_allow_html=True)
    
    st.markdown(f'<h1 class="welcome-header">Welcome, {st.session_state.username}</h1>', unsafe_allow_html=True)

    st.markdown("""
        <div class="disclaimer">
            <h2>Important Information</h2>
            <p>This application utilizes a GPT-based model for generating responses. While we strive for accuracy, the generated content may contain errors or inaccuracies. Users are advised to independently verify any critical information.</p>
            <p class="highlight">Please note: This model is not affiliated with or endorsed by the official GUVI EdTech Company.</p>
        </div>
    """, unsafe_allow_html=True)

    seed_text = st.text_area("Enter your prompt:", height=100, help="Type your text prompt here")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        max_length = st.slider("Output Word Count", min_value=10, max_value=500, value=100, help="Adjust the length of the generated text")
    with col2:
        generate_button = st.button("Generate", key="generate_button")

    st.markdown('</div>', unsafe_allow_html=True)

    if generate_button:
        if seed_text:
            with st.spinner("Generating content..."):
                generated_texts = generate_text(model, tokenizer, seed_text, max_length, temperature=0.000001, num_return_sequences=1)
                for i, text in enumerate(generated_texts):
                    st.markdown(f'<div class="output-box"><strong>Generated Text:</strong><br>{text}</div>', unsafe_allow_html=True)
        else:
            st.warning("Please enter a prompt before generating.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Add guidelines to the sidebar
    st.sidebar.markdown('<h1 style="color: #B22222;">Guidelines for Effective Prompts</h1>', unsafe_allow_html=True)
    st.sidebar.markdown("""
        - Be specific and clear in your instructions.
        - Provide relevant context for the topic.
        - Consider the desired tone and style of the output.
        - Use descriptive language to guide the generation process.
        - Review and refine your prompt for best results.
    """)
            
def login():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
        }
        .big-font {
            font-size: 36px !important;
            font-weight: bold;
            color: #D32F2F;
            margin-bottom: 30px;
            text-align: center;
        }
        .stButton > button {
            width: 100%;
            background-color: #D32F2F;
            color: white;
            font-weight: bold;
            border: none;
            padding: 10px 0;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #B71C1C;
        }
        .stTextInput > div > div > input {
            border-radius: 5px;
            border: 2px solid #FFCDD2;
        }
        .stTextInput > div > div > input:focus {
            border-color: #D32F2F;
            box-shadow: 0 0 0 1px #D32F2F;
        }
        .link-text {
            color: #D32F2F;
            text-align: center;
            cursor: pointer;
            transition: color 0.3s ease;
        }
        .link-text:hover {
            color: #B71C1C;
            text-decoration: underline;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Login</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form(key='login_form', clear_on_submit=True):
            username = st.text_input(label='Username', placeholder='Enter Username')
            password = st.text_input(label='Password', placeholder='Enter Password', type='password')

            st.markdown("<br>", unsafe_allow_html=True)

            if st.form_submit_button('Login'):
                if not username or not password:
                    st.error("Please enter all credentials")
                elif verify_user(username, password):
                    st.success(f"Welcome, {username}!")
                    st.session_state.login_successful = True
                    st.session_state.username = username
                    st.session_state.current_page = 'home'
                    st.experimental_rerun()
                else:
                    st.error("Incorrect username or password. Please try again or sign up if you don't have an account.")

        if not st.session_state.get('login_successful', False):
            st.markdown("<br>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("<div class='link-text'>New user?</div>", unsafe_allow_html=True)
                if st.button('Sign Up'):
                    st.session_state.current_page = 'sign_up'
                    st.experimental_rerun()
            with col_b:
                st.markdown("<div class='link-text'>Forgot Password?</div>", unsafe_allow_html=True)
                if st.button('Reset Password'):
                    st.session_state.current_page = 'reset_password'
                    st.experimental_rerun()

# Sign up page
def signup():
    st.markdown("""
        <style>
        body {
            background-color: #000000;
            color: #ffffff;
        }
        .big-font {
            font-size: 36px !important;
            font-weight: bold;
            color: #D32F2F;
            margin-bottom: 30px;
            text-align: center;
        }
        .stTextInput > div > div > input {
            color: #ffffff;
            background-color: #1a1a1a;
            border: 1px solid #D32F2F;
        }
        .stTextInput > div > div > input:focus {
            border-color: #FF6347;
            box-shadow: 0 0 0 1px #FF6347;
        }
        .stButton > button {
            background-color: #D32F2F;
            color: #ffffff;
        }
        .stButton > button:hover {
            background-color: #B71C1C;
        }
        .link-text {
            color: #D32F2F;
            text-align: center;
            cursor: pointer;
        }
        .link-text:hover {
            color: #FF6347;
            text-decoration: underline;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Sign Up</p>', unsafe_allow_html=True)

    with st.form(key='signup_form', clear_on_submit=True):
        email = st.text_input(label='Email', placeholder='Enter Your Email')
        username = st.text_input(label='Username', placeholder='Enter Your Username')
        password = st.text_input(label='Password', placeholder='Enter Your Password', type='password')
        re_password = st.text_input(label='Confirm Password', placeholder='Confirm Your Password', type='password')

        if st.form_submit_button('Sign Up'):
            if not email or not username or not password or not re_password:
                st.error("Enter all the Credentials")
            elif len(password) <= 3:
                st.error("Password too short")
            elif password != re_password:
                st.error("Passwords do not match! Please Re-enter")
            else:
                result = create_user(username, password, email, datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
                if result == 'success':
                    st.success("Account created successfully!")
                    st.session_state.sign_up_successful = True  # Set sign up success state
                    st.session_state.current_page = 'login'  # Set current page to login
                    st.experimental_rerun()

    # Show link to login page if sign up was not successful
    if not st.session_state.get('sign_up_successful', False):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='link-text'>Already have an account?</div>", unsafe_allow_html=True)
        if st.button('Login'):
            st.session_state.current_page = 'login'
            st.experimental_rerun()

# Reset password page
def reset_password_page():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #000000; /* Black background */
            color: #ffffff; /* White text */
            padding: 20px; /* Padding for better appearance */
        }
        .big-font {
            font-size: 36px !important;
            font-weight: bold;
            color: #D32F2F; /* Red color */
            margin-bottom: 30px;
            text-align: center;
        }
        .stTextInput > div > div > input {
            color: #ffffff; /* White text */
            background-color: #1a1a1a; /* Dark background */
            border: 1px solid #D32F2F; /* Red border */
        }
        .stTextInput > div > div > input:focus {
            border-color: #FF6347; /* Orange border when focused */
            box-shadow: 0 0 0 1px #FF6347; /* Box shadow when focused */
        }
        .stButton > button {
            background-color: #D32F2F; /* Red button background */
            color: #ffffff; /* White text */
            width: 100%; /* Full width */
            margin-top: 10px; /* Margin for spacing */
        }
        .stButton > button:hover {
            background-color: #B71C1C; /* Darker red on hover */
        }
        .link-text {
            color: #D32F2F; /* Red link text */
            text-align: center;
            cursor: pointer;
            transition: color 0.3s ease;
        }
        .link-text:hover {
            color: #FF6347; /* Orange link text on hover */
            text-decoration: underline; /* Underline on hover */
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Reset Password</p>', unsafe_allow_html=True)

    with st.form(key='reset_password_form', clear_on_submit=True):
        username = st.text_input(label='Username', value='', placeholder='Enter your username')
        new_password = st.text_input(label='New Password', type='password', placeholder='Enter new password')
        re_password = st.text_input(label='Confirm New Password', type='password', placeholder='Confirm new password')

        if st.form_submit_button('Reset Password'):
            if not username:
                st.error("Enter your username.")
            elif not username_exists(username):
                st.error("Username not found. Enter a valid username.")
            elif not new_password or not re_password:
                st.error("Enter all the credentials.")
            elif len(new_password) <= 3:
                st.error("Password too short. Must be at least 4 characters.")
            elif new_password != re_password:
                st.error("Passwords do not match. Please re-enter.")
            else:
                reset_password(username, new_password)
                st.success("Password has been reset successfully! Please login with your new password.")
                st.session_state.current_page = 'login'
                st.experimental_rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='link-text'>Remember your password?</div>", unsafe_allow_html=True)
    if st.button('Login'):
        st.session_state.current_page = 'login'
        st.experimental_rerun()

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

if st.session_state.current_page == 'login':
    login()  # Implement your login function
elif st.session_state.current_page == 'sign_up':
    signup()  # Implement your signup function
elif st.session_state.current_page == 'reset_password':
    reset_password_page()  # Implement your reset password function
elif st.session_state.current_page == 'home':
    home_page()  # Implement your home page function
else:
    st.error("Page not found or not implemented yet.")
