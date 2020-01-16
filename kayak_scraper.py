"""
Scrape Kayak
Version: 0.0.5
Specs: code more readable
"""


import re
from datetime import date, timedelta, datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup


def write_csv(dataframe, csv_name):
    """
    Handle error in case csv_name is open.
    """
    try:
        dataframe.to_csv(csv_name, index=False)

    except PermissionError:
        print("\n", "!" * 20)
        print(csv_name, "IS OPEN!! Close the file and confirm")
        confirmation = input(f"Have you closed {csv_name}?")
        if confirmation.lower == "yes":
            write_csv(dataframe, csv_name)


class KayakScraper:                          # class in order to have .error attribute
    """
    self.data for pd.DataFrame with data; self.error for error.
    """
    def __init__(self, html: str, route: str, url: str, departing_date: str) -> None:
        """
        Scrape Kayak best flight page and update self.data (Calls kayak_scraper method).
        :param html: str (html format)
        :param route: str (e.g.: "LAX-ATL")
        :param url: str
        :param departing_date: str
        :return: None
        """
        self.data = None                            # after initializing: pd.DataFrame
        self.error = None                           # after initializing: "DROPDOWNS MISSINg" or "RECAPTCHA" or False
        self.kayak_scraper(html, route, url, departing_date)

    def kayak_scraper(self, html: str, flight_route: str, kayak_url: str, flight_date: str) -> None:
        """
        Scrape Kayak best flight page and update self.data (Called by __init__ method).
        :param html: str (html format)
        :param flight_route: str (e.g.: "LAX-ATL")
        :param kayak_url: str
        :param flight_date: str
        :return: None
        """
        today = str(date.today())
        now_time = str(datetime.now().time())[:-7]

        print("Parsing html")
        soup = BeautifulSoup(html, "lxml")
        dropdowns = soup.find_all("div", {"class": "multibook-dropdown"})
        print("Html parsed")

        if len(dropdowns) == 0:  # if dropdowns fails
            # write file to see error page (only last error will be saved)

            if "real KAYAK user" in html:
                self.error = "RECAPTCHA"
                print(self.error)

            else:
                self.error = "DROPDOWNS MISSING"
                print(self.error)

                with open("no_dropdowns.html", "w", encoding="utf-8") as file:
                    file.write(html)

            print(self.error)
            error = [self.error]
            data = {"arrival": error, "carrier": error, "departure": error, "flight_date": flight_date,
                    "is_best_flight": error, "price": error, "route": [flight_route], "website": error,
                    "url": [kayak_url], "retrieved_on": [today], "retrieved_at": [now_time]}

            self.data = pd.DataFrame(data)

        else:  # if len(dropdowns) > 0:             # (as intended)
            self.error = False
            prices = list()
            websites = list()
            for dropdown in dropdowns:
                pretty = dropdown.text.strip("\n").replace(" Economy", "").strip("Vedi offerta")\
                    .replace("View Deal", "").replace("Basic", "").replace("Cabina principale", "")\
                    .replace("Main Cabin", "").strip().replace("\n", "")

                # set ticket_price and web
                if "$" in dropdown.text:  # $ IS BEFORE PRICE AND CARRIER
                    match = re.compile("[^\W\d]").search(pretty)  # find first letter in string
                    # first char is currency, so from second to letter is price
                    ticket_price = pretty[1:match.start()]
                    website = pretty[match.start():].split("Book")[0]

                elif "€" in dropdown.text:  # € IS BETWEEN PRICE AND CARRIER
                    ticket_price = pretty.split("€")[0].strip()
                    website = pretty.split("€")[1].split("Book")[0]

                else:
                    ticket_price = "No price"
                    website = pretty.replace("Info", "").split("Book")[0]
                    # print("NO PRICE FOUND:", dropdown.text.replace("\n", ""))    # ONLY SOUTHWEST PRICES ARE NOT FOUND
                # ticket_price and web have been set

                prices.append(ticket_price)
                website = website.split("View Deal")[0]
                websites.append(website)

            arrival = [arr.text for arr in soup.find_all("span", {"class": "arrival-time base-time"})]

            carrier = [carr.text.strip() for carr in soup.find_all("div", {"class": "bottom"})]
            while '' in carrier:
                carrier.remove('')
            carrier = carrier[0::2]                         # removes even position carriers because they are empty str

            departure = [depart.text for depart in soup.find_all("span", {"class": "depart-time base-time"})]

            is_best_flight = [False for _ in dropdowns]
            is_best_flight[0] = True  # first flight should be the best one: IMPLEMENT CHECK????

            data = {"arrival": arrival, "carrier": carrier, "departure": departure, "is_best_flight": is_best_flight,
                    "price": prices, "website": websites}

            self.data = pd.DataFrame(data)

            self.data["flight_date"] = flight_date
            self.data["route"] = flight_route
            self.data["url"] = kayak_url
            self.data["retrieved_at"] = now_time
            self.data["retrieved_on"] = today


def kayak_requester_range(start_range: int, end_range: int, flight_route: str) -> None:
    """
    Create db.csv file for flights departing every day from start_range to end_range excluded.
    :param start_range: int (e.g.: 0)
    :param end_range: int (e.g.: 160)
    :param flight_route: str (e.g.: "LAX-ATL")
    :return: None
    """

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

    with requests.session() as s:
        for num in range(start_range, end_range):

            print("READING DATA")
            try:
                starting_df = pd.read_csv("db.csv")
                print("DATA READ")
            except FileNotFoundError:
                print("ERROR: db.csv NOT FOUND")
                column_names = ["arrival", "carrier", "departure", "is_best_flight", "price", "website", "flight_date",
                                "route", "url", "retrieved_at", "retrieved_on"]
                starting_df = pd.DataFrame(columns=column_names)    # empty df
                print("db.csv CREATED")
                write_csv(starting_df, "db.csv")

            tgt_date = date.today() + timedelta(num)
            # get direct flights for route on date
            url = f"https://www.kayak.com/flights/{flight_route}/{tgt_date}?sort=bestflight_a&fs=stops=0"
            headers["Referer"] = url        # update referer header for cookies. Unclear if needed
            print("\n" + url)
            resp = s.get(url, headers=headers)
            print("Url requested")

            scraped = KayakScraper(resp.text, flight_route, url, str(tgt_date))

            df = pd.concat([starting_df, scraped.data], ignore_index=True, sort=False)

            print("SAVING DATA", str(datetime.now().time())[:-7])
            write_csv(df, "db.csv")
            print("DATA SAVED:", str(datetime.now().time())[:-7])

            if scraped.error is "RECAPTCHA":
                print("ABORTING")
                break
            elif scraped.error is "DROPDOWNS MISSING":
                resp = s.get(url, headers=headers)
                print("Url requested AGAIN")

                scraped = KayakScraper(resp.text, flight_route, url, str(tgt_date))

                df = pd.concat([starting_df, scraped.data], ignore_index=True, sort=False)

                print("SAVING DATA", str(datetime.now().time())[:-7])
                write_csv(df, "db.csv")
                print("DATA SAVED:", str(datetime.now().time())[:-7])

    print("-" * 30)
    print("END")


def kayak_requester():
    pass


if __name__ == "__main__":
    # with open("kayakked.html", encoding="utf-8") as f:
    #     t = f.read()
    # d = KayakScraper(t, "LAX-ATL", "www.test", "14-07-20")
    # d.data.to_csv("t.csv")
    st = input("Insert starting date:")
    e = input("Insert final date (excluded):")
    kayak_requester_range(int(st), int(e), "LAX-ATL")
