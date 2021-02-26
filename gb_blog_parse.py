import requests
import typing
from urllib.parse import urljoin
import bs4


class GbBlogParse:
    def __init__(self, start_url):
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = []

    def _get_response(self, url):
        response = requests.get(url)
        return response

    def _get_soup(self, url):
        response = self._get_response(url)
        soup = bs4.BeautifulSoup(response.text, "lxml")
        return soup

    def __create_set_links(self, url, tag_list):
        result = set()
        for href in tag_list:
            if href.attrs.get("href"):
                result.add(urljoin(url, href.attrs.get("href")))

        return result

    def __create_task(self, url, callback, tag_list):
        for link in self.__create_set_links(url, tag_list):
            if link not in self.done_urls:
                task = self._get_task(link, callback)
                self.done_urls.add(link)
                self.tasks.append(task)

    def _parse_feed(self, url, soup) -> None:
        ul = soup.find("ul", attrs={"class": "gb__pagination"})
        self.__create_task(url, self._parse_feed, ul.find_all("a"))
        a_tags = soup.find_all("a", attrs={"class": "post-item__title"})
        self.__create_task(url, self._parse_post, a_tags)

    def _parse_post(self, url, soup) -> dict:
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})
        post_title = soup.find("h1", attrs={"class", "blogpost-title"}).text
        data = {
            "post_data": {"url": url, "title": post_title},
            "author": {
                "name": author_name_tag.text,
                "url": urljoin(url, author_name_tag.parent.attrs.get("href")),
            },
            "tags": [
                {"name": tag.text, "url": urljoin(url, tag.attrs.get("href"))}
                for tag in soup.find_all("a", attrs={"class": "small"})
            ],
        }
        return data

    def _get_task(self, url, callback: typing.Callable) -> typing.Callable:
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)

        return task

    def run(self):
        self.tasks.append(self._get_task(self.start_url, self._parse_feed))
        self.done_urls.add(self.start_url)
        for task in self.tasks:
            result = task()
            if isinstance(result, dict):
                print(result)
            print(1)


if __name__ == "__main__":
    url = "https://geekbrains.ru/posts/"
    parser = GbBlogParse(url)
    parser.run()
