import re
import random
import datetime
import os
from os import getenv
import cv2
import numpy as np
import datetime
from io import BytesIO
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from PIL import Image
from selenium import webdriver
from pyvirtualdisplay import Display
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions

class CrackSlider():
    """
    通过浏览器截图，识别验证码中缺口位置，获取需要滑动距离，并模仿人类行为破解滑动验证码
    """

    def __init__(self):
        super(CrackSlider, self).__init__()
        display = Display(visible=0, size=(800, 600))
        display.start()
        chrome_options = webdriver.ChromeOptions()
        '''chrome_options.add_argument('--headless')'''
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chromedriver = "/usr/bin/chromedriver"
        os.environ["webdriver.chrome.driver"] = chromedriver
        self.driver = webdriver.Chrome(
            options=chrome_options, executable_path=chromedriver)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", { "source": """ Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) """ })    
        self.url = 'https://stuhealth.jnu.edu.cn/#/login'  # 测试网站
        self.wait = WebDriverWait(self.driver, 20)
        self.driver.get(self.url)
        time.sleep(random.randint(2,4))

    def open(self):
        self.driver.get(self.url)

    def get_pic(self):
        time.sleep(random.randint(2,4))
        target = self.wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'yidun_bg-img')))
        template = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'yidun_jigsaw')))
        target_link = target.get_attribute('src')
        template_link = template.get_attribute('src')
        target_img = Image.open(BytesIO(requests.get(target_link).content))
        template_img = Image.open(BytesIO(requests.get(template_link).content))
        target_img.save('target.jpg')
        template_img.save('template.png')
        size_orign = target.size
        local_img = Image.open('target.jpg')
        size_loc = local_img.size
        self.zoom = 320 / int(size_loc[0])

    def get_tracks(self, distance):
        print(distance)
        distance += 20
        v = 0
        t = 0.2
        forward_tracks = []
        current = 0
        mid = distance * 3/5
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            s = v * t + 0.5 * a * (t**2)
            v = v + a * t
            current += s
            forward_tracks.append(round(s))
        back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]
        return {'forward_tracks': forward_tracks, 'back_tracks': back_tracks}

    def match(self, target, template):
        img_rgb = cv2.imread(target)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template, 0)
        run = 1
        w, h = template.shape[::-1]
        print(w, h)
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        # 使用二分法查找阈值的精确值
        L = 0
        R = 1
        while run < 20:
            run += 1
            threshold = (R + L) / 2
            print(threshold)
            if threshold < 0:
                print('Error')
                return None
            loc = np.where(res >= threshold)
            print(len(loc[1]))
            if len(loc[1]) > 1:
                L += (R - L) / 2
            elif len(loc[1]) == 1:
                print('目标区域起点x坐标为：%d' % loc[1][0])
                break
            elif len(loc[1]) < 1:
                R -= (R - L) / 2
        return loc[1][0]

    def crack_slider(self):
        self.open()
        target = 'target.jpg'
        template = 'template.png'
        self.get_pic()
        distance = self.match(target, template)
        tracks = self.get_tracks((distance + 7)*self.zoom)  # 对位移的缩放计算
        print(tracks)
        slider = self.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, 'yidun_slider')))
        ActionChains(self.driver).click_and_hold(slider).perform()
        for track in tracks['forward_tracks']:
            ActionChains(self.driver).move_by_offset(
                xoffset=track, yoffset=0).perform()
        time.sleep(random.randint(2,4))
        for back_tracks in tracks['back_tracks']:
            ActionChains(self.driver).move_by_offset(
                xoffset=back_tracks, yoffset=0).perform()
        ActionChains(self.driver).move_by_offset(
            xoffset=-3, yoffset=0).perform()
        ActionChains(self.driver).move_by_offset(
            xoffset=3, yoffset=0).perform()
        time.sleep(random.randint(2,4))
        ActionChains(self.driver).release().perform()
        time.sleep(random.randint(2,4))
        if (self.driver.find_element(By.XPATH,'//*[@class="yidun_tips__text yidun-fallback__tip"]').get_attribute("innerHTML") == '向右拖动滑块填充拼图'):
            print('滑动验证不通过，正在重试')
            self.crack_slider()
        else:
            print(self.driver.find_element(By.XPATH,
                '//*[@class="yidun_tips__text yidun-fallback__tip"]').get_attribute("innerHTML") + '滑动验证通过')


def checkin(name, account, password):
    usr = account
    pwd = password
    #增加温度的填写
    temp = random.uniform(36,37)
    temp = str(round(temp,1))
    #增加日期
    td = datetime.date.today()
    td = str(td)
    sl = CrackSlider()
    sl.crack_slider()
    sl.driver.find_element(By.XPATH,"//input[@name='appId']").send_keys(usr)
    sl.driver.find_element(By.XPATH,"//input[@name='password']").send_keys(pwd)
    sl.driver.find_element(By.XPATH,"//button[@type='submit']").click()
    time.sleep(random.randint(2,4))
    checktime = datetime.datetime.now()
    try:
        sl.driver.find_element(By.XPATH,'//*[@id="10000"]').click()
        '''增加新表格'''
        #去除readonly限制
        js = "$('input').removeAttr('readonly')"
        sl.driver.execute_script(js)
        #早
        sl.driver.find_element(By.XPATH, '//*[@name="cjtw"]').send_keys(temp)
        sl.driver.find_element(By.XPATH, '//*[@id="twyjcrq"]').send_keys(td)
        #中
        sl.driver.find_element(By.XPATH, '//*[@name="wujtw"]').send_keys(temp)
        sl.driver.find_element(By.XPATH, '//*[@id="twejcrq"]').send_keys(td)           
        #晚
        sl.driver.find_element(By.XPATH, '//*[@name="wajtw"]').send_keys(temp)
        sl.driver.find_element(By.XPATH, '//*[@id="twsjcrq"]').send_keys(td)
            
        sl.driver.find_element(By.XPATH,'//*[@id="tj"]').click()
        time.sleep(random.randint(2,4))
        try:
            temp = sl.driver.find_element(By.XPATH,
                '//*[@style="text-align: center;margin-bottom: 100px"]').get_attribute("innerHTML")
            result = re.split("<[^\u4e00-\u9fa5]+>", temp)
            return checktime, name, result
        except:
            try:
                temp = sl.driver.find_element(By.XPATH,
                    '//*[@style="text-align: center;margin-bottom: 100px;margin-top: 17px"]').get_attribute("innerHTML")
                result = re.split("<[^\u4e00-\u9fa5]+>", temp)
                return checktime, name, result
            except:
                return checktime, name, "失败了"
        sl.driver.close()
    except:
        try:
            temp = sl.driver.find_element(By.XPATH,
                '//*[@style="text-align: center;margin-bottom: 100px"]').get_attribute("innerHTML")
            result = re.split("<[^\u4e00-\u9fa5]+>", temp)
            return checktime, name, result
        except:
            try:
                temp = sl.driver.find_element(By.XPATH,
                    '//*[@style="text-align: center;margin-bottom: 100px;margin-top: 17px"]').get_attribute("innerHTML")
                result = re.split("<[^\u4e00-\u9fa5]+>", temp)
                return checktime, name, result
            except:
                return checktime, name, "失败了"
        sl.driver.close()

if __name__ == '__main__':
    name = ''
    usr = ''
    pwd = ''
    print(checkin(name, usr, pwd))

