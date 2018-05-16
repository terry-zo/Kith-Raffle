import requests
import json
import sys
sys.path.append("config")
sys.path.append("classes")
from sel_kith import *
from verifier import *
from Queue import Queue
from time import time, sleep
from bs4 import BeautifulSoup as soup
from random import randint, choice
from threading import Thread, Lock

# Terry Raffle Bot
# Twitter @zoegodterry


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
    global GLOBAL_VARIABLES
    if rand_proxy in GLOBAL_VARIABLES["p_ll"]:
        with GLOBAL_VARIABLES["p_lock_"]:
            GLOBAL_VARIABLES["p_ll"].remove(rand_proxy)


def unlock_a(email):
    global GLOBAL_VARIABLES
    if email in GLOBAL_VARIABLES["acc_ll"]:
        with GLOBAL_VARIABLES["acc_lock_"]:
            GLOBAL_VARIABLES["acc_ll"].remove(email)
            print("Unlocked account: " + email)


def grabauthkey(challenge_html):
    page_soup = soup(challenge_html, 'lxml')
    authtokenvar = page_soup.findAll("input", {"name": "authenticity_token"})
    if authtokenvar:
        authtoken = authtokenvar[0]["value"]
        return authtoken
    else:
        return("Nope")


def get_log_cookie(rand_acc_list, rand_proxy):
    print("Logging in " + rand_acc_list[0])
    is_verified = verifier(rand_proxy, rand_acc_list[0])
    if is_verified == True:
        with requests.Session() as s:
            KITH_RESP = s.post("https://kith.com/account/login", headers={
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
            if (KITH_RESP.url == "https://kith.com/challenge") or (KITH_RESP.url == "https://kith.com/challenge/"):  # captcha required
                r_c = captcha_harvester()
                authtoken = grabauthkey(KITH_RESP.content)
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
                print("Successfully logged in with captcha.")
                unlock_p(rand_proxy)
                return s.cookies
            else:  # no captcha required
                print("Successfully logged in without captcha.")
                unlock_p(rand_proxy)
                return s.cookies
    else:
        return is_verified


def error_restart(thread_driver, rand_acc_list):
    global GLOBAL_VARIABLES
    thread_driver.refresh()
    with GLOBAL_VARIABLES["q_lock_"]:
        GLOBAL_VARIABLES["queue_"].put(1)
    with GLOBAL_VARIABLES["acc_lock_"]:
        unlock_a(rand_acc_list[0])


def enter_raffle(accs_tuple, url):
    global GLOBAL_VARIABLES, GLOBAL_DATA
    driver_proxy = choice(readproxyfile("config/" + config["proxyfile"]))
    thread_driver = sel()
    thread_driver.CreateHeadlessBrowser(driver_proxy)
    thread_driver.driver.get(url)
    while GLOBAL_VARIABLES["queue_"].qsize() > 0:
        try:
            print("Accounts left: " + str(GLOBAL_VARIABLES["queue_"].qsize()))
            with GLOBAL_VARIABLES["q_lock_"]:
                GLOBAL_VARIABLES["queue_"].get()
            rand_proxy = choice(readproxyfile("config/" + config["proxyfile"]))
            if not rand_proxy in GLOBAL_VARIABLES["p_ll"]:
                with GLOBAL_VARIABLES["p_lock_"]:
                    GLOBAL_VARIABLES["p_ll"].append(rand_proxy)
                    print("Using proxy: " + str(rand_proxy))
                if len(accs_tuple) != 0:
                    rand_acc_list = choice(accs_tuple)
                    with GLOBAL_VARIABLES["acc_lock_"]:
                        accs_tuple = accs_tuple[:accs_tuple.index(rand_acc_list)] + accs_tuple[(accs_tuple.index(rand_acc_list) + 1):]
                    log_cookies_ = get_log_cookie(rand_acc_list, rand_proxy)
                    if (log_cookies_ != False) and (log_cookies_ != "banned"):
                        for c in log_cookies_:
                            thread_driver.driver.add_cookie({'name': c.name, 'value': c.value, 'path': c.path, 'expiry': c.expires})
                        thread_driver.driver.get(url)
                        sleep(2)
                        if (not thread_driver.checkentry()):
                            rand_sz = GLOBAL_DATA[str(choice(range(2, 20)))]
                            thread_driver.submit_entry(GLOBAL_VARIABLES, rand_sz)
                            if thread_driver.checkentry():
                                print("Successfully entered raffle.")
                                thread_driver.refresh()
                                with GLOBAL_VARIABLES["w_lock"]:
                                    with open("config/Entered.txt", "a+") as etxt:
                                        etxt.write("{}:{}\n".format(rand_acc_list[0], rand_acc_list[1]))
                                    with open("config/Entered_Detailed.txt", "a+") as etxt:
                                        etxt.write("{}:{}:{}:{}\n".format(rand_acc_list[0], rand_acc_list[1], rand_sz, GLOBAL_VARIABLES["actual_loc"]))
                            else:
                                print("Failed to enter raffle.")
                                error_restart(thread_driver, rand_acc_list)
                        else:
                            print("Account already entered into raffle.")
                    elif log_cookies_ == "banned":
                        with GLOBAL_VARIABLES["acc_lock_"]:
                            accs_tuple = accs_tuple + tuple(rand_acc_list)
                else:
                    print("Selected proxy is in use.")
                    with GLOBAL_VARIABLES["q_lock_"]:
                        GLOBAL_VARIABLES["queue_"].put(1)
            else:
                print("Finished all accounts.")
                sys.exit()
        except:
            print("Caught an error.")
            with GLOBAL_VARIABLES["q_lock_"]:
                GLOBAL_VARIABLES["queue_"].put(1)


def captcha_harvester():
    with requests.session() as c_s:
        captcha_id = request_recaptcha(c_s)
        token = receive_token(captcha_id, c_s)
        print("Token received.")
        return token


def request_recaptcha(session):
    global GLOBAL_VARIABLES
    url = "http://2captcha.com/in.php?key=" + GLOBAL_VARIABLES["service_key"] + "&method=userrecaptcha&googlekey=" + GLOBAL_VARIABLES["google_site_key"] + "&pageurl=" + GLOBAL_VARIABLES["captcha_url"]
    resp = session.get(url)
    if resp.text[0:2] != 'OK':
        print("Error: {} Exiting...".format(resp.text))
    captcha_id = resp.text[3:]
    print("Successfully requested for captcha.")
    return captcha_id


def receive_token(captcha_id, session):
    global GLOBAL_VARIABLES
    fetch_url = "http://2captcha.com/res.php?key=" + GLOBAL_VARIABLES["service_key"] + "&action=get&id=" + captcha_id
    for count in range(1, 26):
        print("Attempting to fetch token. {}/25".format(count))
        resp = session.get(fetch_url)
        if resp.text[0:2] == 'OK':
            grt = resp.text.split('|')[1]  # g-recaptcha-token
            print("Captcha token received.")
            return grt
        sleep(5)
    print("No tokens received. Restarting...")
    receive_token(captcha_id, session)


def wrapper_(accs_tuple, url):
    global GLOBAL_VARIABLES
    num_of_accs = len(accs_tuple)
    for index in range(num_of_accs):
        with GLOBAL_VARIABLES["q_lock_"]:
            GLOBAL_VARIABLES["queue_"].put(index)
    st = time()
    enter_raffle(accs_tuple, url)
    print("Finished in " + str(time() - st))


if __name__ == "__main__":
    config = readconfig("config/config.json")
    GLOBAL_DATA = readconfig("classes/DATA.json")
    GLOBAL_VARIABLES = {
        "w_lock": Lock(),
        "q_lock_": Lock(),
        "acc_lock_": Lock(),
        "p_lock_": Lock(),
        "acc_ll": [],
        "p_ll": [],
        "queue_": Queue(),
        "url": config["url"],
        "zip_": config["zip"],
        "loc_": config["location"],
        "service_key": config["captchakey"],
        "google_site_key": config["sitekey"],
        "captcha_url": config["captchasite"],
        "actual_loc": GLOBAL_DATA[config["location"]]
    }
    e_acc = loadaccs(readfile("config/Entered.txt"))
    raw_accs_tuple = loadaccs(readfile("config/" + config["accfile"]))
    accs_tuple = []
    for accs_ in raw_accs_tuple:
        if not(accs_ in e_acc):
            accs_tuple.append(accs_)
    accs_tuple = tuple(accs_tuple)
    wrapper_(accs_tuple, GLOBAL_VARIABLES["url"])
