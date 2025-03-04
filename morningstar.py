import os, json
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
from utils import CrawlerUtil
from pybeans.utils import get_cached_file

NAME = 'ms'
CODE = 'F0000004AI'
CU = CrawlerUtil(NAME)

BASE_URL = 'https://www.morningstar.cn/quicktake/'
REG_CMD = r'\?command=(\w+)&'
expected_apis = (
        'banchmark', 
        'fee', 
        #'agency',
        'portfolio',
        'manage',
        'dividend',
        #'report',
        'return',
        'performance',
        'rating',
        #'samefund'
    )

def scrape_ms_fund(code):
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
        
        try:
            TARGET_URL = f"{BASE_URL}{code}"
            HTML_FILE = f"./.cache/{NAME}_{code}.html"
            JSON_FILE = f"./.cache/{NAME}_{code}.json"
            if CU.env()!='prod' and get_cached_file(HTML_FILE):
                CU.debug(f'Use cached file {HTML_FILE}')
                with open(HTML_FILE, "r", encoding="utf-8") as file:
                    html_content = file.read()
                
                CU.debug(f'Use cached file {JSON_FILE}')
                with open(JSON_FILE, "r", encoding="utf-8") as file:
                    api_responses = json.load(file)
            else:
                page = context.new_page()
                # 存储 API 数据的列表
                api_responses = []

                def capture_api_response(response):
                    if "/handler/quicktake.ashx?command" in response.url and response.status == 200:
                        cmd = CU.extract_str(REG_CMD, response.url)
                        if cmd in expected_apis:
                            CU.debug(f"Captured API response = {cmd}")
                            response_text = response.text()
                            api_responses.append({
                                "url": response.url,
                                "data": json.loads(response_text)
                            })

                page.on("response", capture_api_response)
                CU.debug(f"Going to {TARGET_URL}")
                # 导航到目标页面
                page.goto(TARGET_URL, timeout=60000)
                
                while len(api_responses) < len(expected_apis):
                    page.wait_for_timeout(100)  # 避免忙等待，适当暂停

                #CU.info(api_responses)
                
                # 将 HTML 保存到文件
                CU.debug(f"Cached JSON in: {JSON_FILE}")
                with open(JSON_FILE, "w", encoding="utf-8") as file:
                    json.dump(api_responses, file, ensure_ascii=False, indent=4)

                # 获取整个页面的 HTML 源代码
                html_content = page.content()
                
                # 将 HTML 保存到文件
                CU.debug(f"Cached HTML in: {HTML_FILE}")
                with open(HTML_FILE, "w", encoding="utf-8") as file:
                    file.write(html_content)
        
        except Exception as e:
            CU.exception(e)
            print(f"抓取失败: {str(e)}")
            return []
        
        finally:
            # 关闭浏览器
            context.close()
            browser.close()

if __name__ == "__main__":
    scrape_ms_fund(CODE)