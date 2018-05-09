import requests
import Queue
import random
import json
import os
import selenium
import time
from bs4 import BeautifulSoup as soup
from random import choice
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from random import randint, choice
from threading import Thread, Lock

# lxml


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
    soup_html = soup(page_source, "lxml")
    soup_h1 = soup_html.findAll("h1")
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
            log("Released proxy: " + rand_proxy)


def unlock_a(email):
    global acc_lock_, acc_lock
    if email in acc_lock:
        with acc_lock_:
            acc_lock.remove(email)
            log("Unlocked account: " + email)


def enter_raffle(queue_, q_lock_, accs_tuple, acc_lock_, acc_lock, p_list, p_lock_, p_lock, url):
    global zip_, loc_
    while queue_.qsize() > 0:
        with q_lock_:
            queue_.get()
        rand_proxy = choice(p_list)
        if not rand_proxy in p_lock:
            with p_lock_:
                p_lock.append(rand_proxy)
                log("Using proxy: " + str(rand_proxy))
            rand_acc_list = choice(accs_tuple)
            if not rand_acc_list in acc_lock:
                with acc_lock_:
                    acc_lock.append(rand_acc_list)
                log("Logging in " + rand_acc_list[0])
                s = requests.Session()
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
                }, proxies={"https": rand_proxy}, timeout=30)
                log("Successfully logged in (" + resp.cookies["secure_customer_sig"] + ")")
                unlock_p(rand_proxy)
                driver = webdriver.Chrome()
                driver.get("https://kith.com/pages/customer-drawing")
                for c in s.cookies:
                    driver.add_cookie({'name': c.name, 'value': c.value, 'path': c.path, 'expiry': c.expires})
                driver.refresh()
                time.sleep(1.5)
                if not checkentry(driver.page_source):
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[3]/input[1]"))).send_keys(zip_)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[4]/select[1]/option[" + str(choice(range(2, 20))) + "]"))).click()
                    loc = "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[5]/select[1]/option[" + str(loc_) + "]"
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[5]/select[1]/option[" + str(loc_) + "]"))).click()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[7]/input[1]"))).click()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[8]/div[1]/main[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/form[1]/div[7]/input[1]"))).submit()
                    time.sleep(1.5)
                    if checkentry(driver.page_source):
                        log("Successfully entered raffle.")
                        driver.close()
                        driver.quit()
                        with w_lock:
                            with open("Entered.txt", "a+") as etxt:
                                etxt.write(rand_acc_list[0] + ":" + rand_acc_list[1] + "\n")
                    else:
                        log("Failed to enter raffle.")
                        driver.close()
                        driver.quit()
                        with q_lock_:
                            queue_.put(1)
                        with acc_lock_:
                            unlock_a(rand_acc_list[0])


def wrapper_(queue_, q_lock_, accs_tuple, acc_lock_, acc_lock, p_list, p_lock_, p_lock, url):
    num_of_accs = len(accs_tuple)
    for index in range(num_of_accs):
        with q_lock_:
            queue_.put(index)
        t = Thread(target=enter_raffle, args=(queue_, q_lock_, accs_tuple, acc_lock_, acc_lock, p_list, p_lock_, p_lock, url))
        st = time.time()
        t.start()
        t.join()
        log("Finished in " + str(time.time() - st))


if __name__ == "__main__":
    config = readconfig("config.json")
    w_lock = Lock()
    queue_ = Queue.Queue()
    q_lock_ = Lock()
    accs_tuple = loadaccs(readfile(config["accfile"]))
    acc_lock_ = Lock()
    acc_lock = []
    p_list = readproxyfile(config["proxyfile"])
    p_lock_ = Lock()
    p_lock = []
    url = config["url"]
    zip_ = config["zip"]
    loc_ = str(int(config["location"]) + 1)
    wrapper_(queue_, q_lock_, accs_tuple, acc_lock_, acc_lock, p_list, p_lock_, p_lock, url)
