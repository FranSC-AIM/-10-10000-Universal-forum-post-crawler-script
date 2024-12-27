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
    post_count = 0
    total_post_count = 0
    scroll_count = 0

    page.wait_for_load_state("load",timeout=150000)
    
    # Use the query_delecter_all locator to locate all forum sections
    # 使用query_selector_all定位器，定位所有论坛板块
    categories = page.query_selector_all("Here need to fill")

    for category in categories:
        post_count = 0
        title_url = category.get_attribute("href")

        # URL stitching
        # 网址拼接
        full_title_url = urljoin(url, title_url)

        # Enter a certain section
        # 进入某个板块
        new_category_page = context.new_page()
        new_category_page.goto(full_title_url,timeout=600000)
        new_category_page.wait_for_load_state("load",timeout=150000) 

        while True: 
            # Use the query_delecter_all locator to locate all posts on the current page in this forum section
            # 使用query_selector_all定位器，定位这个论坛板块中，当前页面的所有帖子
            titles = new_category_page.query_selector_all("Here need to fill")
            new_titles = titles[post_count:]

            # Scroll refresh, no new posts appear, jump out of the loop, enter the next section
            # 滚动刷新无新帖子出现，跳出循环，进入下个板块
            if len(new_titles)==0:
                break

            for title in new_titles:
                title_text = title.text_content()
                post_count += 1

                post_url = title.get_attribute("href")

                full_post_url = urljoin(url, post_url)
                new_page = context.new_page()
                new_page.goto(full_post_url,timeout=600000)

                new_page.wait_for_load_state("load",timeout=150000)

                if new_page.query_selector("Here need to fill"):
                    board_text = new_page.query_selector("Here need to fill").text_content()
                else:
                    # Not belonging to any sector
                    board_text = "不属于任何板块"

                # Crawl post content and comments
                # 爬取帖子内容
                contentAll = new_page.query_selector_all("Here need to fill")
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

                new_page.close()

            # Scroll and wait for new posts to load
            # 滚动和等待新帖子加载
            while scroll_count < 20:
                scroll_height = new_category_page.evaluate("() => document.body.scrollHeight")
                new_category_page.evaluate(f"() => window.scrollTo(0, {scroll_height})")

                # Scroll the {scroll_count} times
                print(f"滚动{scroll_count}次")
                scroll_count += 1
                
            scroll_count = 0

        
        post_count = 0
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