import requests
from bs4 import BeautifulSoup

def fetch_tvbs_news():
    url = 'https://news.tvbs.com.tw/'
    response = requests.get(url)
    response.encoding = 'utf-8'
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.find_all('h2', class_='news-title')
        
        for index, item in enumerate(news_items, start=1):
            title = item.get_text(strip=True)
            print(f"{index}. {title}")
    else:
        print(f"Failed to retrieve news. Status code: {response.status_code}")

if __name__ == "__main__":
    fetch_tvbs_news()