
# DoctorAI Project

DoctorAI is a web application designed to facilitate interactions between patients and healthcare providers. Using AWS S3 for data storage and Streamlit for the user interface, this application simplifies the process of managing appointments.

## Initial Setup

### Step 1: AWS S3 Bucket Setup

- Create an AWS S3 bucket to store all data such as signup, login, and appointment details.
- Ensure the bucket has the appropriate permissions to allow the application to read and write data.

### Step 2: Secure AWS Credentials

- Store your AWS credentials (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`) and your S3 bucket name in a `.env` file to keep them secure.
- Utilize `python-dotenv` to load these credentials within your application.

## Installation

### Prerequisites

- Python 3.6 or higher
- pip

### Dependencies

Install the required packages using pip:

```bash
pip install streamlit boto3 python-dotenv pandas




