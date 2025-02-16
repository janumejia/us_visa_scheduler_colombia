"""Module for handling visa-related operations and configurations."""

import configparser
import json
import locale
import platform
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
from gtts import gTTS  # To Google voice
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from webdriver_manager.chrome import ChromeDriverManager

from embassy import embassies

config = configparser.ConfigParser()
config.read("config.ini")

# PERSONAL INFORMATION:
# Account and current appointment info from https://ais.usvisa-info.com
USERNAME = config["PERSONAL_INFO"]["USERNAME"]
PASSWORD = config["PERSONAL_INFO"]["PASSWORD"]
# Find SCHEDULE_ID in re-schedule page link:
# https://ais.usvisa-info.com/en-am/niv/schedule/{SCHEDULE_ID}/appointment
SCHEDULE_ID = config["PERSONAL_INFO"]["SCHEDULE_ID"]
# Target Period:
PRIOD_START = config["PERSONAL_INFO"]["PRIOD_START"]
PRIOD_END = config["PERSONAL_INFO"]["PRIOD_END"]
# Embassy Section:
YOUR_EMBASSY = config["PERSONAL_INFO"].get("YOUR_EMBASSY", "es-co-bog")
EMBASSY = embassies[YOUR_EMBASSY][0]
FACILITY_ID = embassies[YOUR_EMBASSY][1]
CAS_FACILITY_ID = embassies[YOUR_EMBASSY][2]
REGEX_CONTINUE = embassies[YOUR_EMBASSY][3]
REGEX_WRONG_CREDENTIALS = embassies[YOUR_EMBASSY][4]

# NOTIFICATION:
# Get email notifications via https://sendgrid.com/ (Optional)
SENDGRID_API_KEY = config["NOTIFICATION"].get("SENDGRID_API_KEY", None)
# Get push notifications via https://pushover.net/ (Optional)
PUSHOVER_TOKEN = config["NOTIFICATION"].get("PUSHOVER_TOKEN", None)
PUSHOVER_USER = config["NOTIFICATION"].get("PUSHOVER_USER", None)
# Get push notifications via PERSONAL WEBSITE http://yoursite.com (Optional)
PERSONAL_SITE_USER = config["NOTIFICATION"].get("PERSONAL_SITE_USER", None)
PERSONAL_SITE_PASS = config["NOTIFICATION"].get("PERSONAL_SITE_PASS", None)
PUSH_TARGET_EMAIL = config["NOTIFICATION"].get("PUSH_TARGET_EMAIL", None)
PERSONAL_PUSHER_URL = config["NOTIFICATION"].get("PERSONAL_PUSHER_URL", None)

# TIME SECTION:
MINUTE = 60
HOUR = 60 * MINUTE
# Time between steps (interactions with forms)
STEP_TIME = 0.5
# Time between retries/checks for available dates (seconds)
RETRY_TIME_L_BOUND = config["TIME"].getfloat("RETRY_TIME_L_BOUND")
RETRY_TIME_U_BOUND = config["TIME"].getfloat("RETRY_TIME_U_BOUND")
# Cooling down after WORK_LIMIT_TIME hours of work (Avoiding Ban)
WORK_LIMIT_TIME = config["TIME"].getfloat("WORK_LIMIT_TIME")
WORK_COOLDOWN_TIME = config["TIME"].getfloat("WORK_COOLDOWN_TIME")
# Temporary Banned (empty list): wait COOLDOWN_TIME hours
BAN_COOLDOWN_TIME = config["TIME"].getfloat("BAN_COOLDOWN_TIME")

# CHROME DRIVER:
# Details for the script to control Chrome
LOCAL_USE = config["CHROMEDRIVER"].getboolean("LOCAL_USE")
# Optional: HUB_ADDRESS is mandatory only when LOCAL_USE = False
HUB_ADDRESS = config["CHROMEDRIVER"].get("HUB_ADDRESS", None)

# URLS:
SIGN_IN_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/users/sign_in"
APPOINTMENT_URL = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment"
DATE_URL = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment/days/{FACILITY_ID}.json?appointments[expedite]=false"
TIME_URL = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment/times/{FACILITY_ID}.json?date=%s&appointments[expedite]=false"
SIGN_OUT_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/users/sign_out"
CAS_DATE_URL = (
    f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment/days/{CAS_FACILITY_ID}.json?&consulate_id={FACILITY_ID}"
    "&consulate_date=%s&consulate_time=%s&appointments[expedite]=false"
)
CAS_TIME_URL = (
    f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment/times/{CAS_FACILITY_ID}.json?"
    "date=%s"
    f"&consulate_id={FACILITY_ID}&"
    "consulate_date=%s&consulate_time=%s&appointments[expedite]=false"
)

