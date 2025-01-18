import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from forex_python.converter import CurrencyRates
import json

import matplotlib.pyplot as plt

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

from selenium.webdriver.chrome.options import Options

import re
from rapidfuzz import fuzz
from urllib.parse import urljoin

# Function to normalize text
def normalize_title(title):
    title = title.lower()    # Convert to lowercase
    #title = re.sub(r'[^a-z\s]', '', title) # Remove special characters and digits
    return title

# Function to find similar titles using RapidFuzz
def find_similar_titles(title, title_list, threshold=75):
    similar_titles = []
    for other_title in title_list:
        # Compute similarity score between title and other title
        score = fuzz.ratio(title, other_title)
        if score >= threshold:
            similar_titles.append((title, other_title, score))
    return similar_titles

# Configure caching options
options = Options()
#options.add_argument("--headless")  # Run in headless mode (without opening a window)
#options.add_argument("--headless")  # Run in headless mode (without opening a window)
options.page_load_strategy = 'eager'

options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--enable-unsafe-swiftshader")  # Disable GPU hardware acceleration


options.add_argument("--disable-extensions")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,  # Block images
    "profile.managed_default_content_settings.stylesheets": 2,  # Block CSS
    "profile.managed_default_content_settings.fonts": 2,  # Block fonts
    "profile.managed_default_content_settings.plugins": 2,  # Block plugins
    "profile.managed_default_content_settings.popups": 2,  # Block popups
    "profile.managed_default_content_settings.notifications": 2,  # Block notifications
})

#Initialize the WebDriver with the options
driver = webdriver.Chrome(options=options)

with open('platformes.json', 'r') as file:
    sites = json.load(file)

# Headers to mimic a real browser and avoid bot detection
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "TE": "Trailers"
}

date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

currency_converter = CurrencyRates()

def convert_prix(the_prix, detected_currency="UNKNOWN"):
    # Convert prix to USD if necessary
    try:
        # Detect currency from the prix string
        if detected_currency == "UNKNOWN":
            if "USD" in the_prix or "$" in the_prix:
                detected_currency = "USD"
            elif "EUR" in the_prix or "€" in the_prix:
                detected_currency = "EUR"

        # Clean the prix string by removing currency symbols and unnecessary text
        cleaned_prix = (
            the_prix
            .replace("USD", "")
            .replace("current price: ", "")
            .replace("$", "")
            .replace("EUR", "")
            .replace("€", "")
            .replace("\xa0", "")
            .replace("–", "")
            .replace(",", "")
            .strip()
        )

        # Convert the cleaned string to a float
        try:
            cleaned_prix = next(float(part) for part in cleaned_prix.split() if part.replace('.', '', 1).isdigit())
        except StopIteration:
            return None  # Return None if no float is found

        # Convert EUR to USD if necessary
        if detected_currency == "EUR":
            cleaned_prix = currency_converter.convert("EUR", "USD", cleaned_prix)
            print(f"Converted prix: {cleaned_prix} USD")
        
        return cleaned_prix
        
    except Exception as e:
        print(f"Currency detection or conversion error: {e}")


def get_description(site):
    try:
        # Navigate to the product page
        driver.get(site["url"])

        html_content = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract the description using the provided CSS selector
        description_element = soup.select_one(site["description"])
        description = description_element.get_text(separator=' ', strip=True) if description_element else "Description not found"

        return description
    except Exception as e:
        print(f"Error fetching description for {site['url']}: {e}")
        return "Error fetching description"

