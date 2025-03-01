from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re, time
from lxml import etree
from utils import CrawlerUtil

NAME = 'dytt8'
CU = CrawlerUtil(NAME)
OUTPUT_FILE = f"./cache/{NAME}_list.html"
MOVIE_FILE = f"./cache/{NAME}_movie.html"

# 配置参数
BASE_URL = "https://dy2018.com"
TARGET_URL = f"{BASE_URL}/html/gndy/dyzz/index.html"
#TARGET_URL = f"https://dy2018.com"
XPATH_LINKS = '//div[@id="header"]/div[@class="contain"]//div[@class="co_content8"]/ul//table'
XPATH_DESCRIPTION = '//div[@id="Zoom"]'

IMDB_SCORE = 7.0
DOUBAN_SCORE = 7.3

# regex pattens
regex_dict = {
    'imdb': re.compile(r'◎IMDb评分\s+(\d+\.?\d*)/(\d+) from ([\d,]+) users', flags=re.IGNORECASE),
    'douban': re.compile(r'◎豆瓣评分\s+(\d+\.?\d*)/(\d+) from ([\d,]+) users'),
    #'datetime': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'),
    'title_cn': re.compile(r'◎译\s+名\s+(.*)'),
    #'title_en': re.compile(r'◎片\s+名\s+(.*)'),
    #'country': re.compile(r'◎产\s+地\s+(.*)'),
    'category': re.compile(r'◎类\s+别\s+(.*)'),
    'show_date': re.compile(r'◎上映日期\s+(\d{4}-\d{2}-\d{2})'),
    'desc': re.compile(r'◎简\s+介\s+([^◎【】]+)')
}
# reg for movie list
title_en_reg = re.compile(r'◎片\s+名\s+([^◎]+)')
country_reg = re.compile(r'◎产\s+地\s+([^◎]+)')
movies = []

def scrape_movie_links():
    with sync_playwright() as p:
        # 启动浏览器（配置反检测参数）
        browser = p.chromium.launch(
            headless=CU.env()=='prod',
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        
        # 创建浏览器上下文（模拟正常用户环境）
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.new_page()
        
        try:
            CU.debug(f"Going to {TARGET_URL}")
            # 导航到目标页面
            page.goto(TARGET_URL, timeout=60000)
            
            # 等待主要内容加载
            page.wait_for_selector(XPATH_LINKS, state="attached", timeout=30000)
            
                  # 获取整个页面的 HTML 源代码
            html_content = page.content()
            
            # 将 HTML 保存到文件
            with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
                file.write(html_content)
            
            CU.debug(f"页面 HTML 已成功保存到: {OUTPUT_FILE}")
        
            list_tree = etree.HTML(html_content)
            table_sel = list_tree.xpath(XPATH_LINKS)
            
            for movie_sel in table_sel:
                link = movie_sel.xpath('.//a/@href')[0]
                content = movie_sel.xpath('.//td[@colspan="2"]/text()')[0]
                content = content   \
                    .replace('\r', '') \
                    .replace(u'\u3000', ' ')
                #CU.debug(link)
                #CU.debug(content)
                
                imdb = float(CU.extract_str(regex_dict['imdb'], content, '-1'))
                douban = float(CU.extract_str(regex_dict['douban'], content, '-1'))
                #CU.debug(f'imdb:{imdb}, douban:{douban}')
                title_en = CU.extract_str(title_en_reg, content)
                country = CU.extract_str(country_reg, content)
                if (imdb > 0 and imdb < IMDB_SCORE) or (douban > 0 and douban < DOUBAN_SCORE):
                    CU.debug(f'跳过低分电影:{title_en}, imdb:{imdb}, douban:{douban}')
                    continue
                else: ## 高分电影，或没有评分，则打开详情页面
                    movie = dict(title_en=title_en, country=country, link=link)
                    #CU.debug(title_en.encode('raw_unicode_escape'), country.encode('raw_unicode_escape'))
                    new_page = context.new_page()
                    new_page.goto(urljoin(BASE_URL, link), timeout=60000)
                    new_page.wait_for_selector(XPATH_DESCRIPTION, state="attached", timeout=30000)
                            
                        # 获取整个页面的 HTML 源代码
                    html_content = new_page.content()
                    
                    # 将 HTML 保存到文件
                    with open(MOVIE_FILE, "w", encoding="utf-8") as file:
                        file.write(html_content)
                    #CU.debug(f"页面 HTML 已成功保存到: {MOVIE_FILE}")
                    movie_tree = etree.HTML(html_content)
                    
                    content_list = movie_tree.xpath('//div[@id="Zoom"]//text()')
                    if not content_list:
                        return None
                    content = '\n'.join(content_list)   \
                        .replace('<br>', '\n') \
                        .replace('&nbsp;', ' ') \
                        .replace(u'\xa0', ' ') \
                        .replace(u'\u3000', ' ')
                    #CU.debug(content)
        
                    for key in regex_dict:
                        movie[key] = CU.extract_str(regex_dict[key], content)
                        
                    if not movie['imdb'] or not movie['douban']:
                        CU.debug(f'没有评分:{title_en}')
                        continue
                    imdb = float(movie['imdb'])
                    douban = float(movie['douban'])
                    if (imdb > 0 and imdb < IMDB_SCORE) or (douban > 0 and douban < DOUBAN_SCORE):
                        CU.debug(f'跳过低分电影:{title_en}, imdb:{imdb}, douban:{douban}')
                        continue
                    
                    CU.debug(f'跳过低分电影:{title_en}, imdb:{imdb}, douban:{douban}')
                    #movie['poster'] = movie_tree.xpath('//div[@id="Zoom"]//img/@src')
                    #movie['magnets'] = movie_tree.xpath('//div[@id="downlist"]//a/@href')
                    time.sleep(5)
                    new_page.close()
                    #CU.debug(movie)
                    movies.append(movie)
                    
            CU.info(movies)
            return movies
        
        except Exception as e:
            CU.exception(e)
            print(f"抓取失败: {str(e)}")
            return []
        
        finally:
            # 关闭浏览器
            context.close()
            browser.close()

if __name__ == "__main__":
    scrape_movie_links()