import streamlit as st
from signup import save_user, check_user_exists
import boto3
from dotenv import load_dotenv
import os
import json
import datetime
import pandas as pd

# Load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Initialize AWS S3 client
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def initialize_session_state():
    """Initialize necessary session state variables."""
    st.session_state.setdefault('action', None)
    st.session_state.setdefault('user_data', {})
    st.session_state.setdefault('booking_step', 0)

def display_homepage_header():
    """Displays the app's logo and description."""
    st.image("logo.jpeg", width=100)
    st.title("Welcome to the DoctorAI App")
    st.write("This application facilitates seamless interactions between patients and healthcare providers.")

def user_options():
    """Handle user actions for login and signup."""
    user_type = st.radio("Select User Type:", ["Patient", "Doctor"], key="user_type")
    action = st.radio("Choose an action:", ["Login", "Signup"], key="action_choice")

    if action == "Signup":
        user_signup(user_type)
    elif action == "Login":
        user_login(user_type)

def user_signup(user_type):
    """Allows new users to sign up."""
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up"):
        if save_user(s3_client, username, password, user_type, S3_BUCKET_NAME):
            st.success(f"Successfully signed up as a {user_type}. Please log in.")
        else:
            st.error("Signup failed. Please try again.")

def user_login(user_type):
    """Handles user login."""
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        user_exists, user_data = check_user_exists(s3_client, username, user_type, S3_BUCKET_NAME)
        if user_exists and user_data['password'] == password:
            st.session_state['user_data'] = user_data
            st.session_state['action'] = 'loggedin'
            st.experimental_rerun()
        else:
            st.error("Invalid credentials or user does not exist.")

def patient_interaction():
    """Manage interactions with patients."""
    st.header("Book an Appointment")
    if st.button("Start Booking Process"):
        st.session_state['booking_step'] = 1

    if st.session_state['booking_step'] == 1:
        date = st.date_input("Choose the date for your appointment:", min_value=datetime.date.today())
        if st.button("Set Date"):
            st.session_state['appointment_date'] = date
            st.session_state['booking_step'] = 2

    if st.session_state['booking_step'] == 2:
        time = st.time_input("Choose your preferred time:")
        if st.button("Set Time"):
            st.session_state['appointment_time'] = time
            st.session_state['booking_step'] = 3

    if st.session_state['booking_step'] == 3:
        reason = st.text_area("Reason for the appointment:")
        if st.button("Submit Appointment"):
            appointment_details = {
                "username": st.session_state['user_data']['username'],
                "date": st.session_state['appointment_date'].strftime("%Y-%m-%d"),
                "time": st.session_state['appointment_time'].strftime("%H:%M"),
                "reason": reason
            }
            save_appointment_to_s3(appointment_details)
            st.success("Your appointment has been booked successfully.")
            st.session_state['booking_step'] = 0

def doctor_interaction():
    """Display doctor-specific interactions."""
    st.header("Doctor Portal")
    if st.button("Fetch Appointments"):
        appointments_df = fetch_appointments_from_s3()
        if appointments_df is not None and not appointments_df.empty:
            st.table(appointments_df)
        else:
            st.write("No appointments found.")

def save_appointment_to_s3(details):
    """Save the appointment details to S3."""
    key = f"appointments/{details['username']}/{details['date']}_{details['time'].replace(':', '-')}.json"
    try:
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=json.dumps(details))
        st.success("Appointment saved successfully.")
    except Exception as e:
        st.error(f"Failed to save the appointment: {str(e)}")

def fetch_appointments_from_s3():
    """Retrieve appointments from S3."""
    try:
        prefix = "appointments/"
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        appointments = [json.loads(s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=item['Key'])['Body'].read().decode("utf-8")) for item in response.get('Contents', [])]
        return pd.DataFrame(appointments)
    except Exception as e:
        st.error(f"Failed to fetch appointments: {str(e)}")
        return pd.DataFrame()

def main():
    """Main function to control the application flow."""
    initialize_session_state()
    display_homepage_header()
    if st.session_state.get('action') == 'loggedin':
        if st.session_state['user_data'].get('type') == 'Patient':
            patient_interaction()
        elif st.session_state['user_data'].get('type') == 'Doctor':
            doctor_interaction()
    else:
        user_options()

if __name__ == "__main__":
    main()
