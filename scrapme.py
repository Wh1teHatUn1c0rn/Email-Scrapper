import requests
from bs4 import BeautifulSoup
import urllib.parse
from collections import deque
import re
import time
import random

# Rotating user agents to simulate real browsers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
]


# Function to get random user agent
def get_random_user_agent():
    return random.choice(USER_AGENTS)


# Throttle requests by adding delay
def throttle_request():
    time.sleep(random.uniform(1, 3))


# Function to check if a URL belongs to the same domain
def is_valid_domain(url, base_domain):
    return urllib.parse.urlparse(url).netloc.endswith(base_domain)


def scrape_emails(user_url, allowed_domain=None, max_count=100):
    urls = deque([user_url])
    scraped_urls = set()
    emails = set()
    count = 0

    base_domain = urllib.parse.urlparse(user_url).netloc if allowed_domain is None else allowed_domain

    try:
        while len(urls):
            count += 1
            if count > max_count:
                print(f"[+] Reached the maximum count of {max_count}. Stopping.")
                break

            url = urls.popleft()
            scraped_urls.add(url)
            parts = urllib.parse.urlsplit(url)
            base_url = f"{parts.scheme}://{parts.netloc}"
            path = url[:url.rfind('/') + 1] if '/' in parts.path else url

            print(f'[{count}] Processing {url}')

            headers = {'User-Agent': get_random_user_agent()}
            try:
                response = requests.get(url, headers=headers, timeout=10)
            except (
            requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                continue

            # Extract emails from the response
            new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
            emails.update(new_emails)

            # Parse HTML and extract links
            soup = BeautifulSoup(response.text, "lxml")
            for anchor in soup.find_all("a"):
                link = anchor.get('href', '')
                link = urllib.parse.urljoin(base_url, link)

                # Only queue links from the allowed domain
                if link not in urls and link not in scraped_urls and is_valid_domain(link, base_domain):
                    urls.append(link)

            throttle_request()

    except KeyboardInterrupt:
        print('[-] Interrupted by user, closing.')

    # Save emails to a file or print them
    if emails:
        with open('scraped_emails.txt', 'w') as f:
            for mail in emails:
                f.write(mail + '\n')
                print(mail)
    else:
        print("[-] No emails found.")


if __name__ == "__main__":
    user_url = str(input('[+] Enter Target URL To Scan: '))
    allowed_domain = input('[+] Enter domain to restrict crawling (optional): ').strip() or None
    scrape_emails(user_url, allowed_domain)
