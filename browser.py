from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import timedelta
from textwrap import dedent
from hoshino import Service, MessageSegment, util, logger

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--mute-audio")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-extensions")
options.add_argument("--log-level=1")
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')

driver1 = None

def init_browser():
    global driver1
    logger.info('初始化Selenium ...')
    driver1 = webdriver.Chrome(chrome_options=options)

def browser_yituliu():
    global driver1
    if not driver1:
        init_browser()
    url = f'https://ark.yituliu.site'
    logger.info(f"akgacha-yituliu: {url}")
    driver = driver1
    driver.set_window_size(960, 800)

    driver.get(url)
    element = driver

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, 'level_card14'))
    )
    driver.execute_script(dedent("""
        document.querySelector('#shop_center').remove()
        document.querySelector('#act_store').remove()
        document.querySelector('#all_material').remove()
        var text = '本页内数值由明日方舟素材获取一图流进行计算，' + document.querySelector('#extra').children[0].lastChild.lastChild.textContent
        document.querySelector('#extra').remove()
        document.querySelector('#foot_main').remove()
        document.querySelector('#foot_warning_text').textContent = text
        document.querySelector('#level_t2_content').remove()
        document.body.style.fontFamily = 'Bahnschrift, sans-serif'
    """))
    logger.info("akgacha-yituliu: 截图中")
    msg = driver.get_screenshot_as_base64()
    logger.info(f"akgacha-yituliu: Complete.")
    return msg

