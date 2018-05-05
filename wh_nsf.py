from pyspider.libs.base_handler import *
import pymongo


class Handler(BaseHandler):

    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',

        },
        'proxy': 'http://127.0.0.1:1087',
        'cookies': {'__cfduid': 'd49ab44db0592abad43db99a19fcff8a21524841610',
                    ' _ga': 'GA1.2.1557020976.1524842180',
                    ' remember_82e5d2c56bdd0811318f0cf078b78bfc': 'eyJpdiI6Ik1GV3pnWkF5eHVvbzdFZG1FZlwvZTBNajV4bUdHU1N5ZU9acUhJQU9uUzhNPSIsInZhbHVlIjoiUlZzbnhrRE5qdldoNTRPaVZtYWdmQmN4b2Z6bEhFNnM4N002SHk1MHdudXE3S1ZGWFZ5STVkYmpzV1ZaRTJ4UU9BT2xwelFqdHZZWjhQVnJwbldBbEdIcWV6QkNtaXowSWRJUG50azNhUG11NllQeUI2YUlLQkJMK0V6N25wUjciLCJtYWMiOiI1NTg2YWM2YzY0ZjY4ZjhiMjRmMWZjZjRiMzA4NjRkZjg3ODM5YzYxNzQ2NmE0YTQ0MDYxMzc3N2QwYjdlM2I4In0%3D',
                    ' wallhaven_session': 'eyJpdiI6Ik0rTVpqYzhjSXRhdTlSVHVrS3RcL1FuZ1wvQUt1d3p2bllcL3BrY3VQMmFcL0N3PSIsInZhbHVlIjoiY0YrR3A3RGU5TVRhNTVHenFtVmEyNytHSktLVWpXalhiR09qK2ExYlwvVUdyaVllNGs3akRXVElNTmQxaWp0VnZMRUhoTkNCWG13eE5QR244ZzNPM2V3PT0iLCJtYWMiOiIxZWNmMTIyOTY1YzgzOTVjMTQ1ZmUxZTFiZDBkYjZmY2E5MGY1Y2JiOTNmY2Q2OGM1NDhhNGVjOWNkMzRiMDdlIn0%3D'},
        'itag': 'v1.0',

    }
    DIR_PATH = '/Users/sam/Pictures/wh/nsf'

    @every(minutes=7 * 24 * 60)
    def on_start(self):
        self.crawl('https://alpha.wallhaven.cc/search?q=&categories=111&purity=001&sorting=favorites&order=desc',
                   callback=self.index_page)

    @config(age=6 * 24 * 60 * 60)
    def index_page(self, response):

        for i, each in enumerate(response.doc('#thumbs li > figure.thumb').items()):
            u = each('a.preview').attr('href')
            self.crawl(u, callback=self.detail_page)

        for each in response.doc('ul.pagination a').items():
            self.crawl(each.attr('href'), callback=self.index_page)

    @config(age=6 * 24 * 60 * 60)
    def detail_page(self, response):
        item = {}
        item['url'] = response.url
        item['code'] = item['url'].split('/')[-1]
        item['favs'] = int(response.doc(
            'dt:contains("Favorites") + dd').text().replace(',', ''))
        item['views'] = int(response.doc(
            'dt:contains("Views") + dd').text().replace(',', ''))
        item['tags'] = self.list_from_doc(response, '#tags a.tagname')
        item['category'] = response.doc('dt:contains("Category") + dd').text()
        item['purity'] = response.doc(
            '#wallpaper-purity-form [checked="checked"] + label').text()
        item['src'] = response.doc('#wallpaper').attr('src')
        item['fname'] = '%05d' % item['favs'] + '-' + item['purity'] + \
            '-' + '%07d' % int(item['code']) + '-' + \
            '-'.join(item['tags']) + '.' + item['src'].split('.')[-1]
        if item['favs'] >= 30:
            self.crawl(item['src'], callback=self.save_img, save={
                       'file_name': item['fname'], 'dir_path': self.DIR_PATH})
        return item

    def list_from_doc(self, response, docs):
        return [i.text() for i in response.doc(docs).items()]

    @config(priority=3)
    def save_img(self, response):
        content = response.content
        dir_path = response.save['dir_path']
        file_name = response.save['file_name']
        file_path = dir_path + '/' + file_name
        f = open(file_path, 'wb')
        f.write(content)
        f.close()

    def on_result(self, result):
        super().on_result(result)
        client = pymongo.MongoClient()
        db = 'wh'
        collection = 'full'
        col = client[db][collection]
        if result:
            col.update_one({'code': result['code']}, {
                           '$setOnInsert': result}, upsert=True)
