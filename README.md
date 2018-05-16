# TerryRaffleBot
## Run using python 2.7

Log in kith accounts with requests and enters through selenium.

## Instructions

  * First, you must enter all appropriate information in **config.json**.
    * **url** is the kith [raffle url link](https://kith.com/pages/customer-drawing).
    * **accfile** is the file name of your kith accounts.
    * **proxyfile** is the file name of your proxies.
    * **zip** is your zip code.
    * **location** is the kith location to pick up your pairs if you win. **IMPORANT:* Please refer to **Location**
    * **captchakey** is the api key for your [2captcha](https://goo.gl/T1c75n) account.
    * **sitekey** is the captcha identifier for [kith](https://kith.com/). The sitekey is pre-filled, and should only be changed if [kith](https://kith.com/) renewed their sitekey.
    * **captchasite** is the link to the captcha for [kith](https://kith.com/). The captchasite is pre-filled, and should only be changed if [kith](https://kith.com/) change their captcha page.
  * Secondly, you must install the modules required for the script to work. Please refer to **Required modules**.

**_Note_** If you don't have a 2captcha account, you can create one [here](https://goo.gl/T1c75n).

## Proxies
_Proxies implemented 5-8-18_

  * Every proxy must be on its own line.
  * Every proxy must be the following format:

    * Supports IP Authentication proxies:
    ```ip:host```

    * Supports user:pass Authentication proxies:
    ```ip:host:user:pass```


  * **Example**:
  ```
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345:hello:bye
  123.123.123.123:12345
  123.123.123.123:12345
  123.123.123.123:12345
  123.123.123.123:12345
  ```

## Required modules

Before running the script, the following modules are required:
```requests bs4 lxml selenium colorama```

This can be accomplished by running the following command in a command prompt:

```
pip install requests bs4 lxml selenium colorama
```

## Location

  * The value for location can only be an integer surrounded by quotes.
    * **Kith SoHo** is **"soho"**
    * **Kith Brooklyn** is **"brooklyn"**
    * **Kith Miami** is **"miami"**
    * **Kith LA** is **"los-angeles"**

## To-do List

  * Implement [Google Sheets API](https://developers.google.com/sheets/api/quickstart/python)

## Other scripts

I _might or might not_ release more scripts on my [twitter](https://twitter.com/zoegodterry).

Follow to be the **first ones to know**!