JS_SCRIPT = (
    "var req = new XMLHttpRequest();"
    "req.open('GET', '%s', false);"
    "req.setRequestHeader('Accept', 'application/json, text/javascript, */*; q=0.01');"
    "req.setRequestHeader('X-Requested-With', 'XMLHttpRequest');"
    "req.setRequestHeader('Cookie', '_yatri_session=%s');"
    "req.send(null);"
    "return req.responseText;"
)

# Log File for current date
LOG_FILE_NAME = "logs/" + "log_" + str(datetime.now().date()) + ".log"

# Audio file name for Google Text-to-Speech
AUDIO_FILENAME = "google_voice.mp3"

# Attempts to connect to the server
REQUEST_ATTEMPTS = 5

# Timeout requests
TIMEOUT_REQUEST = 10

# Success messages patterns to check if the appointment was scheduled
SUCCESS_PATTERNS = [
    "Successfully Scheduled",
    "Usted ha programado exitosamente su cita de visa",
]

# Variable to store the chrome driver instance
DRIVER = None


def set_spanish_locale() -> None:
    """Set the locale to Spanish to convert dates to Spanish format."""
    try:
        locale.setlocale(locale.LC_TIME, "es_ES")  # Linux/macOS
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "Spanish_Spain")  # Windows
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, "Spanish_Spain.1252")  # Another variant in Windows
            except locale.Error:
                print(
                    "No se pudo establecer el idioma español. Se usará el predeterminado.",
                )


def send_notification(title: str, msg: str) -> None:
    """Send notification using various methods based on available configurations.

    Args:
        title (str): The title of the notification.
        msg (str): The message content of the notification.

    Returns:
        None

    """
    if SENDGRID_API_KEY:
        message = Mail(from_email=USERNAME, to_emails=USERNAME, subject=msg, html_content=msg)
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)

        except Exception as e:
            print(e.message)

    if PUSHOVER_TOKEN:
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": msg,
        }
        requests.post(url, data, timeout=TIMEOUT_REQUEST)
    if PERSONAL_SITE_USER:
        url = PERSONAL_PUSHER_URL
        data = {
            "title": "VISA - " + str(title),
            "user": PERSONAL_SITE_USER,
            "pass": PERSONAL_SITE_PASS,
            "email": PUSH_TARGET_EMAIL,
            "msg": msg,
        }
        requests.post(url, data, timeout=TIMEOUT_REQUEST)


def auto_action(  # noqa: PLR0913
    label: str,
    find_by: str,
    element_type: str,
    action: str,
    value: str,
    sleep_time: float = 0,
) -> None:
    """Perform an automated action on a web element.

    Args:
        label (str): Label for the action being performed.
        find_by (str): Method to find the element (id, name, class, xpath).
        element_type (str): Identifier for the element.
        action (str): Action to perform (send, click).
        value (str): Value to send if action is "send".
        sleep_time (float, optional): Time to sleep after action. Defaults to 0.

    Returns:
        None

    """
    print("\t" + label + ":", end="")

    # Find Element By
    match find_by.lower():
        case "id":
            item = DRIVER.find_element(By.ID, element_type)
        case "name":
            item = DRIVER.find_element(By.NAME, element_type)
        case "class":
            item = DRIVER.find_element(By.CLASS_NAME, element_type)
        case "xpath":
            item = DRIVER.find_element(By.XPATH, element_type)
        case _:
            return

    # Do Action:
    match action.lower():
        case "send":
            item.send_keys(value)
        case "click":
            item.click()
        case _:
            return

    print("\t\tCheck!")
    if sleep_time:
        time.sleep(sleep_time)


def create_logging_file_path_if_does_not_exist() -> None:
    """Create the directory path for the logging file if it doesn't exist.

    Returns:
        None

    """
    try:
        directory = Path(LOG_FILE_NAME).parent  # Create the directory path if it doesn't exist
        if directory != Path():  # Avoid unnecessary mkdir for the current directory
            directory.mkdir(parents=True, exist_ok=True)

    except PermissionError:
        print("Permission denied while creating logging directory: %s", directory)
    except OSError as e:
        print("Failed to create logging directory: %s - Error: %s", directory, e)
    except Exception as e:
        print("An error occurred while creating logging directory: %s", e)


