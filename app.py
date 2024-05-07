import streamlit as st
import random
import re
from signup import save_user, check_user_exists, verify_user_password
import boto3
from dotenv import load_dotenv
import os
import json
import datetime
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

# Initialize session state variables using a more concise method
for key in ['action', 'user_data', 'booking_step']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'booking_step' else 0

def display_homepage_header():
    """Displays the app's logo and description in the center."""
    st.image("drailogo.png", width=150)  # Adjust width as needed
    st.title("Welcome to the DoctorAI App")
    st.write("""
    This application facilitates seamless interactions between patients and healthcare providers,
    allowing for easy appointment bookings and management.
    """)

def display_user_options():
    display_homepage_header() 
    user_type = st.radio("Select User Type:", ["Patient", "Doctor"], key="user_type")
    action = st.radio("Choose an action:", ["Login", "Signup"], key="action_choice")
    
    if action == "Signup":
        signup_page(user_type)
    elif action == "Login":
        login_page(user_type)

def signup_page(user_type):
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    email = st.text_input("Email", key="signup_email")  # Collect email address from user
    if st.button("Sign Up", key="signup"):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):  # Simple email validation
            st.error("Invalid email format.")
        else:
            success, message = save_user(s3_client, username, password, user_type, email, S3_BUCKET_NAME)
            if success:
                st.success(f"You're signed up successfully as a {user_type}. Please log in.")
                st.session_state['action'] = None
            else:
                st.error(f"Signup failed: {message}")

def generate_mfa_code():
    return str(random.randint(100000, 999999))

def send_email(recipient_email, subject, body):
    sender_email = "doctorai2k24@gmail.com"
    sender_password = "isgw bjbh gzvr lgfz"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        print("Email sent successfully")
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")


def login_page(user_type):
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    # if st.button("Login", key="login"):
    #     user_exists, user_data = check_user_exists(s3_client, username, user_type, S3_BUCKET_NAME)
    #     if user_exists and verify_user_password(user_data['password'], password):
    #         if 'mfa_code' not in st.session_state or st.session_state['mfa_code'] is None:
    #             st.session_state['mfa_code'] = generate_mfa_code()
    #             print("current st.session_state['mfa_code'] = generate_mfa_code()",st.session_state['mfa_code'])
    #             send_email(user_data['email'], "Your Verification Code", f"Your code is: {st.session_state['mfa_code']}")

    #         code_input = st.text_input("Enter your MFA code:", type="password", key="mfa_code_input")
    #         print("session state prompts for mfa",st.session_state)
    #         if st.button("Verify MFA Code", key="verify_mfa"):
    #             print("verify for mfa session")
    #             if code_input == st.session_state['mfa_code']:
    #                 print("session state",user_data,user_type)
    #                 st.session_state['user_data'] = user_data
    #                 st.session_state['action'] = 'loggedin'
    #                 st.session_state['user_type'] = user_type
    #                 print("User Type in session state:", st.session_state.get('user_type'))
    #                 st.success("Login successful, loading your dashboard...")
    #                 del st.session_state['mfa_code']  # Clear the MFA code from session state
    #                 st.experimental_rerun()  # Forces a rerun of the application
    #             else:
    #                 st.error("Invalid MFA code.")
    #     else:
    #         st.error("Invalid credentials or user does not exist.")

    if st.button("Verify User", key="login"):
        user_exists, user_data = check_user_exists(s3_client, username, user_type, S3_BUCKET_NAME)
        if user_exists and verify_user_password(user_data['password'], password):
            mfa_code = st.text_input("enter your MFA", type="password", key="mfa_code_input")
            
            st.session_state['user_data'] = user_data
            
            print("before login with mfa session state prompts for mfa",st.session_state,mfa_code)
            if st.button("login with mfa"):
                print("after login with mfa session state prompts for mfa",st.session_state,mfa_code)
                st.session_state['mfa_code_input']=mfa_code
                if mfa_code:
                    print("verified mfa")
                    print("session state",user_data,user_type)
                    st.session_state['user_type'] = user_type
                    st.session_state['action'] = 'loggedin'
                    
                    print("User Type in session state:", st.session_state.get('user_type'))
                    st.success("Login successful, loading your dashboard...")
                    st.experimental_rerun()  # Forces a rerun of the application
            # if 'mfa_code' not in st.session_state or st.session_state['mfa_code'] is None:
            #     st.session_state['mfa_code'] = generate_mfa_code()
            #     print("current st.session_state['mfa_code'] = generate_mfa_code()",st.session_state['mfa_code'])
            #     send_email(user_data['email'], "Your Verification Code", f"Your code is: {st.session_state['mfa_code']}")

        else:
            st.error("Invalid credentials or user does not exist.")


