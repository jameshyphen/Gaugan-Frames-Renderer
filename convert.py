import base64
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
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

def initialize_browser() -> WebDriver:
    print("Initializing Browser: Started")
    driver: WebDriver = webdriver.Chrome()
    driver.get("http://34.216.122.111/gaugan/")
    driver.maximize_window()
    checkbox = driver.find_element_by_id("myCheck")
    click_checkbox(checkbox)
    print("Initializing Browser: Finished")
    set_style_filter(driver)
    return driver

async def convert_image(driver: WebDriver, image_path: str):
    abs_path = os.path.abspath(image_path)
    file_input: WebElement = driver.find_element_by_id("segmapfile")
    upload_button: WebElement = driver.find_element_by_id("btnSegmapLoad")
    print("Uploading")
    file_input.send_keys(abs_path)
    time.sleep(2)
    upload_button.click()
    print("Uploaded")
    convert_button: WebElement = driver.find_element_by_id("render")
    convert_button.send_keys(Keys.SPACE)
    print("Converting")
    time.sleep(5)
    canvas: WebElement = driver.find_element_by_id("output")
    print("Converted")
    path, image_name_with_ext = image_path.split("/")
    image_name = image_name_with_ext.split(".")[0]
    print(f"Path: {path}, Image_with_ext: {image_name_with_ext}, Image name: {image_name}")
    canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/jpg').substring(21);", canvas)
    canvas_jpg = base64.b64decode(canvas_base64)
    print("Decoding")
    convert_path = f"converted_{path}"
    if not os.path.exists(convert_path):
        os.makedirs(convert_path)
    with open(f"{convert_path}/{image_name}.jpg", 'wb') as f:
        f.write(canvas_jpg)



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

