from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains


from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from typing import List, Dict
import re

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
                        ActionChains(driver).click(r).perform()
                        sleep(3)
                        food_tables = driver.find_element(By.CSS_SELECTOR, ".tab-pane.active").find_elements(By.CSS_SELECTOR, "div > div:not(.row):not(.menu-period-dropdowns) > div")
                        for n in food_tables:
                            foods = n.find_elements(By.CSS_SELECTOR, "div > table > tbody > tr ")
                            
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
                                print({"name" : food_name, "portion" : portion, "calories": calories, "fat" : fat, "carbs": carbs, "protein": protein, "venue": venue, "store": store_name})
                                food_list.append({"name" : food_name, "portion" : portion, "calories": calories, "fat" : fat, "carbs": carbs, "protein": protein, "venue": venue, "store": store_name})
                                sleep(1)

                
get_foods("1901 Marketplace", driver)