# Function to collect data via scraping
def collect_data_from_scraping(site, products=None):
        
    driver.get(site["url"])
    # Allow time for the page to load
    #time.sleep(2)

    # Extract the fully rendered HTML
    html_content = driver.page_source

    print ("Opened : ",site["url"])
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    if products is None:
        products = []
    for item in soup.select(site["product_selector"]):
        nom =  item.select_one(site["nom_selector"])
        prix = item.select_one(site["prix_selector"])
        #cleaned_prix = convert_prix(the_prix, detected_currency)
        promotion = item.select_one(site["promotion_selector"]) if site.get("promotion_selector") else None
        
        if nom and prix:
            # Convert prix to USD if necessary
            the_prix = prix.text.strip()
            try:
                detected_currency = "UNKNOWN"  # Default currency if none detected

                # Detect currency from the prix string
                if "USD" in the_prix or "$" in the_prix:
                    detected_currency = "USD"
                elif "EUR" in the_prix or "€" in the_prix:
                    detected_currency = "EUR"
                elif "GBP" in the_prix or "£" in the_prix:
                    detected_currency = "GBP"

                # Clean the prix string by removing currency symbols and unnecessary text
                cleaned_prix = (
                    the_prix
                    .replace("USD", "")
                    .replace("current price: ", "")
                    .replace("$", "")
                    .replace("EUR", "")
                    .replace("€", "")
                    .replace("GBP", "")
                    .replace("£", "")
                    .replace("\xa0", "")
                    .replace("–", "")
                    .replace(",", "")
                    .strip()
                )

                # Convert the cleaned string to a float
                try:
                    cleaned_prix = next(float(part) for part in cleaned_prix.split() if part.replace('.', '', 1).isdigit())
                except StopIteration:
                    return None  # Return None if no float is found

                # Convert EUR to USD if necessary
                if detected_currency == "EUR":
                    cleaned_prix = currency_converter.convert("EUR", "USD", cleaned_prix)
                elif detected_currency == "GBP":
                    cleaned_prix = currency_converter.convert("GBP", "USD", cleaned_prix)

                    print(f"Converted prix: {cleaned_prix} USD")
            except Exception as e:
                print(f"Currency detection or conversion error: {e}")
            
            
            if promotion:
                promotion_text = promotion.text.strip()
            else:
                promotion_text = ""
            
            
            nomt = nom.text.strip()
            if site.get("nom_regex"):
                nomt = nomt.str.extract(site["nom_regex"])

            product_url = ""
            if 'href' in nom.attrs:
                product_url = nom['href']
                if product_url.startswith('/'):
                    product_url = urljoin(site["url"], product_url)  # Combine domain with path

            # Run description fetching concurrently
            description = get_description({"url": product_url, "description": site["description"]})
            
            products.append({
                "nom": nomt,
                "prix": cleaned_prix,
                "website": site["website"],
                "source": site["url"],
                "date_scraped": date_now,
                "category": site["category"],
                "promotion": promotion_text,
                "url": product_url,
                "description": description,
            })
            print ("append product : ",site["url"])
    
    if site.get("next_page"):
        print ("next_page")
        next_page = soup.select_one(site["next_page"])
        if next_page and 'href' in next_page.attrs:
            next_page_url = next_page['href']
            if next_page_url.startswith('/'):
                from urllib.parse import urljoin
                next_page_url = urljoin(site["url"], next_page_url)  # Automatically combines domain with path
            print(next_page_url)
            site["url"] = next_page_url
            collect_data_from_scraping(site, products)
    
    return products


# Function to collect data via API
def collect_data_from_api(site):
    response = requests.get(site["url"], headers=headers)  # Adding headers to the request
    
    if response.status_code == 200:
        data = response.json()
    
        products = []
        items = data.get(*site["selectors"]["product_key"].split('.'))
        
        for item in items:
            nom = item.get(site["selectors"]["nom_key"])
            prix = item.get(site["selectors"]["price_key"])
            category = item.get(site["selectors"]["category_key"])
            promotion = item.get(site["selectors"]["promotion_key"])
            
            if nom and prix:
            
                cleaned_prix = convert_prix(prix)
                
                products.append({
                    "nom": nom,
                    "prix": prix,
                    "website": site["website"],
                    "source": site["url"],
                    "date_scraped": date_now,
                    "category": category,
                    "promotion": promotion
                })
                print ("append : ",site["url"])
        
        return products
    else:
        print(f"API error: {response.status_code} {response.text}")
        return []


# Function to collect data from all sites
def collect_all_data():
    data = []
    for site in sites:
        try:
            if site["type"] == "scraping":
                result = collect_data_from_scraping(site)
                if result:  # Check if result is not None or empty
                    data.extend(result)
                    print ("Add : ",site["url"])
            elif site["type"] == "API":
                result = collect_data_from_api(site)
                if result:  # Check if result is not None or empty
                    data.extend(result)
        except Exception as e:
            print(f"Error processing site {site}: {e}")
            # Optionally, log the error or add the site to a list of failed sites
    return data


