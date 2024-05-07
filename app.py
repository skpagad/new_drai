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

s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

# Initialize session state variables
if 'action' not in st.session_state:
    st.session_state['action'] = None
if 'user_data' not in st.session_state:
    st.session_state['user_data'] = {}
if 'booking_step' not in st.session_state:
    st.session_state['booking_step'] = 0

def display_homepage_header():
    """Displays the app's logo and description in the center."""
    st.image("logo.jpeg", width=100)  # Adjust width as needed
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
    if st.button("Sign Up", key="signup"):
        if save_user(s3_client, username, password, user_type, S3_BUCKET_NAME):
            st.success(f"You're signed up successfully as a {user_type}. Please log in.")
            st.session_state['action'] = None
        else:
            st.error("Signup failed. Please try again.")

def login_page(user_type):
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login"):
        user_exists, user_data = check_user_exists(s3_client, username, user_type, S3_BUCKET_NAME)
        if user_exists and user_data['password'] == password:
            st.session_state['user_data'] = user_data
            st.session_state['action'] = 'loggedin'
            st.experimental_rerun()
        else:
            st.error("Invalid credentials or user does not exist.")

def home_page():
    display_homepage_header()  # Display logo and app description centrally on the homepage
    
    if st.session_state['user_data'].get('type') == 'Patient':
        patient_interaction()
    elif st.session_state['user_data'].get('type') == 'Doctor':
        doctor_interaction()
    
    if st.button("Logout"):
        logout()

# Implement the patient_interaction function here as described in the previous guidance
def patient_interaction():
    st.header("Book an Appointment")

    # Initialize booking steps and other variables if not present
    if 'booking_step' not in st.session_state:
        st.session_state['booking_step'] = 0
    if 'appointment_date' not in st.session_state:
        st.session_state['appointment_date'] = datetime.date.today()
    if 'appointment_time' not in st.session_state:
        st.session_state['appointment_time'] = datetime.datetime.now().time()
    if 'appointment_reason' not in st.session_state:
        st.session_state['appointment_reason'] = ''

    # Display the current step for debugging
    # st.write(f"Current booking step: {st.session_state.booking_step}")

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
            st.success("Your appointment has been booked successfully.")
            
            # Reset the booking process
            st.session_state['booking_step'] = 0
            del st.session_state['appointment_date'], st.session_state['appointment_time'], st.session_state['appointment_reason']
            # Optionally, rerun the app to refresh the state
            st.experimental_rerun()



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

if __name__ == "__main__":
    main()
