#!/usr/bin/env python3
#import sys
#import os

# Ensure user-specific site-packages are included
#sys.path.append('/home/youssef/.local/lib/python3.8/site-packages')

import asyncio
import json
from datetime import datetime
from forex_python.converter import CurrencyRates
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from rapidfuzz import fuzz
from urllib.parse import urljoin

# Function to normalize text
def normalize_text(text):
    if isinstance(text, str):
        text = text.lower()  # Convert to lowercase
        # nom = re.sub(r'[^a-z\s]', '', text)  # Uncomment if needed for special character removal
        return text
    else:
        # Convert non-string inputs to a string or handle them appropriately
        return str(text) if text is not None else ""

# Function to find similar noms using RapidFuzz
def find_similar_noms(nom, nom_list, threshold=95):
    similar_noms = []
    for other_nom in nom_list:
        score = fuzz.ratio(nom, other_nom)
        if score >= threshold:
            similar_noms.append((nom, other_nom, score))
    return similar_noms

# Configure caching options
options = Options()
options.add_argument("--headless")  # Run in headless mode (without opening a window)

#options.page_load_strategy = 'eager'
options.page_load_strategy = 'normal'


#options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--enable-unsafe-swiftshader")  # Disable GPU hardware acceleration

options.add_argument("--disable-extensions")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-software-rasterizer")  # Disable the software rasterizer
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,  # Block images
    "profile.managed_default_content_settings.stylesheets": 2,  # Block CSS
    "profile.managed_default_content_settings.fonts": 2,  # Block fonts
    "profile.managed_default_content_settings.plugins": 2,  # Block plugins
    "profile.managed_default_content_settings.popups": 2,  # Block popups
    "profile.managed_default_content_settings.notifications": 2,  # Block notifications
    "profile.managed_default_content_settings.media_stream": 2,  # Block audio and video
})
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

with open('platformes.json', 'r') as file:
    sites = json.load(file)

# Initialize the WebDriver with the options
def initialize_driver():
    driver = webdriver.Chrome(options=options)
    return driver

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


async def get_description(driver, site):
    try:
        # Navigate to the product page
        driver.get(site["url"])

        html_content = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract the description using the provided CSS selector
        description_element = soup.select_one(site["description"])
        description = description_element.get_text(separator=' ', strip=True) if description_element else ""

        return description
        
    except Exception as e:
        print(f"Error fetching description for {site['url']}: {e}")
        return "Error fetching description"


# site category
async def collect_data_from_scraping(driver, site, products=None, page_limit=2, max_products=30, current_page=1, total_products=0):
    driver.get(site["url"])

    # Retrieve HTML content asynchronously
    html_content = await asyncio.to_thread(lambda: driver.page_source)

    print("Opened : ", site["url"])
    soup = BeautifulSoup(html_content, "html.parser")

    if products is None:
        products = []

    tasks = []
    
    for item in soup.select(site["product_selector"]):
        if total_products >= max_products:
            break  # Stop when max products are reached
        tasks.append(process_product(driver, item, site))
        total_products += 1
    
    # Run all product processing tasks concurrently
    pts = await asyncio.gather(*tasks)
    for product in pts:
        products.append(product)
            
    #dftemp = pd.DataFrame(products)
    #export_data(dftemp, "tempElectromenagerscleaned_data")

    if site.get("next_page") and current_page <= page_limit:
        print ("next_page : ", current_page+1)
        next_page = soup.select_one(site["next_page"])
        if next_page and 'href' in next_page.attrs:
            next_page_url = next_page['href']
            if next_page_url.startswith('/'):
                next_page_url = urljoin(site["url"], next_page_url)  # Automatically combines domain with path
            print(next_page_url)
            site["url"] = next_page_url
            current_page += 1  # Increment the page counter
            await collect_data_from_scraping(driver, site, products, page_limit, max_products, current_page) #total_products if total in all pages


    if products:
        # Read old data and clean current data
        try:
            # Attempt to read the file
            old_data = pd.read_csv("temp2Electromenagerscleaned_data.csv")
        except FileNotFoundError:
            # If the file doesn't exist, initialize as an empty DataFrame
            old_data = pd.DataFrame()
            
        newproducts = pd.DataFrame(products)

        data_now = pd.concat([old_data, newproducts], ignore_index=True)
        df_cleaned = clean_data(data_now)
        export_data(df_cleaned, "temp2Electromenagerscleaned_data")
        print("append site : ", site["url"])  # Using the last product for print
    else:
        print("No products found for site:", site["url"])

    return products


async def process_product(driver, item, site):
    nom = item.select_one(site["nom_selector"])
    prix = item.select_one(site["prix_selector"])
    promotion = item.select_one(site["promotion_selector"]) if site.get("promotion_selector") else None
    
    product = {}

    if nom and prix:
        the_prix = prix.text.strip()
        detected_currency = "UNKNOWN"
        cleaned_prix = convert_prix(the_prix, detected_currency)

        promotion_text = promotion.text.strip() if promotion else ""
        nomt = nom.text.strip() if nom else None

        #if site.get("nom_regex"):
        #    nomt = nomt.str.extract(site["nom_regex"])

        product_url = ""
        if 'href' in nom.attrs:
            product_url = nom['href']
            if product_url.startswith('/'):
                product_url = urljoin(site["url"], product_url)  # Combine domain with path

        # Run description fetching concurrently
        description = await get_description(driver, {"url": product_url, "description": site["description"]})

        product = {
                "nom": nomt,
                "prix": cleaned_prix,
                "website": site["website"],
                "source": site["url"],
                "date_scraped": date_now,
                "category": site["category"],
                "promotion": promotion_text,
                "url": product_url,
                "description": description,
            }
        print("append product : ", nomt)
    return product


