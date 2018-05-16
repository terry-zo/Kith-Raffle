import platform
import time
from random import choice, randint
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class sel():

    @staticmethod
    def send_multiple_keys_(dict):
        for send_request in dict.items():
            send_request[0].send_keys(send_request[1])

    def checkentry(self):
        page_source = self.driver.page_source.encode("ascii", "ignore")
        soup_h1 = soup(page_source, "lxml").findAll("h1")
        for h1 in soup_h1:
            if "received" in h1.text:
                return True
        return False

    def submit_entry(self, GLOBAL_VARIABLES, actual_sz):
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[3]/input[1]"))).send_keys(GLOBAL_VARIABLES["zip_"])
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.XPATH, "//option[@value='men']"))).click()  # //option[@value='men']
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//option[@value=\'" + str(actual_sz) + "\']"))).click()  # size
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//option[@value=\'" + str(GLOBAL_VARIABLES["loc_"]) + "\']"))).click()  # location
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@id='agreeToTerms']"))).click()  # terms
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))).click()  # submit button
        time.sleep(2)

    def refresh(self):
        self.driver.delete_all_cookies()
        self.driver.refresh()

    def CreateHeadlessBrowser(self, proxy):
        options = webdriver.ChromeOptions()
        # options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.add_argument("window-size=1920,1080")
        # options.add_argument("--start-maximized")
        # options.add_argument("--allow-running-insecure-content")
        chrome_instance = "builds/" + str(platform.system()) + "_chrome"
        if proxy != None:
            proxy_parts = (proxy.split("http://")[1]).split(":")
            if len(proxy_parts) == 3:
                PROXY = ((((proxy_parts[1].split("@"))[1]) + ":" + proxy_parts[2]))  # IP:PORT
                options.add_extension("builds/Proxy_Auth.crx")
                options.add_argument("--proxy-server=http://{}".format(PROXY))
                self.driver = webdriver.Chrome(chrome_instance, chrome_options=options)
                main_window = self.driver.window_handles[0]
                second_window = self.driver.window_handles[1]
                self.driver.switch_to_window(second_window)
                self.driver.close()
                self.driver.switch_to_window(main_window)
                self.driver.get("chrome-extension://ggmdpepbjljkkkdaklfihhngmmgmpggp/options.html")
                self.driver.find_element_by_id("login").send_keys(proxy_parts[0])
                self.driver.find_element_by_id("password").send_keys((proxy_parts[1].split("@"))[0])
                self.driver.find_element_by_id("retry").clear()
                self.driver.find_element_by_id("retry").send_keys("2")
                self.driver.find_element_by_id("save").click()
            elif len(proxy_parts) == 2:
                proxy = ':'.join(proxy_parts)
                options.add_argument('--proxy-server=%s' % proxy)
                self.driver = webdriver.Chrome(chrome_instance, chrome_options=options)
        else:
            self.driver = webdriver.Chrome(chrome_instance, chrome_options=options)
        print("Driver proxy: " + str(proxy))

    def end_session(self):
        driver = self.driver
        driver.close()
        driver.quit()
