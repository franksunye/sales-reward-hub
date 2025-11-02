# request_module.py
import os
import json
import requests
import datetime
from requests.exceptions import Timeout
import logging
from modules.config import METABASE_PASSWORD, METABASE_SESSION, METABASE_USERNAME
from modules.log_config import setup_logging

# 设置日志
setup_logging()

SESSION_FILE = 'metabase_session.json'
SESSION_DURATION = 14 * 24 * 60 * 60  # 14 days in seconds

def get_metabase_session():
    logging.info("Attempting to get Metabase session.")
    
    headers = {
        'Content-Type': 'application/json',
    }

    data = {"username": METABASE_USERNAME, "password": METABASE_PASSWORD}
    logging.debug(f"Sending POST request to {METABASE_SESSION} with username: {METABASE_USERNAME} and password: {METABASE_PASSWORD}")
    response = requests.post(METABASE_SESSION, headers=headers, json=data, timeout=30)
    session_id = response.json()['id']
    
    # Save session info to file
    session_info = {
        'id': session_id,
        'timestamp': datetime.datetime.now().timestamp()
    }
    logging.info(f"Saving session info to file: {SESSION_FILE}")
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_info, f)
    
    logging.info(f"Metabase session obtained with ID: {session_id}")
    return session_id

def load_session():
    logging.info("Attempting to load session from file.")
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            session_info = json.load(f)
        logging.info("Session loaded successfully.")
        return session_info
    logging.warning("No session found in file.")
    return None

def is_session_valid(session_info):
    logging.info("Checking session validity.")
    if session_info is None:
        logging.warning("Session info is None.")
        return False
    session_timestamp = session_info['timestamp']
    current_timestamp = datetime.datetime.now().timestamp()
    logging.info(f"Current timestamp: {current_timestamp}, Session timestamp: {session_timestamp}")
    return (current_timestamp - session_timestamp) < SESSION_DURATION

def get_valid_session():
    logging.info("Getting valid session.")
    session_info = load_session()
    if is_session_valid(session_info):
        logging.info("Valid session found, returning session ID.")
        return session_info['id']
    else:
        logging.info("Invalid session, getting a new one.")
        return get_metabase_session()

def _send_request_with_session(session_id, api_url):
    try:
        header = {
            'X-Metabase-Session': session_id,
            'Content-Type': 'application/json'
        }
        response = requests.post(api_url, headers=header, timeout=30)
        if response.status_code == 202:
            return response.json()
        else:
            logging.error(f"Request failed with status code {response.status_code}")
            return None
    except Timeout:
        logging.error("Request timed out")
        return None
    except Exception as e:
        logging.error(f"An error occurred: {e.__class__.__name__}: {str(e)}")
        return None

def send_request(session_id, api_url=None):
    if api_url is None:
        logging.error("API URL not provided.")
        return None
    return _send_request_with_session(session_id, api_url)

def send_request_with_managed_session(api_url=None):
    if api_url is None:
        logging.error("API URL not provided.")
        return None
    logging.debug(f"send_request_with_managed_session called at {datetime.datetime.now()}")

    session_id = get_valid_session()
    response = _send_request_with_session(session_id, api_url)

    # 如果返回None（可能是401错误），尝试重新获取session并重试一次
    if response is None:
        logging.info("First request failed, attempting to get new session and retry...")
        session_id = get_metabase_session()  # 强制获取新session
        response = _send_request_with_session(session_id, api_url)

    return response