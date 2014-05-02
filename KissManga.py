#/usr/bin/python

from bs4 import BeautifulSoup
import gzip
import re
import io
import urllib.request, urllib.error, urllib.parse
from Crawler import Crawler

class KissManga(Crawler):
	def __init__(self, url):
		self.url = url
		if re.match(r'.*kissmanga\.com/Manga/.*/', url, flags=re.IGNORECASE):
			self.page = BeautifulSoup(self.open_url(self.chapter_series(url)))
			self.init_with_chapter = True
		else:
			self.page = BeautifulSoup(self.open_url(url))
			self.init_with_chapter = False

	# Returns the series page for an individual chapter URL. Useful for scraping series metadata for an individual chapter.
	def chapter_series(self, url):
		series_url = re.match(r'(.*kissmanga\.com/Manga/.*)/.*', url, flags=re.IGNORECASE).group(1)
		return series_url

	# Returns a dictionary containing chapter number, chapter name and chapter URL.
	def chapter_info(self, chapter_data):
		chapter = BeautifulSoup(str(chapter_data))
		chapter_url = 'http://kissmanga.com' + chapter.a['href']
		chapter_number = re.search(r'{} (Ch\.)?([0-9\-]*).*'.format(self.series_info('title')), chapter.a.text).group(2)

		try:
			chapter_name = re.search(r'.*: (.*)', chapter.a.text).group(1)
		except AttributeError:
			chapter_name = None

		return {"chapter": chapter_number, "name": chapter_name, "url": chapter_url}

	# Returns the image URL for the page.
	def chapter_images(self, chapter_url):
		image_list = []

		page = BeautifulSoup(self.open_url(chapter_url.encode('ascii', 'ignore').decode('utf-8')))
		scripts = page.find("div", {"id": "containerRoot"}).find_all('script')
		for script in scripts:
			if re.search(r'lstImages', script.text):
				for match in re.findall(r'lstImages\.push\(".*"\);', script.text):
					image_list.append(re.search(r'lstImages\.push\("(.*)"\);', match).group(1))
				break

		return image_list

	# Function designed to create a request object with correct headers, open the URL and decompress it if it's gzipped.
	def open_url(self, url):
		req = urllib.request.Request(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept-encoding': 'gzip'})
		response = urllib.request.urlopen(req)

		if response.info().get('Content-Encoding') == 'gzip':
			buf = io.BytesIO(response.read())
			data = gzip.GzipFile(fileobj=buf, mode="rb")
			return data
		else:
			return reponse.read()

	def series_chapters(self, all_chapters=False):
		chapter_row = self.page.find("table", {"class": "listing"}).find_all("tr")[2:]
		chapters = []
		for chapter in chapter_row:
			chapters.append(self.chapter_info(chapter))

		# If the object was initialized with a chapter, only return the chapters.
		if self.init_with_chapter == True and all_chapters == False:
			for chapter in chapters:
				if self.url == chapter["url"]:
					return [chapter]

		return chapters

	def series_info(self, search):
		def title():
			return self.page.find("a", {"class":"bigChar"}).text

		def description():
			description = self.page.find("div", {"class":"barContent"}).find_all("div")[1].find_all("div")[0].text
			return description.strip('\n')

		def author():
			return self.page.select('a[href*="/AuthorArtist/"]')[0].text.title()

		options = {"title": title, "description": description, "author": author}
		return options[search]()
