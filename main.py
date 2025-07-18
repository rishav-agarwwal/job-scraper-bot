import csv
import time
from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT_FILE = "jobs.csv"
KEYWORDS = ["python", "automation", "data", "implementation", "analyst", "intern"]

def clean_text(text):
    return ' '.join(text.strip().split())

def keyword_match(text):
    text_lower = text.lower()
    return ', '.join([kw for kw in KEYWORDS if kw in text_lower])

def write_csv(jobs):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Job Title", "Company", "Location", "Apply Link", "Source", "Keywords Matched"])
        for job in jobs:
            writer.writerow(job)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(options=chrome_options)

def scrape_internshala():
    print("[*] Scraping Internshala...")
    jobs = []
    driver = setup_driver()
    url = "https://internshala.com/internships/keywords-python%20automation%20data"
    driver.get(url)

    try:
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CLASS_NAME, "individual_internship"))
        )
    except Exception as e:
        print("[!] Timed out waiting for Internshala job cards:", e)
        driver.quit()
        return jobs

    job_cards = driver.find_elements(By.CLASS_NAME, 'individual_internship')
    print(f"[Internshala] Found {len(job_cards)} job cards")

    for card in job_cards:
        try:
            title = card.find_element(By.CLASS_NAME, 'job-title-href').text
            company = card.find_element(By.CLASS_NAME, 'company-name').text
            location = card.find_element(By.CLASS_NAME, 'locations').find_element(By.TAG_NAME, 'a').text
            stipend = card.find_element(By.CLASS_NAME, 'stipend').text
            link = card.find_element(By.CLASS_NAME, 'job-title-href').get_attribute('href')
            kw = keyword_match(title)
            jobs.append([title, company, location, link, "Internshala", kw])
        except:
            continue

    driver.quit()
    return jobs

def scrape_wellfound(driver):
    print("[*] Scraping Wellfound...")
    jobs = []
    url = "https://wellfound.com/jobs"
    
    try:
        driver.get(url)
        print("[Wellfound] Waiting for job cards to load...")
        
        # Adjusting wait and using more robust logging
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.styles_component__n5n3W"))
            )
            print("[Wellfound] Job cards loaded.")
        except Exception as e:
            print(f"[Wellfound] Error waiting for job cards to load: {e}")
            return jobs  # Exit early if we can't find job cards
        
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.styles_component__n5n3W")
        
        if not job_cards:
            print("[Wellfound] No job cards found on the page.")
        
        for card in job_cards:
            try:
                # Extract job title
                title = card.find_element(By.CSS_SELECTOR, "a").text
                
                # Extract company name
                company = card.find_element(By.CLASS_NAME, "styles_name__ftDd0").text
                
                # Extract location
                location = card.find_element(By.CLASS_NAME, "styles_location__rYf3W").text
                
                # Extract job link
                link = "https://wellfound.com" + card.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                # Apply keyword match
                kw = keyword_match(title)
                
                # Append job data to the list
                jobs.append([clean_text(title), company, location, link, "Wellfound", kw])

            except Exception as e:
                print(f"[Wellfound] Error parsing a job card: {e}")
                continue  # Skip this job card and continue with the rest

        print(f"[Wellfound] Found {len(jobs)} jobs.")
        
    except Exception as e:
        print(f"[Wellfound] Failed to scrape Wellfound: {e}")
    
    return jobs

def parse_himalayas(soup):
    print("[*] Parsing Himalayas...")
    jobs = []
    job_cards = soup.find_all("article", class_="flex flex-shrink-0 cursor-pointer flex-col items-start")
    print(f"[Himalayas] Found {len(job_cards)} article tags")
    for card in job_cards:
        title_tag = card.find("a", class_="text-xl font-medium text-gray-900")
        if not title_tag:
            continue
        title = title_tag.text.strip()
        link = "https://www.himalayas.app" + title_tag['href'].strip()
        company_tag = card.find("a", href=lambda href: href and href.startswith("/companies/"))
        company = company_tag.text.strip() if company_tag else None
        jobs.append([title, company, "Remote", link, "Himalayas", keyword_match(title)])
    print(f"[Himalayas] Parsed {len(jobs)} jobs")
    return jobs

def main():
    driver = setup_driver()
    all_jobs = []
    all_jobs += scrape_internshala()
    #all_jobs += scrape_wellfound(driver)
    #driver.get("https://www.himalayas.app/jobs")
    time.sleep(3)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    #all_jobs += parse_himalayas(soup)
    driver.quit()
    print(f"[+] Scraped {len(all_jobs)} jobs. Writing to CSV...")
    write_csv(all_jobs)
    print(f"[✔] Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