# Function to collect data from API
async def collect_data_from_api(site):
    response = await loop.run_in_executor(None, requests.get, site["url"])  # Asynchronous request

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
                print ("append : ",nom)

        return products
    else:
        print(f"API error: {response.status_code}")
        return []


# Function to collect all data concurrently
async def collect_all_data():
    data = []
    driver = initialize_driver()
    
    # Running scraping tasks concurrently
    tasks = []
    for site in sites:
        if site["type"] == "scraping":
            result = await collect_data_from_scraping(driver, site)
            if result:  # Check if result is not None or empty
                data.extend(result)
                print ("Add : ",site["url"])
        elif site["type"] == "API":
            result = await collect_data_from_api(site)
            if result:  # Check if result is not None or empty
                data.extend(result)
    
    driver.quit()  # Close the driver after all scraping is done
    return data


# Data cleaning function
def clean_data(raw_data):
    df = pd.DataFrame(raw_data)

    if 'nom' not in df.columns:
        print("Error: 'nom' column is missing!")
        return df

    df["nom"] = df["nom"].astype(str).str.replace(r"[,-]$|\(\)$|(?: - |, )?(Matte Black|Copper|Slate|Brown|biscuit|Champagne|Tuscan stainless steel|Brushed Black|Brushed Navy|Carbon Graphite|Chrome|Forest Green|Graphite Steel|Ivory|Alpine White|Grey|Sapphire Blue|Specialty|Dark Steel|Essence White|Midnight Steel|Mirror|Satin Green|Silver Steel|Titanium|Beige & Bisque|Metallic|Red|Specialty|Black Slate|Black slate|Black Stainless|Multi-color|Black steel|Bronze|Nickel|Diamond Gray|Platinum Glass|Platinum|Graphite Steel|Graphite steel|Green|Orange|Yellow|Stainless steel look|Black stainless steel|Bisque|CleanSteel|Black Glass|Graphite|Slate|Matte Black|Matte black|Custom Panel Ready|Custom Panel Required|Custom Panel|Stainless Steel|SmudgeProof Stainless Steel|Smudge Proof Stainless Steel|White Glass|PrintShield Black Stainless Steel|Stainless Steel with Brushed Stainless Steel Handles|Stainless Steel|Stainless steel|Stainless Look|Matte Black with Brushed Stainless Steel Handles and Knobs|High Gloss White|White|Matte White|Matte white|Starlight|Space|Black|Blue|Gold|Gray|Green|Purple|Pink|Silver|Fingerprint Resistant Black Stainless Steel|Fingerprint Resistant Stainless Steel)", "", regex=True)
    
    df_cleaned = df.drop_duplicates(subset=["nom", "website", "date_scraped"], keep="first")
    
    df['normalized_nom'] = df['nom'].apply(normalize_text)
    df['normalized_description'] = df['description'].apply(normalize_text)
    
    df['nom_and_description'] = df['description']+" "+df['nom']
    
    # Continue with finding similar noms and further processing...
    groups = []
    seen = set()

    # To store the similar rows with their corresponding similarity ratio
    similar_rows_info = []

    for idx, row in df.iterrows():
        if idx in seen:
            continue
        nom = row["nom_and_description"]
        matches = find_similar_noms(nom, df["nom_and_description"].tolist())
        
        if not matches:
            continue
        
        match_indices = [
            idx for idx, match in enumerate(df["nom_and_description"]) if (nom, match, fuzz.ratio(nom, match)) in matches
        ]
        
        if match_indices:
            groups.append(match_indices)
            seen.update(match_indices)
            
            # Store the similar rows and their ratios
            for match_idx in match_indices:
                similarity_ratio = fuzz.ratio(nom, df["nom_and_description"].iloc[match_idx])
                similar_rows_info.append((df.iloc[match_idx], similarity_ratio))

    rows_to_keep = set()
    for group in groups:
        if group:
            min_prix_index = df.loc[group, "prix"].idxmin()
            rows_to_keep.add(min_prix_index)

    # Convert rows_to_keep to a list
    rows_to_keep = list(rows_to_keep)

    # Get the rows that were removed
    rows_removed = set(df.index) - set(rows_to_keep)

    # Convert rows_removed to a list before using it as an indexer
    rows_removed_list = list(rows_removed)

    # Print the removed rows
    print("Removed rows:")
    print(df.loc[rows_removed_list])

    # Print the similar rows that were kept, along with their similarity ratios
    #print("\nSimilar rows kept (with similarity ratio):")
    #for row, ratio in similar_rows_info:
    #    print(f"Row: {row.to_dict()} - Similarity Ratio: {ratio}%")
    
    # Use the list as the indexer
    df_cleaned = df.loc[rows_to_keep].reset_index(drop=True)
    
    return df_cleaned


# Export cleaned data
def export_data(df, filename="Electromenagerscleaned_data"):
    df.to_csv(filename+".csv", index=False)
    df.to_excel(filename+".xlsx", index=False, engine="openpyxl")
    print(f"Data exported to '{filename}'")


# Main execution
if __name__ == "__main__":
    # Get the event loop
    raw_data = asyncio.run(collect_all_data())

    df_cleaned = clean_data(raw_data)

    try:
        old_data = pd.read_csv("Electromenagerscleaned_data.csv")
        data_now = pd.concat([old_data, df_cleaned], ignore_index=True)
    except FileNotFoundError:
        data_now = df_cleaned

    export_data(data_now)
