import mysql.connector
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

# Connect to MySQL database, here is an online database
# 连接到 MySQL 数据库,这里是线上数据库
db = mysql.connector.connect(
    host="your host",
    user="your user name",
    password="your password",
    database="your database name",
    charset='utf8mb4'
)
cursor = db.cursor()
cursor.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci';")

# 创建表的 SQL 语句
create_table_query = """
CREATE TABLE IF NOT EXISTS your table name (
    id INT AUTO_INCREMENT PRIMARY KEY,
    website VARCHAR(255),
    title VARCHAR(255),
    board VARCHAR(255),
    content TEXT,
    comment1 TEXT,
    comment2 TEXT,
    comment3 TEXT,
    comment4 TEXT,
    comment5 TEXT
)
"""
cursor.execute(create_table_query)

def run(playwright):
    browser = playwright.chromium.launch(headless=True,args=['--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'])
    context = browser.new_context()
    page = context.new_page()

    # Visit the forum homepage
    # 访问论坛首页
    base_url = "the base url"

    # The root URL of the forum can be retained if there is a need for URL concatenation at the end
    # 论坛根网址，如后面有网址拼接需要可保留
    url = "the root url"
    page.goto(base_url,timeout=600000)

    # initialize the variable
    # 初始化变量
    every_post_count = 0
    total_post_count = 0

    page.wait_for_load_state("load")

    # Use the query_delecter_all locator to locate all forum sections
    # 使用query_selector_all定位器，定位所有论坛板块
    categories = page.query_selector_all('Here need to fill')

    for category in categories:
        # Crawl the name and title of the post section
        # 爬取帖子板块名字
        board_text = category.query_selector('Here need to fill').query_selector('Here need to fill').text_content().strip().replace('\n', '').replace('\t', '')
        category_url = category.query_selector('Here need to fill').query_selector('Here need to fill').get_attribute("href")

        # URL stitching
        # 网址拼接
        full_category_url = urljoin(url, category_url)

        # Enter a certain section
        # 进入某个板块
        new_category_page = context.new_page()
        new_category_page.goto(full_category_url,timeout = 600000)

        while True:
            # Use the query_delecter_all locator to locate all posts on the current page in this forum section
            # 使用query_selector_all定位器，定位这个论坛板块中，当前页面的所有帖子
            titles = new_category_page.query_selector_all('Here need to fill')

            for title in titles:
                # Crawl post title
                # 爬取帖子标题
                title_text = title.query_selector('Here need to fill').text_content().strip().replace('\n', '').replace('\t', '')
                post_url = title.query_selector('Here need to fill').get_attribute("href")
                full_post_url = urljoin(url, post_url)
                new_page = context.new_page()
                new_page.goto(full_post_url,timeout = 600000)

                # Crawl post content
                # 爬取帖子内容
                contentAll = new_page.query_selector_all('Here need to fill')
                if len(contentAll) < 1:
                    # No Content
                    content = "无内容"
                else:
                    content = contentAll[0].text_content()

                # Crawl post comments
                # 爬取帖子评论
                comments = []
                if len(contentAll) == 1:
                    for i in range(5):
                        # No comments
                        comments.append("无评论")
                elif (len(contentAll) <= 6):
                    for i in range(1,len(contentAll)):       
                        comment = contentAll[i].text_content()
                        comments.append(comment)
                    for i in range(6 - len(contentAll)):
                        # No comments
                        comments.append("无评论")
                else:   
                    for i in range(1,6):
                        comment = contentAll[i].text_content()
                        comments.append(comment)

                select_query = "SELECT id FROM your table name WHERE title=%s AND board=%s"
                cursor.execute(select_query, (title_text, board_text))
                result = cursor.fetchone()
                if result:
                    # print("The post already exists, skip insertion")
                    print("帖子已存在，跳过插入。")
                else:
                    # Insert data into database
                    # 插入数据到数据库
                    insert_query = """
                    INSERT INTO your table name (website, title, board, content, comment1, comment2, comment3, comment4, comment5)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (url, title_text, board_text, content, comments[0], comments[1], comments[2], comments[3], comments[4]))
                    db.commit()

                    total_post_count += 1
                    # Crawl the data of the {total post count} th post
                    print(f'爬取第{total_post_count}篇帖子的数据')

                every_post_count += 1
                new_page.close()

                if every_post_count == len(titles):
                    # print("I have finished crawling the entire page and will automatically turn pages soon")
                    print("已爬完一整页,即将自动翻页")

            # The posts on the current page have been crawled, locate the Next button to move to the next page
            # 当前页面的帖子已爬取完毕，定位Next按钮到下一个页面
            if every_post_count == len(titles):
                if new_category_page.query_selector('Here need to fill'):
                    category_url = new_category_page.query_selector('Here need to fill').get_attribute("href")
                    full_category_url = urljoin(url, category_url)
                    new_category_page.goto(full_category_url,timeout=600000)
                    new_category_page.wait_for_timeout(10000)
                    every_post_count = 0
                else:
                    every_post_count = 0
                    break

        if total_post_count >= 1000:
            break

        new_category_page.close()

    # Close database connection
    # 关闭数据库连接
    cursor.close()
    db.close()

    browser.close()


with sync_playwright() as playwright:
    run(playwright)
