from time import sleep
from datetime import datetime
from os import system, name as os_name
from io import BytesIO
from re import findall
from base64 import b64encode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from requests import Session, post
from guara.transaction import AbstractTransaction, Application  # Corrected import

# Constants
CAPTCHA_URL = "https://zefoy.com"
CAPTCHA_SOLVER_URL = "https://platipus9999.pythonanywhere.com/"


# Define Transactions
class SolveCaptcha(AbstractTransaction):
    def do(self, **kwargs):
        session = Session()
        session.headers = {
            "authority": "zefoy.com",
            "origin": "https://zefoy.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        }

        while True:
            source_code = str(session.get(CAPTCHA_URL).text).replace("&amp;", "&")
            captcha_token = findall(r'<input type="hidden" name="(.*)">', source_code)

            if "token" in captcha_token:
                captcha_token.remove("token")

            captcha_url = findall(r'img src="([^"]*)"', source_code)[0]
            token_answer = findall(r'type="text" name="(.*)" oninput="this.value', source_code)[0]
            encoded_image = b64encode(
                BytesIO(session.get(CAPTCHA_URL + captcha_url).content).read()
            ).decode("utf-8")
            captcha_answer = post(
                CAPTCHA_SOLVER_URL,
                json={
                    "captcha": encoded_image,
                    "current_time": datetime.now().strftime("%H:%M:%S"),
                },
            ).json()["result"]

            sleep(1)

            data = {
                token_answer: captcha_answer,
            }

            for values in captcha_token:
                token, value = values.split('" value="')
                data[token] = value
            else:
                data["token"] = ""

            response = session.post(CAPTCHA_URL, data=data).text
            try:
                findall(r'remove-spaces" name="(.*)" placeholder', response)[0]
                return {"name": "PHPSESSID", "value": session.cookies.get("PHPSESSID")}
            except:
                pass


class NavigateToZefoy(AbstractTransaction):
    def do(self, **kwargs):
        self._driver.get(CAPTCHA_URL)


class WaitForXPath(AbstractTransaction):
    def do(self, xpath, **kwargs):
        while True:
            try:
                self._driver.find_element(By.XPATH, xpath)
                break
            except:
                pass


class CheckStatus(AbstractTransaction):
    def do(self, xpaths, **kwargs):
        statuses = {}
        for thing in xpaths:
            value = xpaths[thing]
            element = self._driver.find_element(By.XPATH, value)
            if not element.is_enabled():
                statuses.update({thing: "[OFFLINE]"})
            else:
                statuses.update({thing: "[WORKS]"})
        return statuses


class SendBot(AbstractTransaction):
    def do(self, search_button, url_box, vid_info, div, **kwargs):
        element = self._driver.find_element(By.XPATH, url_box)
        element.clear()
        element.send_keys(vid_info)
        self._driver.find_element(By.XPATH, search_button).click()
        sleep(3)

        ratelimit_seconds, full = self.check_submit()
        if "(s)" in str(full):
            self.main_sleep(ratelimit_seconds)
            self._driver.find_element(By.XPATH, search_button).click()
            sleep(2)

        sleep(3)

        send_button = f"/html/body/div[{div}]/div/div/div[1]/div/form/button"
        self._driver.find_element(By.XPATH, send_button).click()
        print(f"Sent {kwargs.get('sent', 0) + 1} times.")
        sleep(4)
        self.do(search_button, url_box, vid_info, div, sent=kwargs.get("sent", 0) + 1)

    def check_submit(self):
        remaining = (
            f'//*[@id="{self._driver.execute_script("return window.tasks[self.option][1]")}"]/span'
        )
        try:
            element = self._driver.find_element(By.XPATH, remaining)
        except:
            return None, None

        if "READY" in element.text:
            return True, True

        if "seconds for your next submit" in element.text:
            output = element.text.split("Please wait ")[1].split(" for")[0]
            minutes = element.text.split("Please wait ")[1].split(" ")[0]
            seconds = element.text.split("(s) ")[1].split(" ")[0]
            sleep_duration = self.convert(int(minutes), int(seconds))
            return sleep_duration, output

        return element.text, None

    def main_sleep(self, delay):
        while delay != 0:
            sleep(1)
            delay -= 1
            self.change_title(
                f"TikTok Zefoy Automator using Zefoy.com / Cooldown: {delay}s / Github: @useragents"
            )

    def convert(self, min: int, sec: int) -> int:
        return min * 60 + sec + 4 if min != 0 else sec + 4

    def change_title(self, arg):
        os.system(f"title {arg}" if os.name == "nt" else "")


# Main Script
if __name__ == "__main__":
    # Set up Selenium WebDriver
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))

    # Initialize Application
    app = Application(driver)

    # Perform actions using the Page Transactions pattern
    app.at(NavigateToZefoy)
    captcha_cookie = app.at(SolveCaptcha).result
    driver.add_cookie(captcha_cookie)
    driver.refresh()

    # Wait for the views button to be available
    app.at(WaitForXPath, xpath="/html/body/div[6]/div/div[2]/div/div/div[5]/div/button")

    # Check the status of all tasks
    xpaths = {
        "followers": "/html/body/div[6]/div/div[2]/div/div/div[2]/div/button",
        "hearts": "/html/body/div[6]/div/div[2]/div/div/div[3]/div/button",
        "comment_hearts": "/html/body/div[6]/div/div[2]/div/div/div[4]/div/button",
        "views": "/html/body/div[6]/div/div[2]/div/div/div[5]/div/button",
        "shares": "/html/body/div[6]/div/div[2]/div/div/div[6]/div/button",
        "favorites": "/html/body/div[6]/div/div[2]/div/div/div[7]/div/button",
    }
    status = app.at(CheckStatus, xpaths=xpaths).result

    # Print status
    for thing in status:
        print(f"{thing} {status[thing]}")

    # Get user input
    option = int(input("Select an option: "))
    video_url = input("Enter video URL: ")

    # Execute the selected task
    tasks = {
        1: ('self.driver.find_element(By.XPATH, xpaths["followers"]).click()', "7"),
        2: ('self.driver.find_element(By.XPATH, xpaths["hearts"]).click()', "8"),
        3: ('self.driver.find_element(By.XPATH, xpaths["comment_hearts"]).click()', "9"),
        4: ('self.driver.find_element(By.XPATH, xpaths["views"]).click()', "10"),
        5: ('self.driver.find_element(By.XPATH, xpaths["shares"]).click()', "11"),
        6: ('self.driver.find_element(By.XPATH, xpaths["favorites"]).click()', "12"),
    }
    task, div = tasks[option]
    eval(task)

    # Send bot
    video_url_box = f"/html/body/div[{div}]/div/form/div/input"
    search_box = f"/html/body/div[{div}]/div/form/div/div/button"
    app.at(SendBot, search_box=search_box, url_box=video_url_box, vid_info=video_url, div=div)