def start_login_process() -> bool:
    """Initiate the login process, attempting to bypass reCAPTCHA and log in to the system.

    This function creates a logging file path if it doesn't exist, then attempts to log in
    up to LOGIN_ATTEMPTS times. It performs various actions such as entering credentials, accepting
    privacy terms, and navigating through the login process. If successful, it prints a
    success message. If it fails, it logs the error and retries.

    Returns:
        bool: True if login is successful, False otherwise.

    """
    create_logging_file_path_if_does_not_exist()

    attempts = 0
    while attempts < REQUEST_ATTEMPTS:
        try:
            attempts += 1
            DRIVER.get(SIGN_IN_LINK)
            time.sleep(STEP_TIME)
            WebDriverWait(DRIVER, 30).until(
                expected_conditions.presence_of_element_located((By.NAME, "commit")),
            )
            auto_action(
                "Click bounce",
                "xpath",
                '//a[@class="down-arrow bounce"]',
                "click",
                "",
                STEP_TIME,
            )
            auto_action("Email", "id", "user_email", "send", USERNAME, STEP_TIME)
            auto_action("Password", "id", "user_password", "send", PASSWORD, STEP_TIME)
            auto_action("Privacy", "class", "icheckbox", "click", "", STEP_TIME)
            auto_action("Enter Panel", "name", "commit", "click", "", STEP_TIME)
            time.sleep(STEP_TIME)
            WebDriverWait(DRIVER, 30).until(
                lambda driver: (
                    driver.find_elements(By.XPATH, f"//a[contains(text(), '{REGEX_CONTINUE}')]")
                    or driver.find_elements(
                        By.XPATH,
                        f"//*[contains(text(), '{REGEX_WRONG_CREDENTIALS}')]",
                    )
                ),
            )
            # Verificar si apareció el mensaje de error
            if DRIVER.find_elements(
                By.XPATH,
                f"//*[contains(text(), '{REGEX_WRONG_CREDENTIALS}')]",
            ):
                _handle_notification(
                    "EXCEPTION",
                    "Credenciales incorrectas. Por favor corregirlas e intentar nuevamente.",
                )
                return False

            print("\n\tLogin successful!\n")
            return True

        except Exception as e:
            msg = f"login failed! Error: {e}\n"
            print(msg)
            info_logger(msg)
            time.sleep(STEP_TIME)

    return False


def identify_os_and_play_audio() -> None:
    """Detect the user's operating system and plays an audio file using the appropriate command.

    Returns:
        None

    """
    # Detects the user's operating system
    operativo_system = platform.system()

    if operativo_system == "Darwin":  # macOS
        subprocess.run(["afplay", AUDIO_FILENAME], check=True)  # noqa: S603, S607
    elif operativo_system == "Linux":
        subprocess.run(  # noqa: S603
            ["mpg123", AUDIO_FILENAME],  # noqa: S607
            check=True,
        )
    elif operativo_system == "Windows":
        subprocess.run(  # noqa: S603
            ["cmd", "/c", "start", AUDIO_FILENAME],  # noqa: S607
            check=True,
        )
    else:
        print(f"No se pudo reproducir el audio en el SO: {operativo_system}")


def str_to_google_voice(message: str) -> None:
    """Convert a string to a Google voice message.

    Args:
        message (str): Text to convert to voice.

    Returns:
        None

    """
    # Create a gTTS object with the message and set the language to Spanish
    tts = gTTS(text=message, lang="es")

    # Save the audio and play it
    tts.save(AUDIO_FILENAME)
    identify_os_and_play_audio()


def get_cas_date(consulate_date: str, consulate_time: str) -> str | bool:
    """Attempt to retrieve a CAS date based on the provided consulate date and time.

    Args:
        consulate_date (str): The date of the consulate appointment.
        consulate_time (str): The time of the consulate appointment.

    Returns:
        str | bool: The selected CAS date if available, or False if no date could be retrieved.

    """
    cas_date_url = CAS_DATE_URL % (consulate_date, consulate_time)
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            print(f"Attempt {attempt} of {REQUEST_ATTEMPTS} to get CAS date")
            session = DRIVER.get_cookie("_yatri_session")["value"]
            script = JS_SCRIPT % (str(cas_date_url), session)
            content = DRIVER.execute_script(script)
            json_data = json.loads(content)
            dates = [item["date"] for item in json_data if item.get("business_day")]
            if dates:
                print("CAS Available Dates:", ", ".join(dates))
                cas_date = dates[-1]
                print("Selected CAS Date:", cas_date)
                return cas_date
            print("No available CAS dates found.")

        except Exception as e:
            msg = (
                f"Error to get cas date for consulate_date={consulate_date} and "
                f"consulate_time={consulate_time} in method get_cas_date(). Error: {e}"
            )
            print(msg)
            info_logger(msg)

        print("Retrying...")
        time.sleep(STEP_TIME)

    return False


