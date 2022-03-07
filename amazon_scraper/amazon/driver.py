import random
import sys
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


class AmazonDriver:
    """
    Selenium driver wrapper handling Amazon login.
    """

    def __init__(self):
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options

        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(5)

    def login(self, host, email, password):
        driver = self.driver
        driver.get(f"{host}/?language=en_GB")
        rand_sleep()

        driver.find_element(
            By.CSS_SELECTOR,
            "#nav-signin-tooltip > a.nav-action-button"
        ).click()
        rand_sleep()

        driver.find_element(By.ID, "ap_email").clear()
        driver.find_element(By.ID, "ap_email").send_keys(email)

        # Sometimes there is a Continue button after entering your email, sometimes not
        try:
            driver.find_element(By.ID, "continue").click()
            rand_sleep()
        except NoSuchElementException:
            print("No continue button found; ignoring...")

        driver.find_element(By.ID, "ap_password").clear()
        driver.find_element(By.ID, "ap_password").send_keys(password)
        driver.find_element(By.ID, "signInSubmit").click()

    def get_url(self, url):
        self.driver.get(url)
        rand_sleep()
        return self.driver.page_source

    def clean_up(self):
        self.driver.quit()


def rand_sleep(max_seconds=5):
    """
    Wait a little so we won't be treated as a bot.
    """

    seconds = random.randint(2, max_seconds)
    print(f"Sleeping for {seconds} seconds...")
    sys.stdout.flush()
    time.sleep(seconds)
