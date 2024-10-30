import re
import random
import datetime
import os
import time
import requests
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from selenium import webdriver
from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains

class CrackSlider:
    """
    使用浏览器截图、模板匹配等方法模拟人类滑动行为破解验证码。
    """
    def __init__(self, url='https://stuhealth.jnu.edu.cn/#/login'):
        display = Display(visible=0, size=(800, 600))
        display.start()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        chromedriver_path = "/usr/bin/chromedriver"
        self.driver = webdriver.Chrome(options=chrome_options, executable_path=chromedriver_path)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"""})
        self.url = url
        self.wait = WebDriverWait(self.driver, 20)
        self.driver.get(self.url)
        time.sleep(random.uniform(2, 4))

    def get_image(self, class_name):
        element = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        image_link = element.get_attribute('src')
        return Image.open(BytesIO(requests.get(image_link).content))

    def save_images(self):
        self.target_img = self.get_image('yidun_bg-img')
        self.template_img = self.get_image('yidun_jigsaw')
        self.target_img.save('target.jpg')
        self.template_img.save('template.png')
        self.zoom = 320 / self.target_img.width

    def calculate_tracks(self, distance):
        distance += 20
        current, mid = 0, distance * 3 / 5
        tracks = []

        while current < distance:
            a = 2 if current < mid else -3
            current += a * 0.2
            tracks.append(round(a * 0.2))
        
        return {'forward_tracks': tracks, 'back_tracks': [-3] * 5 + [-2] * 5 + [-1] * 5}

    def match_position(self):
        img_rgb = cv2.imread('target.jpg')
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread('template.png', 0)
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)

        for threshold in [0.95, 0.9, 0.85, 0.8]:
            loc = np.where(res >= threshold)
            if len(loc[1]) == 1:
                return loc[1][0]
        return None

    def crack_slider(self):
        self.save_images()
        distance = self.match_position()
        if distance is None:
            return False

        distance = int((distance + 7) * self.zoom)
        tracks = self.calculate_tracks(distance)

        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'yidun_slider')))
        ActionChains(self.driver).click_and_hold(slider).perform()

        for track in tracks['forward_tracks']:
            ActionChains(self.driver).move_by_offset(xoffset=track, yoffset=0).perform()
        time.sleep(random.uniform(0.5, 1))
        for track in tracks['back_tracks']:
            ActionChains(self.driver).move_by_offset(xoffset=track, yoffset=0).perform()

        ActionChains(self.driver).release().perform()
        time.sleep(1)

        tip = self.driver.find_element(By.CLASS_NAME, 'yidun_tips__text').get_attribute("innerHTML")
        return "通过" in tip

def checkin(name, account, password):
    temp = round(random.uniform(36, 37), 1)
    date_today = str(datetime.date.today())

    slider = CrackSlider()
    if not slider.crack_slider():
        print("滑动验证失败，尝试重试")
        if not slider.crack_slider():
            return None, name, "滑动验证失败"

    try:
        slider.driver.find_element(By.NAME, "appId").send_keys(account)
        slider.driver.find_element(By.NAME, "password").send_keys(password)
        slider.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(2)

        check_time = datetime.datetime.now()
        slider.driver.find_element(By.ID, "10000").click()

        js_remove_readonly = "$('input').removeAttr('readonly')"
        slider.driver.execute_script(js_remove_readonly)

        for period in ["cjtw", "wujtw", "wajtw"]:
            slider.driver.find_element(By.NAME, period).send_keys(str(temp))
            slider.driver.find_element(By.ID, period.replace("tw", "jcrq")).send_keys(date_today)

        slider.driver.find_element(By.ID, "tj").click()
        time.sleep(2)

        feedback = slider.driver.find_element(By.CSS_SELECTOR, 'div[style*="text-align: center;"]').get_attribute("innerHTML")
        result = re.split("<[^\u4e00-\u9fa5]+>", feedback)
        return check_time, name, result
    except Exception as e:
        print(f"错误：{e}")
        return None, name, "提交失败"
    finally:
        slider.driver.quit()

if __name__ == '__main__':
    name = ''
    usr = ''
    pwd = ''
    print(checkin(name, usr, pwd))
