from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import time
import random
import json
import pandas as pd

# Cấu hình Chrome Options
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Safari/537.36")

# Chỉ định đường dẫn đến ChromeDriver
driver_path = "/usr/local/bin/chromedriver"
driver = uc.Chrome(options=options, driver_executable_path=driver_path, headless=False)

base_url = "https://batdongsan.com.vn"
link_base = base_url + "/nha-dat-ban-ha-noi/p"

# final data
listings = []

# convert trieu sangty
def convert_price_to_billion(price_str):
    try:
        price_str = price_str.replace(" ", "").lower()
        if "tỷ" in price_str:
            price_value = float(price_str.replace("tỷ", "").replace(",", "."))
            return price_value
        elif "triệu" in price_str:
            price_value = float(price_str.replace("triệu", "").replace(",", ".")) / 1000
            return price_value
        else:
            return "N/A"
    except (ValueError, AttributeError):
        return "N/A"
# convert loai nha
def convert_home_type(text):
    try:
        text = text.strip()
        if text.startswith("Bán "):
            text = text[4:]
        if text.endswith(" tại Việt Nam"):
            text = text[:-13]
        return text.strip()
    except (AttributeError, TypeError):
        return "N/A"

try:
    for i in range(1, 2):
        link = link_base + str(i)
        print(f"crawl page: {link}")
        driver.get(link)

        try:
            elements = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "re__card-config.js__card-config"))
            )
            listing_data = []
            for element in elements:
                try:
                    #price
                    price_tag = element.find_element(By.CLASS_NAME, "re__card-config-price.js__card-config-item").text
                    price = convert_price_to_billion(price_tag)

                    # S
                    area_tag = element.find_element(By.CLASS_NAME, "re__card-config-area.js__card-config-item").text
                    area_str = area_tag.replace("m²", "").replace(" ", "").strip()
                    area = float(area_str.replace(",", "."))

                    # price per S
                    try:
                        price_per_m2_tag = element.find_element(By.CLASS_NAME, "re__card-config-price_per_m2.js__card-config-item").text
                        price_per_m2_str = price_per_m2_tag.replace("tr/m²", "").replace(" ", "").strip()
                        price_per_m2 = float(price_per_m2_str.replace(",", "."))
                    except:
                        price_per_m2 = "N/A"

                    # ph ngu
                    try:
                        bedroom = element.find_element(By.CLASS_NAME, "re__card-config-bedroom.js__card-config-item").text
                    except:
                        bedroom = "N/A"

                    # nvs
                    try:
                        wc = element.find_element(By.CLASS_NAME,"re__card-config-toilet.js__card-config-item").text
                    except:
                        wc = "N/A"

                    # location
                    try:
                        card_info = element.find_element(By.XPATH, "./ancestor::div[@class='re__card-info']")
                        location_div = WebDriverWait(card_info, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "re__card-location"))
                        )
                        location_spans = location_div.find_elements(By.TAG_NAME, "span")
                        location = "N/A"
                        for span in location_spans:
                            span_text = span.text.strip()
                            span_class = span.get_attribute("class")
                            if "re__card-config-dot" not in span_class:
                                location = span_text
                                break
                    except Exception as e:
                        location = "N/A"

                    # link to   detail
                    try:
                        detail_link_tag = element.find_element(By.XPATH, "./ancestor::a[@class='js__product-link-for-product-id']")
                        detail_link_relative = detail_link_tag.get_attribute("href")
                        if detail_link_relative.startswith("http://") or detail_link_relative.startswith("https://"):
                            detail_link = detail_link_relative
                        else:
                            detail_link_relative = detail_link_relative.lstrip('/')
                            detail_link = f"{base_url}/{detail_link_relative}"
                    except:
                        detail_link = None

                    listing_data.append({
                        "page": i,
                        "price": price,
                        "area": area,
                        "price_per_m2": price_per_m2,
                        "bedroom": bedroom,
                        "wc": wc,
                        "location": location,
                        "detail_link": detail_link
                    })

                except Exception as e:
                    continue

            # duyet qya tung trang chi tiet de lay cac thong tin bi an o ds
            for data in listing_data:
                legal_status = "N/A" #pphap ly
                furniture = "N/A"      #noi that

                if data["detail_link"]:
                    try:
                        driver.get(data["detail_link"])

                        # chờ thẻ chưa tt xh
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "re__pr-other-info-display"))
                        )

                        # lay all
                        specs_items = driver.find_elements(By.CLASS_NAME, "re__pr-specs-content-item")
                        for item in specs_items:
                            legal_status = 'N/A'
                            furniture = 'N/A'
                            title = item.find_element(By.CLASS_NAME, "re__pr-specs-content-item-title").text
                            value = item.find_element(By.CLASS_NAME, "re__pr-specs-content-item-value").text

                            if title == "Pháp lý":
                                legal_status = value
                            elif title == "Nội thất":
                                furniture = value
                        try:
                            link_se_tag = driver.find_element(By.CLASS_NAME, "re__link-se")
                            link_se_title = link_se_tag.get_attribute("title")
                            home_type = convert_home_type(link_se_title)
                        except:
                            link_se_title = "N/A"
                            home_type = "N/A"

                        data["legal_status"] = legal_status
                        data["furniture"] = furniture
                        data["home_type"] = home_type
                        listings.append(data)

                        print(f"Tin đăng: {data}")
                        time.sleep(random.uniform(1, 3))

                    except Exception as e:
                        data["legal_status"] = "N/A"
                        data["furniture"] = "N/A"
                        data["home_type"] = "N/A"
                        listings.append(data)
            # delay ngau nhien
            time.sleep(random.uniform(3, 7))

        except Exception as e:
            print(f"lỗi tải trag {i}: {e}")

finally:
    # close browser
    driver.quit()

df = pd.DataFrame(listings)
df = df.drop(columns=['detail_link'])
df.to_csv('real_estate_listings.csv', index=False, encoding='utf-8-sig')