def closest_time_to_desired_time(
    available_hours: list,
    desired_time: str = "10:00",
) -> str:
    """Given a list of available hours return the closest time to the desired time.

    Args:
        available_hours (list): List of available hours.
        desired_time (str): The desired time to compare against.

    Returns:
        str: The closest time to the desired time.

    """
    # Convert the desired time to a datetime object
    target = datetime.strptime(desired_time, "%H:%M")

    # Convert each hour to a datetime object and find the closest one
    return min(
        available_hours,
        key=lambda t: abs(datetime.strptime(t, "%H:%M") - target),
    )


def get_cas_time(consulate_date: str, consulate_time: str, cas_date: str) -> str | bool:
    """Get the CAS time for the given consulate date, time, and CAS date.

    Args:
        consulate_date (str): The consulate appointment date.
        consulate_time (str): The consulate appointment time.
        cas_date (str): The CAS date.

    Returns:
        str | bool: The closest available CAS time if found, False otherwise.

    """
    cas_time_url = CAS_TIME_URL % (cas_date, consulate_date, consulate_time)
    print(f"CAS_TIME_URL: {cas_time_url}")
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            print(f"Attempt {attempt} of {REQUEST_ATTEMPTS} to get CAS time")
            session = DRIVER.get_cookie("_yatri_session")["value"]
            script = JS_SCRIPT % (str(cas_time_url), session)
            content = DRIVER.execute_script(script)
            json_data = json.loads(content)
            available_times = json_data.get("available_times")
            if available_times:
                print("CAS Available Times:", ", ".join(available_times))
                closest_time = closest_time_to_desired_time(available_times)
                print("Selected CAS Time:", closest_time)
                return closest_time
            print("No available CAS times found.")

        except Exception as e:
            msg = (
                f"Error to get cas time for cas_date={cas_date}, consulate_date={consulate_date}, "
                f"consulate_time={consulate_time} in method get_cas_date(). Error: {e}"
            )
            print(msg)
            info_logger(msg)

        print("Retrying...")
        time.sleep(STEP_TIME)

    return False


def _handle_notification(msg_title: str, msg: str) -> None:
    print(msg)
    info_logger(msg)
    str_to_google_voice(msg)
    send_notification(msg_title, msg)


