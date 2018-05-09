import requests
import Queue
import random
import json
import os
import selenium
import time
import threading
from os import sys
from bs4 import BeautifulSoup as soup
from random import choice
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from random import randint, choice
from threading import Thread, Lock


# Terry Raffle Bot
# Twitter @zoegodterry


def log(phrase):
    global w_lock
    phrase = phrase.strip()
    with w_lock:
        with open('log.txt', 'a+') as logfile:
            logfile.write(phrase + "\n")
            print(phrase)


def readconfig(filename):
    with open(filename, 'r') as config_json:
        config_data = config_json.read()
    return json.loads(config_data)


def loadaccs(list_accs):
    dict_accs = {}
    for element in list_accs:
        element = element.strip()
        if ":" in element:
            userpass = element.split(":")
            user = userpass[0]
            pw = userpass[1]
            dict_accs[user] = pw
    return dict_accs.items()


def checkentry(page_source):
    page_source = page_source.encode("ascii", "ignore")
    soup_h1 = soup(page_source, "lxml").findAll("h1")
    for h1 in soup_h1:
        if "received" in h1.text:
            return True
    return False


def readproxyfile(proxyfile):
    with open(proxyfile, "r") as raw_proxies:
        proxies = raw_proxies.read().split("\n")
        proxies_list = []
        for individual_proxies in proxies:
            if individual_proxies.strip() != "":
                p_splitted = individual_proxies.split(":")
                if len(p_splitted) == 2:
                    proxies_list.append("http://" + individual_proxies)
                if len(p_splitted) == 4:
                    # ip0:port1:user2:pass3
                    # -> username:password@ip:port
                    p_formatted = "http://{}:{}@{}:{}".format(p_splitted[2], p_splitted[3], p_splitted[0], p_splitted[1])
                    proxies_list.append(p_formatted)
        proxies_list.append(None)
    return proxies_list


def readfile(rawfile):
    with open(rawfile, "r") as CONTENTS:
        CONTENTS = CONTENTS.readlines()
    return CONTENTS


def unlock_p(rand_proxy):
    global p_lock, p_lock_
    if rand_proxy in p_lock:
        with p_lock_:
            p_lock.remove(rand_proxy)
            print("Released proxy: " + str(rand_proxy))


def unlock_a(email):
    global acc_lock_, acc_lock
    if email in acc_lock:
        with acc_lock_:
            acc_lock.remove(email)
            print("Unlocked account: " + email)


# def request_recaptcha(driver, rand_acc_list):
#     global service_key, google_site_key, captcha_url
#     url = "http://2captcha.com/in.php?key=" + service_key + "&method=userrecaptcha&googlekey=" + google_site_key + "&pageurl=" + captcha_url
#     resp = requests.get(url)
#     if resp.text[0:2] != 'OK':
#         log("Error: {} Exiting...".format(resp.text))
#         sys.exit()
#     captcha_id = resp.text[3:]
#     print("Successfully requested for captcha.")
#     return captcha_id


# def receive_token(driver, rand_acc_list, captcha_id):
#     global service_key
#     fetch_url = "http://2captcha.com/res.php?key=" + service_key + "&action=get&id=" + captcha_id
#     for count in range(1, 26):
#         print("Attempting to fetch token. {}/25".format(count))
#         resp = requests.get(fetch_url)
#         if resp.text[0:2] == 'OK':
#             grt = resp.text.split('|')[1]  # g-recaptcha-token
#             print("Captcha token received.")
#             return grt
#         time.sleep(5)
#     print("No tokens received. Restarting...")
#     receive_token(driver, rand_acc_list, captcha_id)


# def submit_recaptcha(grt, at, session, rand_proxy):
#     payload = {
#         "authenticity_token": at,
#         "g-recaptcha-response": grt
#     }
#     headers = {
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "en-US,en;q=0.9",
#         "Content-Type": "application/x-www-form-urlencoded",
#         "Host": "kith.com",
#         "Referer": "https://kith.com/challenge",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
#     }
#     resp = session.post('https://kith.com/account', headers=headers, data=payload, proxies={"https": rand_proxy}, timeout=30)
#     return resp


# def grabauthkey(challenge_html, driver, rand_acc_list):
#     page_soup = soup(challenge_html, 'html.parser')
#     authtokenvar = page_soup.findAll("input", {"name": "authenticity_token"})
#     if authtokenvar:
#         authtoken = authtokenvar[0]["value"]
#         print("Authenticity token found.")
#         return authtoken
#     else:
#         log("No authenticity token found. Restarting...")
#         error_restart(driver, rand_acc_list)


