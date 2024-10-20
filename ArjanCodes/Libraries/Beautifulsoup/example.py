import requests
from bs4 import BeautifulSoup
import urllib.robotparser


def can_scrape(url: str, user_agent: str = "*") -> bool:
    # Create an instance of the robot parser
    rp = urllib.robotparser.RobotFileParser()

    # Parse the robots.txt file of the website
    rp.set_url(url + "/robots.txt")
    rp.read()

    # Check if scraping is allowed for the given user agent
    return rp.can_fetch(user_agent, url)


def main():
    url = "https://arjancodes.com"
    user_agent = "*"

    if can_scrape(url, user_agent):
        print(f"Scraping is allowed on {url} for user agent '{user_agent}'.")
    else:
        print(
            f"Scraping is not allowed on {url} for user agent '{user_agent}'."
        )

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract all the links
    for link in soup.find_all("a"):
        print(link.get("href"))


if __name__ == "__main__":
    main()