def reschedule(date: str) -> bool:
    """Reschedule a consulate appointment for the given date.

    Args:
        date (str): The date to reschedule the appointment for.

    Returns:
        bool: True if the appointment was successfully rescheduled, False otherwise.

    """
    DRIVER.get(APPOINTMENT_URL)

    time = get_consulate_appointment_time(date)
    if not time:
        _handle_notification("EXCEPTION", "Error al obtener hora para reagendar cita")
        return False

    cas_date = get_cas_date(date, time)
    if not cas_date:
        _handle_notification("EXCEPTION", "Error al obtener fecha CAS para reagendar cita")
        return False

    cas_time = get_cas_time(date, time, cas_date)
    if not cas_time:
        _handle_notification("EXCEPTION", "Error al obtener hora CAS para reagendar cita")
        return False

    headers = {
        "User-Agent": DRIVER.execute_script("return navigator.userAgent;"),
        "Referer": APPOINTMENT_URL,
        "Cookie": "_yatri_session=" + DRIVER.get_cookie("_yatri_session")["value"],
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "authenticity_token": DRIVER.find_element(
            by=By.NAME,
            value="authenticity_token",
        ).get_attribute("value"),
        "confirmed_limit_message": DRIVER.find_element(
            by=By.NAME,
            value="confirmed_limit_message",
        ).get_attribute("value"),
        "use_consulate_appointment_capacity": DRIVER.find_element(
            by=By.NAME,
            value="use_consulate_appointment_capacity",
        ).get_attribute("value"),
        "appointments[consulate_appointment][facility_id]": FACILITY_ID,
        "appointments[consulate_appointment][date]": date,
        "appointments[consulate_appointment][time]": time,
        "appointments[asc_appointment][facility_id]": CAS_FACILITY_ID,
        "appointments[asc_appointment][date]": cas_date,
        "appointments[asc_appointment][time]": cas_time,
    }

    data_converted_to_urlencoded = urlencode(data, doseq=True)

    log_message = (
        f"\nRequest to Reschedule:\nURL: {APPOINTMENT_URL}\n\n"
        f"Headers:\n{json.dumps(headers, indent=4)}\n\n"
        f"Data:\n{data}\n\n"
        f"Data in URL Encode:\n{data_converted_to_urlencoded}\n"
    )
    info_logger(log_message)

    # Request to reschedule
    r = requests.post(
        APPOINTMENT_URL,
        headers=headers,
        data=data_converted_to_urlencoded,
        timeout=TIMEOUT_REQUEST,
    )
    response_log = f"Response Status Code: {r.status_code}\nResponse Content: {r.text}\n\n"
    print(response_log)
    info_logger(response_log)

    # Appointment in in readable date format
    appointment_readable_date = (
        datetime.strptime(date, "%Y-%m-%d").strftime("%d de %B de %Y").lstrip("0")
    )

    # CAS in readable date format
    cas_readable_date = (
        datetime.strptime(cas_date, "%Y-%m-%d").strftime("%d de %B de %Y").lstrip("0")
    )

    # Check if the appointment was successfully rescheduled
    if any(substring in r.text for substring in SUCCESS_PATTERNS):
        msg = (
            f"¡Cita reagendada para el {appointment_readable_date} a las {time} y "
            f"cita CAS para el {cas_readable_date} a las {cas_time}!"
        )
        _handle_notification("SUCCESS", msg)
        return True

    # If the appointment was not successfully rescheduled, log the error message
    _handle_notification(
        "EXCEPTION",
        f"No se pudo reagendar la cita para la fecha {appointment_readable_date} a las {time}",
    )
    return False


def get_consulate_appointment_date() -> dict | bool:
    """Retrieve the available dates for consulate appointments.

    Returns:
        dict | bool: A dictionary containing the available dates or False if an error occurs.

    """
    try:
        # Requesting to get the whole available dates
        session = DRIVER.get_cookie("_yatri_session")["value"]
        script = JS_SCRIPT % (str(DATE_URL), session)
        content = DRIVER.execute_script(script)
        return json.loads(content)

    except Exception as e:
        print(e)
        return False


def get_consulate_appointment_time(date_visa: str) -> str | bool:
    """Attempt to retrieve the consulate appointment time for a given date.

    Args:
        date_visa (str): The date for which to retrieve the appointment time.

    Returns:
        str | bool: The closest available time to the desired time if successful, False otherwise.

    """
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            print(f"Attempt {attempt} of {REQUEST_ATTEMPTS} to get time")
            time_url = TIME_URL % date_visa
            session = DRIVER.get_cookie("_yatri_session")["value"]
            script = JS_SCRIPT % (str(time_url), session)
            content = DRIVER.execute_script(script)
            data = json.loads(content)
            available_times = data.get("available_times")
            print("Available Times:", ", ".join(available_times))
            time_available = closest_time_to_desired_time(available_times)
            print(f"Got date and time successfully! {date_visa} - {time_available}")
            return time_available

        except Exception as e:
            msg = f"Error to get time in {date_visa} in method get_time(). Error: {e}"
            print(msg)
            info_logger(msg)

        print("Retrying...")
        time.sleep(STEP_TIME)

    return False


def _is_in_period(date: str, priod_start_date_obj: datetime, priod_end_date_obj: datetime) -> bool:
    new_date = datetime.strptime(date, "%Y-%m-%d")
    return new_date <= priod_end_date_obj and new_date >= priod_start_date_obj


def get_available_date(dates: list) -> str | None:
    """Evaluate different available dates and return the first date within the specified period.

    Args:
        dates (list): A list of dictionaries containing date information.

    Returns:
        str | None: The first available date within the period, or None if no date is found.

    """
    priod_start_date_obj = datetime.strptime(PRIOD_START, "%Y-%m-%d")
    priod_end_date_obj = datetime.strptime(PRIOD_END, "%Y-%m-%d")
    for d in dates:
        date = d.get("date")
        if _is_in_period(date, priod_start_date_obj, priod_end_date_obj):
            print(f"Date found: {date}")
            return date
    print(
        f"\n\nNo available dates between ({priod_start_date_obj.date()}) and "
        f"({priod_end_date_obj.date()})!",
    )
    return None


