import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ACCOUNT_EMAIL = "bob@test.com"  # The email you registered with
ACCOUNT_PASSWORD = "ReallyGoodPassword"  # The password you used during registration
GYM_URL = "https://appbrewery.github.io/gym/"

chrome_options = webdriver.ChromeOptions()
# Keep the browser open if the script finishes or crashes.
# If True, you need to *manually* QUIT Chrome before you re-run the script.
chrome_options.add_experimental_option("detach", True)
# Create a folder for the Chrome Profile Selenium will use every time
user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
# include double -- for command line argument to Chrome
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
driver = webdriver.Chrome(options=chrome_options)
driver.get(GYM_URL)

# ---------------- Automated Login ----------------
def login():
    login_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "login-button"))
    )
    login_button.click()

    email_input = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "email-input"))
    )
    email_input.send_keys(ACCOUNT_EMAIL)

    password_input = driver.find_element(By.ID, "password-input")
    password_input.send_keys(ACCOUNT_PASSWORD)

    submit_button = driver.find_element(By.ID, "submit-button")
    submit_button.click()


@retry(
    stop=stop_after_attempt(17),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(TimeoutException),
    reraise=True
)
def retry_login():
    login()
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "Schedule_scheduleTitle__zfZxg")
        )
    )

    print("Logged in")


try:
    retry_login()
except TimeoutException:
    print("Login failed after retries.")

class_cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='class-card-']")
bookings_made = 0
waitlists_joined = 0
already_booked = 0
processed_classes = []
attempted_bookings = []
for card in class_cards:
    day_group = card.find_element(By.XPATH, "./ancestor::div[contains(@id, 'day-group-')]")
    day_title = day_group.find_element(By.TAG_NAME, "h2").text

    if "Tue" in day_title or "Thu" in day_title:
        time = card.find_element(By.CSS_SELECTOR, "p[id^='class-time-']").text
        if "6:00 PM" in time:
            gym_class = card.find_element(By.CSS_SELECTOR, "h3[id^='class-name-']").text
            class_button = card.find_element(By.CSS_SELECTOR, "button[id^='book-button-']")
            # Track the class details
            class_info = f"{gym_class} on {day_title}"
            attempted_bookings.append(class_info)

            # Check if already booked
            if class_button.text == "Booked":
                print(f"✓ Already booked: {gym_class.title()} on {day_title}")
                already_booked += 1
                processed_classes.append(f"[Booked] {class_info}")
            elif class_button.text == "Waitlisted":
                print(f"✓ Already on waitlist: {gym_class.title()} on {day_title}")
                already_booked += 1
                processed_classes.append(f"[Waitlisted] {class_info}")
            elif class_button.text == "Book Class":
                # Book the class
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[id^='book-button-']"))
                    )
                    class_button.click()
                    bookings_made += 1
                    print(f"✓ Successfully booked: {gym_class.title()} on {day_title}")
                    processed_classes.append(f"[New Booking] {class_info}")
                except NoSuchElementException:
                    print("Unable to book")

                except TimeoutException:
                    print("Unable to add you to waitlist")
            elif class_button.text == "Join Waitlist":
                # Join waitlist if class is full
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[id^='book-button-']"))
                    )
                    class_button.click()
                    waitlists_joined += 1
                    print(f"✓ Joined waitlist for: {gym_class.title()} on {day_title}")
                    processed_classes.append(f"[New Waitlist] {class_info}")
                except NoSuchElementException:
                    print("Unable to add you to waitlist")

                except TimeoutException:
                    print("Unable to add you to waitlist")

print(f"Total Tuesday/Thursday 6pm classes processed: {bookings_made + waitlists_joined + already_booked}")

# Print detailed class list
print("\n--- DETAILED CLASS LIST ---")
for class_detail in processed_classes:
    print(f"  • {class_detail}")

# Simple comparison
print("\n--- Verification Result ---")
print(f"Expected: {len(attempted_bookings)}")
print(f"Found: {len(processed_classes)}")
if len(attempted_bookings) == len(processed_classes):
    print("✅ SUCCESS: All bookings verified!")
else:
    print(f"❌ MISMATCH: Missing {len(attempted_bookings) - len(processed_classes)} bookings")
