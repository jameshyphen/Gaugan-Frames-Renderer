import base64
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

import time
import asyncio
import queue
import os
"""

This script has been written by James Hyphen @ https://github.com/jameshyphen
in collaboration with Arthur Zwartjes for his Bachelor's on Deeplearning and movie making

Working hand-to-hand with Nvidia's Gaugan, which you can refer to here: http://nvidia-research-mingyuliu.com/gaugan/

"""


MAX_BROWSERS = 1  # TODO: Implement in the future multiple browsers
SEGMENT_QUEUE: queue.Queue = queue.Queue()
FOLDER = "01_test_GauGan"  # Folder in which your png frames are located.

def click_checkbox(checkbox: WebElement):
    print(f"The checkbox type is: {type(checkbox)}")
    checkbox.send_keys(Keys.SPACE)

def fill_queue():
    QUEUE = queue.Queue()
    for filename in os.listdir(FOLDER):
        if filename.endswith(".png"):
            QUEUE.put(os.path.join(FOLDER, filename))
        else:
            continue
    print(QUEUE.empty())
    return QUEUE

def set_style_filter(driver: WebDriver):
    for filename in os.listdir(FOLDER):
        if filename == "style_filter.png":
            pass
        else:
            default_style: WebElement = driver.find_element_by_id("example2")
            default_style.click()

def get_base64_canvas(driver):
    canvas: WebElement = driver.find_element_by_id("output")
    return driver.execute_script("return arguments[0].toDataURL('image/jpg').substring(21);", canvas)

def initialize_browser() -> WebDriver:
    print("Initializing Browser: Started")
    driver: WebDriver = webdriver.Chrome()
    driver.get("http://34.216.122.111/gaugan/")
    driver.maximize_window()
    checkbox = driver.find_element_by_id("myCheck")
    canvas_base64_base = get_base64_canvas(driver)
    click_checkbox(checkbox)
    print("Initializing Browser: Finished")
    set_style_filter(driver)
    while(not canvas_changed(canvas_base64_base, driver)):
        time.sleep(0.1)
    return driver

def decode_and_save_canvas_base64_as_jpg(canvas_base64, convert_path, image_name):
    canvas_jpg = base64.b64decode(canvas_base64)
    if not os.path.exists(convert_path):
        os.makedirs(convert_path)
    with open(f"{convert_path}/{image_name}.jpg", 'wb') as f:
        f.write(canvas_jpg)

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
    upload_button.click()
    convert_button: WebElement = driver.find_element_by_id("render")
    convert_button.send_keys(Keys.SPACE)
    while(not canvas_changed(canvas_base64_base, driver)):
        time.sleep(0.1)
    canvas_base64 = get_base64_canvas(driver)
    path, image_name_with_ext = image_path.split("/")
    image_name = image_name_with_ext.split(".")[0]
    convert_path = f"converted_{path}"
    decode_and_save_canvas_base64_as_jpg(canvas_base64, convert_path, image_name)



async def image_converter_service():
    print("Started image convert service: Started")
    driver = initialize_browser()
    print("Image convert service: Finished initializing browser")
    while not SEGMENT_QUEUE.empty():
        image_path = SEGMENT_QUEUE.get()
        await convert_image(driver, image_path)

async def main():
    tasks = []
    for _ in range(MAX_BROWSERS):
        tasks.append(image_converter_service())
    await asyncio.gather(*tasks)

SEGMENT_QUEUE = fill_queue()
asyncio.run(main())