def info_logger(log_msg: str) -> None:
    """Log information to logging file with timestamp.

    Args:
        log_msg (str): The message to be logged.

    Returns:
        None

    """
    with Path(LOG_FILE_NAME).open("a") as file:
        file.write(str(datetime.now().time()) + ":\n" + log_msg + "\n")


def setup_chrome_driver() -> webdriver.Chrome | webdriver.Remote | None:
    """Set up the Chrome driver.

    Returns:
        webdriver.Chrome | webdriver.Remote | None: The Chrome driver instance or None if an error.

    """
    driver = None
    try:
        if LOCAL_USE:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            # driver = webdriver.Chrome(service=Service(executable_path='~/.wdm/drivers/chromedriver/mac64/129.0.6668.70/chromedriver-mac-arm64/chromedriver'))
        elif HUB_ADDRESS:
            driver = webdriver.Remote(
                command_executor=HUB_ADDRESS,
                options=webdriver.ChromeOptions(),
            )

    except Exception as e:
        # Exception Occurred
        msg = f"Exception in webdriver.Chrome!\n{e}"
        print(msg)
        info_logger(msg)
        str_to_google_voice("Falló la carga del Web Driver de Google Chrome")
        send_notification("EXCEPTION", msg)

    else:
        return driver


def start_visa_process() -> None:
    """Start the main process to schedule a visa appointment."""
    first_loop = True
    total_time, req_count = 0, 0

    while True:
        if first_loop:
            if DRIVER is None:
                break
            t0 = time.time()
            total_time = 0
            req_count = 0
            if not start_login_process():
                break
            first_loop = False

        req_count += 1
        try:
            log_request_status(req_count)

            dates = get_consulate_appointment_date()
            if not dates:
                handle_ban_situation()
                first_loop = True
                continue

            log_available_dates(dates)
            date = get_available_date(dates)
            if date and reschedule(date):
                break

            total_time = time.time() - t0
            if handle_break_time(total_time, req_count):
                first_loop = True
                continue

            handle_retry_wait()

        except Exception as e:
            handle_exception(e)
            break


def log_request_status(req_count: int) -> None:
    """Log the request count and timestamp.

    Args:
        req_count (int): The request count.

    """
    msg = f"{'-' * 60}\nRequest count: {req_count}, Log time: {datetime.today()}\n"
    print(msg)
    info_logger(msg)


def handle_ban_situation() -> None:
    """Handle ban scenario by logging out and waiting for cooldown time."""
    msg = f"List is empty, Probably banned!\n\tSleep for {BAN_COOLDOWN_TIME} hours!\n"
    print(msg)
    info_logger(msg)
    send_notification("BAN", msg)
    DRIVER.get(SIGN_OUT_LINK)
    time.sleep(BAN_COOLDOWN_TIME * HOUR)


def log_available_dates(dates: list) -> None:
    """Log available appointment dates.

    Args:
        dates (list): A list of dictionaries containing date information.

    """
    msg = "Available dates:\n" + ", ".join(d.get("date") for d in dates)
    print(msg)
    info_logger(msg)


def handle_break_time(total_time: float, req_count: int) -> bool:
    """Handle cooldown period if working time exceeds the limit."""
    msg = f"\nWorking Time: ~ {total_time / MINUTE:.2f} minutes"
    print(msg)
    info_logger(msg)

    if total_time > WORK_LIMIT_TIME * HOUR:
        msg = f"Break-time after {WORK_LIMIT_TIME} hours | Repeated {req_count} times"
        print(msg)
        info_logger(msg)
        send_notification("REST", msg)
        DRIVER.get(SIGN_OUT_LINK)
        time.sleep(WORK_COOLDOWN_TIME * HOUR)
        return True  # Restart process after cooldown
    return False


def handle_retry_wait() -> None:
    """Wait a random retry time before the next attempt."""
    retry_wait_time = random.randint(RETRY_TIME_L_BOUND, RETRY_TIME_U_BOUND)  # noqa: S311
    msg = f"Retry Wait Time: {retry_wait_time} seconds"
    print(msg)
    info_logger(msg)
    time.sleep(retry_wait_time)


def handle_exception(e: Exception) -> None:
    """Log and handles exceptions by breaking the loop."""
    msg = f"Break the loop after exception!\n{e}"
    print(msg)
    info_logger(msg)
    str_to_google_voice("Falló la ejecución")


if __name__ == "__main__":
    set_spanish_locale()
    DRIVER = setup_chrome_driver()
    if DRIVER is not None:
        start_visa_process()
