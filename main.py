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


def grabauthkey(challenge_html):
    page_soup = soup(challenge_html, 'lxml')
    authtokenvar = page_soup.findAll("input", {"name": "authenticity_token"})
    if authtokenvar:
        authtoken = authtokenvar[0]["value"]
        return authtoken
    else:
        return("Nope")


def get_log_cookie(rand_acc_list, rand_proxy, driver):
    print("Logging in " + rand_acc_list[0])
    with requests.Session() as s:
        s.post("https://kith.com/account/login", headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "kith.com",
            "Origin": "https://kith.com",
            "Referer": "https://kith.com/account/login?redirect=/pages/customer-raffle",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
        }, data={
            "form_type": "customer_login",
            "customer[email]": rand_acc_list[0],
            "customer[password]": rand_acc_list[1],
            "checkout_url": "/pages/customer-raffle"
        }, proxies={"https": rand_proxy}, timeout=30)  # false for captcha
        challenge = s.get('https://kith.com/challenge', proxies={"https": rand_proxy})
        challenge_html = challenge.content
        authtoken = grabauthkey(challenge_html)
        if authtoken != "Nope":  # captcha required
            print("Authenticity token found.")
            r_c = captcha_harvester()
            payload = {
                "authenticity_token": authtoken,
                "g-recaptcha-response": r_c
            }
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Host": "kith.com",
                "Origin": "https://kith.com",
                "Referer": "https://kith.com/challenge",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
            }
            resp = s.post('https://kith.com/account/login', headers=headers, data=payload, proxies={"https": rand_proxy}, timeout=30)
            print("Successfully logged in with captcha. S_C: " + str(resp.status_code))
            unlock_p(rand_proxy)
            return s.cookies
        else:  # no captcha required
            print("Successfully logged in.")
            unlock_p(rand_proxy)
            return s.cookies


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
    driver_proxy = choice(p_list)
    if driver_proxy != None:
        proxy_parts = (driver_proxy.split("http://")[1]).split(":")
        # [username][password@ip][port]
        # [ip][port]
        if len(proxy_parts) == 3:
            options = webdriver.ChromeOptions()
            PROXY = ((((proxy_parts[1].split("@"))[1]) + ":" + proxy_parts[2]))  # IP:PORT
            print("Driver using Auth proxy: " + PROXY)
            options.add_extension("Proxy_Auth.crx")
            options.add_argument("--proxy-server=http://{}".format(PROXY))
            driver = webdriver.Chrome(chrome_options=options)
            main_window = driver.window_handles[0]
            second_window = driver.window_handles[1]
            driver.switch_to_window(second_window)
            driver.close()
            driver.switch_to_window(main_window)
            driver.get("chrome-extension://ggmdpepbjljkkkdaklfihhngmmgmpggp/options.html")
            driver.find_element_by_id("login").send_keys(proxy_parts[0])
            driver.find_element_by_id("password").send_keys((proxy_parts[1].split("@"))[0])
            driver.find_element_by_id("retry").clear()
            driver.find_element_by_id("retry").send_keys("2")
            driver.find_element_by_id("save").click()
        if len(proxy_parts) == 2:
            proxy = ':'.join(proxy_parts)
            print ("Driver using No-Auth proxy: " + proxy)
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--proxy-server=%s' % proxy)
            driver = webdriver.Chrome(chrome_options=chrome_options)
    else:
        print "Driver using no proxy!"
        driver = webdriver.Chrome()
    driver.get(url)
    while queue_.qsize() > 0:
        try:
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
                    time.sleep(2)
                    try:
                        if (not checkentry(driver.page_source)):
                            WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[3]/input[1]"))).send_keys(zip_)
                            WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[4]/select[1]/option[" + str(choice(range(2, 20))) + "]"))).click()
                            loc = "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[5]/select[1]/option[" + str(loc_) + "]"
                            WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[5]/select[1]/option[" + str(loc_) + "]"))).click()
                            WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[7]/input[1]"))).click()
                            WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[7]/input[1]"))).submit()
                            time.sleep(2)
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
        except Exception:
            error_restart(driver, rand_acc_list)
            with q_lock_:
                queue_.put(1)


def captcha_harvester():
    with requests.session() as c_s:
        captcha_id = request_recaptcha(c_s)
        token = receive_token(captcha_id, c_s)
        print("Token received.")
        return token


def request_recaptcha(session):
    global service_key, google_site_key, captcha_url
    url = "http://2captcha.com/in.php?key=" + service_key + "&method=userrecaptcha&googlekey=" + google_site_key + "&pageurl=" + captcha_url
    resp = session.get(url)
    if resp.text[0:2] != 'OK':
        log("Error: {} Exiting...".format(resp.text))
    captcha_id = resp.text[3:]
    print("Successfully requested for captcha.")
    return captcha_id


def receive_token(captcha_id, session):
    global service_key
    fetch_url = "http://2captcha.com/res.php?key=" + service_key + "&action=get&id=" + captcha_id
    for count in range(1, 26):
        print("Attempting to fetch token. {}/25".format(count))
        resp = session.get(fetch_url)
        if resp.text[0:2] == 'OK':
            grt = resp.text.split('|')[1]  # g-recaptcha-token
            print("Captcha token received.")
            return grt
        time.sleep(5)
    print("No tokens received. Restarting...")
    receive_token(captcha_id, session)


def wrapper_(accs_tuple, url):
    global queue_, q_lock_
    num_of_accs = len(accs_tuple)
    for index in range(num_of_accs):
        with q_lock_:
            queue_.put(index)
    st = time.time()
    # t_list = []
    # t_list.append(Thread(target=enter_raffle, args=(accs_tuple, url)))
    # for t_ in t_list:
    #     t_.start()
    #     t_.join()
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
    # c_list = []
    # c_lock = Lock()
    wrapper_(accs_tuple, url)
