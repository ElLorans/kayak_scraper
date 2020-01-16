"""
Scrape Kayak
Version: 0.0.3
Specs: added error handler in case csv already open
"""


import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from time import sleep
from random import random


def write_csv(dataframe, csv_name):
    """
    Handle error in case csv_name is open.
    """
    try:
        dataframe.to_csv(csv_name, index=False)

    except:
        print("\n!" * 20)
        print(csv_name, "IS OPEN!! Close the file and confirm")
        confirmation = input(f"Have you closed {csv_name}?")
        if confirmation.lower == "yes":
            write_csv(dataframe, csv_name)

            
# Cookie must be updated every tot (2 weeks???) Last Cookie: 26 Nov 2019
headers = {
        "Host": "www.kayak.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": "xp-session-seg=control14; Apache=JAFJAB1D8Ddhww$Jbk538w-AAABbnn3YNw-98-YclfRQ; "
                  "kayak=Jv1vDB_C2TAPMt2$Fzna; "
                  "kayak.mc"
                  "=AbMXwcHKew67JtM5QFg69TLKASksbMSCeOCE5GDpICNsmVmzui5IAr7jdu6Lh9laVd9m4jaA_w5OP7cZrppeOG5BCzKd4EyoajG"
                  "bZE1TNfxOSAZCW1ni9APJIOxksXPpvSie1St5vly0sFXrfY5B6Th0CG_mJo2d7v-PQ8QLjx-Zimv8-Hdd4nhqunMUhIfVQgHChfy"
                  "Xp9b5RffIEmmvI-gKkNCKF6f0lzZLFFXnSDGIVR_rcU9CyAjbi2D8SZ5MpXnpyCtCYodFNDv2Fj0qAPTaos0We6Y79110ehugHQ"
                  "DwFnAxeVgXTm2W_MPUBBbB1GNHkkUkWWHu0USGDWyqsAl9hjNzN-bBZosJjbt52vEwISMQFDlJHUBwF9L-5iiXWPEMjdZY0ADwS"
                  "BV_ActyQiyfLs1Y026QKCdw73RTSgtJ8uU9Vq5xQ8KCsOg23JN6zAgledqrBgwfjs3-OrNys-dMzwBaBjTD8GaktpOZ2h6l0CqK"
                  "12fmpvorLaksqYflfQArAiVNupYSWQhMokH1TB4fzfHnekMWkzcOV00GT4Jj; kykprf=285; p1.med.sid=H-58RzsrTZlDv8E"
                  "9VSsXzZi-asDMG__y9VZjYwFnB3_xAQXpp27GUJRiFFSa9BMC6; _pxhd=""; p1.med.sc=6; _pxvid=1ed3f1e2-1001-11ea"
                  "-9d54-0242ac12000c; _gcl_au=1.1.777878553.1574740783; _ga=GA1.2.109955462.1574740783; _gid=GA1.2.15"
                  "41310337.1574740783; _up=1.2.1950175204.1574740784; G_ENABLED_IDPS=google; __gads=ID=22dffd3207285d"
                  "34:T=1574740790:S=ALNI_Mb4b-OLfcBGBRp4DiGjBqsV82WR7w; cluster=5; NSC_q5-tqbslmf=ffffffff0989b891455"
                  "25d5f4f58455e445a4a422a59; NSC_q5-lbqj=ffffffff0989bd4745525d5f4f58455e445a4a42299c; _gat=1; _gat_U"
                  "A4220918541=1; _gat_UA4220918542=1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "TE": "Trailers"
            }

route = "LAX-ATL"

with requests.session() as s:
    for num in range(99, 160):
        print("READING DATA")
        starting_df = pd.read_csv("db.csv")
        print("DATA READ")
        tgt_date = date.today() + timedelta(num)
        # get direct flights for route on date
        url = f"https://www.kayak.com/flights/{route}/{tgt_date}?sort=bestflight_a&fs=stops=0"
        headers["Referer"] = url
        print("\n" + url)
        resp = s.get(url, headers=headers)
        print("Url requested")
        
        # THIS WORKS ONLY FOR $ and € (IF $ IS BEFORE PRICE AND CARRIER and IF € IS BETWEEN PRICE AND CARRIER)
        soup = BeautifulSoup(resp.text, "lxml")
        dropdowns = soup.find_all("div", {"class": "multibook-dropdown"})
        print("Soup cooked")
        
        if len(dropdowns) == 0:       # if dropdowns fails
            # write file to see error page (only last error will be saved)
            
            if "real KAYAK user" in resp.text:
                error = ["RECAPTCHA"]

            else:
                error = ["DROPDOWNS MISSING"]

                with open("no_dropdowns.html", "w", encoding="utf-8") as f:
                    f.write(resp.text) 
            
            print(error[0])
                
            result = {"price": error, "website": error, "is_best_flight": error, 
                      "departure": error, "arrival": error, "carrier": error, 
                      "retrieved_on": [str(datetime.now())], "flight_date": [tgt_date], "route": [route], "url": [url]}
            
            df = pd.DataFrame(result)
            df = pd.concat([starting_df, df], ignore_index=True, sort=False)

            write_csv(df, "db.csv")
            
            if error == ["RECAPTCHA"]:     # stop loop
                print(num)
                break
            
        else:                        # if dropdowns as intended
            price = list()
            website = list()
            for dropdown in dropdowns:
                pretty = dropdown.text.strip("\n").replace(" Economy", "").strip("Vedi offerta")
                pretty = pretty.replace("View Deal", "").replace("Basic", "")
                pretty = pretty.replace("Cabina principale", "").replace("Main Cabin", "").strip().replace("\n", "")

                if "$" in dropdown.text:        # $ IS BEFORE PRICE AND CARRIER
                    match = re.compile("[^\W\d]").search(pretty)    # find first letter in string
                    # first char is currency, so from second to letter is price
                    ticket_price = pretty[1:match.start()]          
                    price.append(ticket_price)
                    web = pretty[match.start():]

                elif "€" in dropdown.text:     # € IS BETWEEN PRICE AND CARRIER
                    ticket_price = pretty.split("€")[0].strip()
                    price.append(ticket_price)
                    web = pretty.split("€")[1]
                else:
                    price.append("No price")
                    web = pretty.replace("Info", "")

                web = web.split("View Deal")[0]
                website.append(web)

            is_best_flight = [False for dropdown in dropdowns]
            is_best_flight[0] = True                            # first flight should be the best one: IMPLEMENT CHECK????

            departure = [depart.text for depart in soup.find_all("span", {"class": "depart-time base-time"})]
            arrival = [arr.text for arr in soup.find_all("span", {"class": "arrival-time base-time"})]
            
            carrier = [carr.text.strip() for carr in soup.find_all("div", {"class": "bottom"})]
            while '' in carrier:
                carrier.remove('')
            carrier = carrier[0::2]    # removes even position carriers because they are useless

            result = {"price": price, "website": website, "is_best_flight": is_best_flight, "departure": departure, 
                      "arrival": arrival, "carrier": carrier}

            print("Converting data to DF")
            df = pd.DataFrame(result)
            now = datetime.now()
            df["retrieved_on"] = now
            df["flight_date"] = tgt_date
            df["route"] = route
            df["url"] = url
            df = pd.concat([starting_df, df], ignore_index=True, sort=False)

            write_csv(df, "db.csv")
            
            #sleep(random()*4)                # random pause to avoid recaptcha
            print("DATA SAVED:", now)

print("\nEND!!")
print("-"*30)
