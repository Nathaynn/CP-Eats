from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from typing import List, Dict
import re
import requests 

# Custom Error for my own exceptions
class CustomError(Exception):
    """Custom exception class."""
    pass

# Set up chrome drivers
service = Service(ChromeDriverManager().install())
opt = webdriver.ChromeOptions()
opt.add_argument("--log-level=1")

driver = webdriver.Chrome(service=service, options=opt)

# Website: https://dineoncampus.com/calpoly/whats-on-the-menu


url_items = "http://localhost:1337/items/"
url_location = "http://localhost:1337/locations/"
headers = {
    "Content-Type": "application.json"
}

# Return a list of venues with their respective stores
def get_venues_and_stores(driver: webdriver) -> List[Dict[str, List[str]]]:
    driver.get("https://dineoncampus.com/calpoly/whats-on-the-menu")
    sleep(10)
    venues = []

    venue_elements = driver.find_element(By.ID, "menu-location-selector")
    venue_elements = venue_elements.find_elements(By.CSS_SELECTOR, "ul > li > header")
    stores = driver.find_element(By.ID, "menu-location-selector").find_elements(By.CSS_SELECTOR, "ul > li > ul")

    for i in range(len(venue_elements)):
        try:
            ven_stores = []
            venue = venue_elements[i].get_attribute('innerHTML')
            ven_stores = stores[i].find_elements(By.TAG_NAME, "li")
            ven_stores = map(lambda x: x.find_element(By.TAG_NAME, "button").get_attribute("innerHTML").strip(), ven_stores)
            venues.append({venue : list(ven_stores)})
        except:
            print(i.get_attribute("outerHTML"))

    return venues   

def get_foods(venue: str, driver: webdriver) -> List[Dict[str, str]]:
    driver.get("https://dineoncampus.com/calpoly/whats-on-the-menu")
    sleep(10)

    venue_elements = driver.find_element(By.ID, "menu-location-selector")
    venue_elements = venue_elements.find_elements(By.CSS_SELECTOR, "ul > li > header")
    stores = driver.find_element(By.ID, "menu-location-selector").find_elements(By.CSS_SELECTOR, "ul > li > ul")
    food_list = []

    for i in range(len(venue_elements)):
        if venue == venue_elements[i].get_attribute("innerHTML"):
            ven_stores = stores[i].find_elements(By.TAG_NAME, "li")
            for j in range(len(ven_stores)):
                ActionChains(driver).click(driver.find_element(By.ID, "menu-location-selector").find_element(By.TAG_NAME, "button")).perform()
                sleep(1)
                ActionChains(driver).click(ven_stores[j]).perform()
                store_name = ven_stores[j].find_element(By.TAG_NAME, "button").get_attribute("innerHTML").strip()
                sleep(6)

                try:
                    tab_times = driver.find_element(By.CSS_SELECTOR, "[role='tablist']").find_elements(By.TAG_NAME, "li")
                except:
                    tab_times = None

                if tab_times:
                    for r in tab_times:
                        print(len(tab_times))
                        ActionChains(driver).click(r).perform()
                        sleep(3)
                        food_tables = driver.find_element(By.CSS_SELECTOR, "[role='tabpanel']").find_elements(By.CSS_SELECTOR, "div > div:not(.row) > div > div > table")
                        for n in food_tables:
                            foods = n.find_elements(By.CSS_SELECTOR, "tbody > tr ")
                            print(len(food_tables))
                            for m in foods:
                                nt = m.find_element(By.CSS_SELECTOR, "td > div > span > div > button")
                                food_name = m.find_element(By.CSS_SELECTOR, "td > div > span > strong").get_attribute("innerHTML").strip()
                                calories = m.find_element(By.CSS_SELECTOR, "[aria-colindex='3'] > div").get_attribute("innerHTML").strip()  
                                portion = m.find_element(By.CSS_SELECTOR, "[aria-colindex='2'] > div").get_attribute("innerHTML").strip()  

                                ActionChains(driver).click(nt).perform()
                                sleep(3)

                                try:
                                    fat = driver.find_element(By.XPATH, "//li[strong[contains(text(), 'Total Fat')]]")
                                    match = re.search(r'Total Fat.*?(\d+)', fat.get_attribute("innerHTML"))
                                    if match:
                                        fat = match.group(1)
                                    else: 
                                        raise CustomError("Nutrition Facts not Valid!")

                                    carbs = driver.find_element(By.XPATH, "//li[strong[contains(text(), 'Total Carbohydrates')]]")
                                    match = re.search(r'Total Carbohydrates.*?(\d+)', carbs.get_attribute("innerHTML"))
                                    if match:
                                        carbs = match.group(1)
                                    else: 
                                        raise CustomError("Nutrition Facts not Valid!")

                                    
                                    protein = driver.find_element(By.XPATH, "//li[strong[contains(text(), 'Protein')]]")
                                    match = re.search(r'Protein.*?(\d+)', protein.get_attribute("innerHTML"))
                                    if match:
                                        protein = match.group(1)
                                    else: 
                                        raise CustomError("Nutrition Facts not Valid!")
                                except Exception as e:
                                    fat = 0
                                    carbs = 0
                                    protein = 0
                                    print(e)

                                ActionChains(driver).click(driver.find_element(By.CSS_SELECTOR, "[aria-label='Close']")).perform()
                                x = {"name" : food_name, "portion" : portion, "calories": calories, "fat" : fat, "carbs": carbs, "protein": protein, "venue": venue, "store": store_name}
                                if (x["venue"] == "1901 Marketplace"):
                                    location_payload = {
                                        "venue_id": 1,
                                        "name": x["store"],
                                        "address": "N"
                                    }
                                elif (x["venue"] == "Vista Grande"):
                                    location_payload = {
                                        "venue_id": 2,
                                        "name": x["store"],
                                        "address": "N"
                                    }
                                elif (x["venue"] == "Poly Canyon Village"):
                                    location_payload = {
                                        "venue_id": 3,
                                        "name": x["store"],
                                        "address": "N"
                                    }
                                response_location = requests.post(url_location, json=location_payload)
                                if response_location.ok:
                                    print("Success:", response_location.json())
                                
                                response_id = requests.post(url_location + "getId/", json={"name" : x["store"]})
                                if response_id.ok:
                                    print("Success:", response_id.json())
                                else:
                                    print("Failed:", response_id.status_code, response_id.text)
                                food_payload = {
                                    "location_id": response_id.json().get("id"),
                                    "item_name": x["name"],     
                                    "calories": int(x["calories"]),  
                                    "protein": int(x["protein"]),    
                                    "fat": int(x["fat"]),            
                                    "carbs": int(x["carbs"])         
                                }
  
                                response_food = requests.post(url_items, json=food_payload)
                                if response_food.ok:
                                    print("Success:", response_food.json)
                                else:
                                    print(x)
                                    print("Failed:", response_food.status_code, response_food.text)
                                sleep(1)


# 1901: ID = 1
get_foods("1901 Marketplace", driver)

# Vista Grande: ID = 2
get_foods("Vista Grande", driver)

# PCV: ID = 3
get_foods("Poly Canyon Village", driver)