def get_log_cookie(rand_acc_list, rand_proxy, driver):
    print("Logging in " + rand_acc_list[0])
    with requests.Session() as s:
        resp = s.post("https://kith.com/account/login", headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "kith.com",
            "Origin": "https://kith.com",
            "Referer": "https://kith.com/account/login?redirect=/pages/customer-raffle",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
        }, data={
            "form_type": "customer_login",
            "customer[email]": rand_acc_list[0],
            "customer[password]": rand_acc_list[1],
            "checkout_url": " /pages/customer-raffle"
        }, proxies={"https": rand_proxy}, timeout=30, allow_redirects=True)  # false for captcha
        if resp.status_code == 200:
            log("Successfully logged in.")
            unlock_p(rand_proxy)
            return s.cookies
        # if resp.status_code == 302:
        #     print("Captcha Required.")
        #     captcha_id = request_recaptcha(driver, rand_acc_list)
        #     grt = receive_token(driver, rand_acc_list, captcha_id)
        #     challenge = s.get('https://kith.com/challenge', proxies={"https": rand_proxy}, timeout=30)
        #     challenge_html = challenge.content
        #     authtoken = grabauthkey(challenge_html, driver, rand_acc_list)
        #     submit_recaptcha(grt, authtoken, s, rand_proxy)
        else:
            log("Failed to get cookies.")
            error_restart(driver, rand_acc_list)


def error_restart(driver, rand_acc_list):
    global q_lock_, queue_, acc_lock_
    driver.delete_all_cookies()
    driver.refresh()
    with q_lock_:
        queue_.put(1)
    with acc_lock_:
        unlock_a(rand_acc_list[0])


def enter_raffle(accs_tuple, url):
    global zip_, loc_, queue_, q_lock_, acc_lock_, acc_lock, p_list, p_lock_, p_lock
    driver = webdriver.Chrome("chromedriver")
    driver.get(url)
    while queue_.qsize() > 0:
        print("Accounts left: " + str(queue_.qsize()))
        with q_lock_:
            queue_.get()
        rand_proxy = choice(p_list)
        if not rand_proxy in p_lock:
            with p_lock_:
                p_lock.append(rand_proxy)
                print("Using proxy: " + str(rand_proxy))
            rand_acc_list = choice(accs_tuple)
            if not rand_acc_list in acc_lock:
                with acc_lock_:
                    acc_lock.append(rand_acc_list)
                log_cookies_ = get_log_cookie(rand_acc_list, rand_proxy, driver)
                for c in log_cookies_:
                    driver.add_cookie({'name': c.name, 'value': c.value, 'path': c.path, 'expiry': c.expires})
                driver.get(url)
                try:
                    if not checkentry(driver.page_source):
                        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[3]/input[1]"))).send_keys(zip_)
                        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[4]/select[1]/option[" + str(choice(range(2, 20))) + "]"))).click()
                        loc = "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[5]/select[1]/option[" + str(loc_) + "]"
                        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[5]/select[1]/option[" + str(loc_) + "]"))).click()
                        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[7]/input[1]"))).click()
                        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[7]/input[1]"))).submit()
                        time.sleep(3)
                        if checkentry(driver.page_source):
                            log("Successfully entered raffle.")
                            driver.delete_all_cookies()
                            driver.refresh()
                            with w_lock:
                                with open("Entered.txt", "a+") as etxt:
                                    etxt.write(rand_acc_list[0] + ":" + rand_acc_list[1] + "\n")
                        else:
                            log("Failed to enter raffle.")
                            error_restart(driver, rand_acc_list)
                    else:
                        log("Account already entered into raffle.")
                except (Exception, KeyError, TimeoutException, NoSuchElementException, WebDriverException, TypeError):
                    log("Caught an error.")
                    error_restart(driver, rand_acc_list)
            else:
                with q_lock_:
                    queue_.put(1)
        else:
            with q_lock_:
                queue_.put(1)


def wrapper_(accs_tuple, url):
    global queue_, q_lock_, acc_lock_, acc_lock, p_list, p_lock_, p_lock
    num_of_accs = len(accs_tuple)
    for index in range(num_of_accs):
        with q_lock_:
            queue_.put(index)
    st = time.time()
    enter_raffle(accs_tuple, url)
    log("Finished in " + str(time.time() - st))


if __name__ == "__main__":
    config = readconfig("config.json")
    w_lock = Lock()
    q_lock_ = Lock()
    accs_tuple = loadaccs(readfile(config["accfile"]))
    acc_lock_ = Lock()
    acc_lock = []
    p_list = readproxyfile(config["proxyfile"])
    p_lock_ = Lock()
    p_lock = []
    queue_ = Queue.Queue()
    url = config["url"]
    zip_ = config["zip"]
    loc_ = str(int(config["location"]) + 1)
    service_key = config["captchakey"]
    google_site_key = config["sitekey"]
    captcha_url = config["captchasite"]

    wrapper_(accs_tuple, url)
