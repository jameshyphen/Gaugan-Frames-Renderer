import base64
from os import path
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

import time
import asyncio
import os

from typing import List
"""

This script has been written by James Hyphen @ https://github.com/jameshyphen
in collaboration with Arthur Zwartjes for his Bachelor's on Deeplearning and movie making

Working hand-to-hand with Nvidia's Gaugan, which you can refer to here: http://nvidia-research-mingyuliu.com/gaugan/

"""


MAX_BROWSERS = 1  # TODO: Implement in the future multiple browsers
FRAME_LIST: List[str] = []
FOLDER = "02_test_GauGan"  # Folder in which your png frames are located.

def click_checkbox(checkbox: WebElement):
    print(f"The checkbox type is: {type(checkbox)}")
    checkbox.send_keys(Keys.SPACE)

def filter_frame_list(frame_list: List[str]):
    RENDERED_FRAMES: List[str] = []
    path_convert = f"converted_{FOLDER}"
    if os.path.exists(path_convert):
        for filename in os.listdir(path_convert):
            if filename.endswith(".png"):
                RENDERED_FRAMES.append(os.path.join(FOLDER, filename))
            else:
                continue
        for rendered_frame in RENDERED_FRAMES:
            frame_list.remove(rendered_frame)
    return frame_list

def fill_frame_list():
    FRAME_ORDER = []
    for filename in os.listdir(FOLDER):
        if filename.endswith(".png"):
            FRAME_ORDER.append(os.path.join(FOLDER, filename))
        else:
            continue
    FRAME_ORDER.sort()
    return FRAME_ORDER

def set_style_filter(driver: WebDriver):
    for filename in os.listdir(FOLDER):
        if filename == "style_filter.png":
            pass
        else:
            default_style: WebElement = driver.find_element_by_id("example2")
            default_style.click()

def get_base64_canvas(driver):
    canvas: WebElement = driver.find_element_by_id("output")
    return driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)

def initialize_browser() -> WebDriver:
    print("Initializing Browser: Started")
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # TODO: Fix headless, for now it doesn't work. Crashes after first run.
    driver: WebDriver = webdriver.Chrome()
    driver.get("http://34.216.122.111/gaugan/")
    driver.maximize_window()
    checkbox = driver.find_element_by_id("myCheck")
    canvas_base64_base = get_base64_canvas(driver)
    click_checkbox(checkbox)
    print("Initializing Browser: Finished")
    set_style_filter(driver)
    t0 = time.time()
    t1 = time.time()
    while(
        not canvas_changed(canvas_base64_base, driver)
        and (t1-t0) < 20
    ):
        t1 = time.time()
        print(f"Initial render time: {t1-t0}")
        time.sleep(0.1)
    return driver

def decode_and_save_canvas_base64_as_png(canvas_base64, convert_path, image_name):
    canvas_png = base64.b64decode(canvas_base64)
    if not os.path.exists(convert_path):
        os.makedirs(convert_path)
    with open(f"{convert_path}/{image_name}.png", 'wb') as f:
        f.write(canvas_png)

def canvas_changed(base_canvas, driver):
    canvas = get_base64_canvas(driver)
    return base_canvas != canvas

async def convert_image(driver: WebDriver, image_path: str):
    canvas_base64_base = get_base64_canvas(driver)
    abs_path = os.path.abspath(image_path)
    file_input: WebElement = driver.find_element_by_id("segmapfile")
    upload_button: WebElement = driver.find_element_by_id("btnSegmapLoad")
    file_input.send_keys(abs_path)
    time.sleep(2)
    upload_button.send_keys(Keys.SPACE)
    convert_button: WebElement = driver.find_element_by_id("render")
    convert_button.send_keys(Keys.SPACE)
    print("RENDER BUTTON CLICKED")
    t0 = time.time()
    t1 = time.time()

    while(
        not canvas_changed(canvas_base64_base, driver)
        and (t1-t0) < 20
    ):
        t1 = time.time()
        print(f"Rendering time: {t1-t0}")
        time.sleep(0.1)

    canvas_base64 = get_base64_canvas(driver)
    path, image_name_with_ext = image_path.split("/")
    image_name = image_name_with_ext.split(".")[0]
    convert_path = f"converted_{path}"
    decode_and_save_canvas_base64_as_png(canvas_base64, convert_path, image_name)


async def image_converter_service():
    print("Started image convert service: Started")
    driver = initialize_browser()
    print("Image convert service: Finished initializing browser")
    while len(FRAME_LIST)>0:
        image_path = FRAME_LIST[0]
        FRAME_LIST.remove(image_path)
        await convert_image(driver, image_path)

async def main():
    tasks = []
    for _ in range(MAX_BROWSERS):
        tasks.append(image_converter_service())
    await asyncio.gather(*tasks)

FRAME_LIST = fill_frame_list()
FRAME_LIST = filter_frame_list(FRAME_LIST)
print(FRAME_LIST)
asyncio.run(main())