# Data cleaning function
def clean_data(raw_data):
    df = pd.DataFrame(raw_data)
    
    # Check if 'nom' exists in the columns
    if 'nom' not in df.columns:
        print("Error: 'nom' column is missing!")
        return df  # or return an empty dataframe
    
    #print(df.columns)  # To inspect the columns in the data
    
    # Safeguard the 'nom' column to ensure it contains strings
    df["nom"] = df["nom"].astype(str).str.replace(r"[,-]$|\(\)$|(?: - |, )?(Matte Black Steel|Copper|Slate|Brown|biscuit|Champagne|Tuscan stainless steel|Brushed Black|Brushed Navy|Carbon Graphite|Chrome|Forest Green|Graphite Steel|Ivory|Alpine White|Grey|Sapphire Blue|Specialty|Dark Steel|Essence White|Midnight Steel|Mirror|Satin Green|Silver Steel|Titanium|Beige & Bisque|Metallic|Red|Specialty|Black Slate|Black slate|Black Stainless|Multi-color|Black steel|Bronze|Nickel|Diamond Gray|Platinum Glass|Platinum|Graphite Steel|Graphite steel|Green|Orange|Yellow|Stainless steel look|Black stainless steel|Bisque|CleanSteel|Black Glass|Graphite|Slate|Matte Black|Matte black|Custom Panel Ready|Custom Panel Required|Custom Panel|Stainless Steel|SmudgeProof Stainless Steel|Smudge Proof Stainless Steel|White Glass|PrintShield Black Stainless Steel|Stainless Steel with Brushed Stainless Steel Handles|Stainless Steel|Stainless steel|Stainless Look|Matte Black with Brushed Stainless Steel Handles and Knobs|High Gloss White|White|Matte White|Matte white|Starlight|Space|Black|Blue|Gold|Gray|Green|Purple|Pink|Silver|Fingerprint Resistant Black Stainless Steel|Fingerprint Resistant Stainless Steel)", "", regex=True)




    # Drop duplicates based on selected columns
    df_cleaned = df.drop_duplicates(subset=["nom", "website", "date_scraped"], keep="first")
    
    # Continue with finding similar titles and further processing...
    #groups = []
    #seen = set()
    #
    #for idx, row in df.iterrows():
    #    if idx in seen:
    #        continue
    #    title = row["nom"]
    #    matches = find_similar_titles(title, df["nom"].tolist())
    #    
    #    if not matches:
    #        continue
    #    
    #    match_indices = [
    #        idx for idx, match in enumerate(df["nom"]) if (title, match, fuzz.ratio(title, match)) in matches
    #    ]
    #    
    #    if match_indices:
    #        groups.append(match_indices)
    #        seen.update(match_indices)
    #
    #rows_to_keep = set()
    #for group in groups:
    #    if group:
    #        min_prix_index = df.loc[group, "prix"].idxmin()
    #        rows_to_keep.add(min_prix_index)
    #
    #df_cleaned = df.loc[rows_to_keep].reset_index(drop=True)
    
    return df_cleaned

# Export cleaned data
def export_data(df, filename="Electromenagerscleaned_data.csv"):
    df.to_csv(filename, index=False)
    df.to_excel("Electromenagerscleaned_data.xlsx", index=False, engine="openpyxl")  # Using openpyxl for Excel support
    print(f"Data exported to '{filename}'")

# Main execution
if __name__ == "__main__":
    raw_data = collect_all_data()
    df_cleaned = clean_data(raw_data)
    
    try:
        old_data = pd.read_csv("Electromenagerscleaned_data.csv")  # Read the existing data from the file
        # Concatenate the cleaned data to the old data
        data_now = pd.concat([old_data, df_cleaned], ignore_index=True)
    except FileNotFoundError:
        # If the file doesn't exist, use the cleaned data as the initial dataset
        data_now = df_cleaned
        
    # Concatenate the cleaned data to the old data
    export_data(data_now)
    
    driver.quit()