# Implement the patient_interaction function here as described in the previous guidance
def patient_interaction():
    st.header("Book an Appointment")

    # Check if the booking has been completed and hide further steps if so
    if 'booking_completed' in st.session_state and st.session_state['booking_completed']:
        st.success("Your appointment has been booked successfully.")
        st.session_state['booking_completed'] = False 
    else:
        # Initialize booking steps and other variables if not present
        if 'booking_step' not in st.session_state:
            st.session_state['booking_step'] = 0
        if 'appointment_date' not in st.session_state:
            st.session_state['appointment_date'] = datetime.date.today()
        if 'appointment_time' not in st.session_state:
            st.session_state['appointment_time'] = datetime.datetime.now().time()
        if 'appointment_reason' not in st.session_state:
            st.session_state['appointment_reason'] = ''

        if st.session_state.booking_step == 0:
            if st.button("Start Booking Process"):
                st.session_state.booking_step = 1

        if st.session_state.booking_step == 1:
            st.session_state['appointment_date'] = st.date_input("Choose the date for your appointment:", key="date", min_value=datetime.date.today())
            if st.button("Set Date", key="set_date"):
                st.session_state.booking_step = 2

        if st.session_state.booking_step == 2:
            st.session_state['appointment_time'] = st.time_input("Choose your preferred time:", key="time")
            if st.button("Set Time", key="set_time"):
                st.session_state.booking_step = 3

        if st.session_state.booking_step == 3:
            st.session_state['appointment_reason'] = st.text_area("Reason for the appointment:", key="reason")
            if st.button("Submit Appointment", key="submit_appointment"):
                # Gather the appointment details
                appointment_details = {
                    "username": st.session_state['user_data']['username'],
                    "date": st.session_state['appointment_date'].strftime("%Y-%m-%d"),
                    "time": st.session_state['appointment_time'].strftime("%H:%M"),
                    "reason": st.session_state['appointment_reason']
                }
                # Call the function to save the appointment details to S3
                save_appointment_to_s3(appointment_details)
                
                # Set the booking completed flag
                st.session_state['booking_completed'] = True
                st.success("Your appointment has been booked successfully.")
                
                # Reset the booking process
                st.session_state['booking_step'] = 0
                del st.session_state['appointment_date'], st.session_state['appointment_time'], st.session_state['appointment_reason']
                # Optionally, rerun the app to refresh the state
                st.experimental_rerun()
    if st.button("View My Appointments"):
        appointments_df = fetch_patient_appointments_from_s3()
        if not appointments_df.empty:
            st.write("Here are your upcoming appointments:")
            st.table(appointments_df)
        else:
            st.write("You have no upcoming appointments.")



# Implement the doctor_interaction function here as described in the previous guidance
def doctor_interaction():
    st.header("Doctor Portal")
    if st.button("Fetch Appointments"):
        appointments_df = fetch_appointments_from_s3()
        if appointments_df is not None and not appointments_df.empty:
            st.table(appointments_df)
        else:
            st.write("No appointments found.")

# Implement the save_appointment_to_s3 function here as described in the previous guidance
def save_appointment_to_s3(details):
    appointment_key = f"appointments/{details['username']}/{details['date']}_{details['time'].replace(':', '-')}.json"
    try:
        appointment_json = json.dumps(details)
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=appointment_key, Body=appointment_json)
        st.success("Appointment booked successfully.")
    except Exception as e:
        st.error(f"Failed to save the appointment: {str(e)}")

# Implement the fetch_appointments_from_s3 function here as described in the previous guidance
def fetch_appointments_from_s3():
    doctor_username = st.session_state['user_data'].get('username')
    prefix = f"appointments/"
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        appointments = [json.loads(s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=item['Key'])['Body'].read().decode("utf-8")) for item in response.get('Contents', [])]
        return pd.DataFrame(appointments)
    except Exception as e:
        st.error(f"Failed to fetch appointments: {str(e)}")
        return pd.DataFrame()

def fetch_patient_appointments_from_s3():
    username = st.session_state['user_data']['username']
    prefix = f"appointments/{username}/"
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if 'Contents' in response:
            appointments = [json.loads(s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=item['Key'])['Body'].read().decode("utf-8")) for item in response['Contents']]
            return pd.DataFrame(appointments)
        else:
            return pd.DataFrame()  # Return an empty DataFrame if no appointments
    except Exception as e:
        st.error(f"Failed to fetch appointments: {str(e)}")
        return pd.DataFrame()

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state['action'] = None
    st.experimental_rerun()

def main():
    if st.session_state.get('action') == 'loggedin':
        home_page()
    else:
        display_user_options()


main()

def home_page():
    print("User Type in session state:", st.session_state.get('user_type'))
    display_homepage_header()  # Always show the header
    user_type = st.session_state.get('user_type')  # Fetch the user type from session state
    if user_type == 'Patient':
        patient_interaction()
    elif user_type == 'Doctor':
        doctor_interaction()
    if st.button("Logout"):
        logout()

def load_css():
    try:
        with open('styles.css', 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("CSS file not found.")
load_css()
