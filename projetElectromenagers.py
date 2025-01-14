#!/usr/bin/env python3
#import sys
#import os

# Ensure user-specific site-packages are included
#sys.path.append('/home/youssef/.local/lib/python3.8/site-packages')

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
from seleniumwire import webdriver

import re
from rapidfuzz import fuzz, process

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
seleniumwire_options = {
    #'request_storage': 'selenium_cache',  # Directory to save cached requests
    'port': 4444,  # Specify a custom port
    'timeout': 240  # Increase timeout value
    #'request_storage_limit': 1000         # Limit to 1000 requests
}
options = Options()
options.add_argument("--headless")  # Run in headless mode (without opening a window)
options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration (optional but recommended)
options.add_argument("--enable-unsafe-swiftshader")  # Disable GPU hardware acceleration
options.add_argument("--no-sandbox")  # Prevent sandboxing (optional for certain environments)

#Initialize the WebDriver with the options
#driver = webdriver.Chrome(options=options)
#seleniumwire_options=seleniumwire_options, 
driver = webdriver.Chrome(options=options)

# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

#capabilities = DesiredCapabilities.CHROME
#capabilities['acceptInsecureCerts'] = True
#driver = webdriver.Chrome(desired_capabilities=capabilities)

with open('platformes.json', 'r') as file:
    sites = json.load(file)

# Headers to mimic a real browser and avoid bot detection
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
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
            .replace(",", ".")
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


# Function to collect data via scraping
def collect_data_from_scraping(site, products=None):

    if site.get("typehtml") or not site.get("typehtml"):
        
        driver.get(site["url"])
        # Allow time for the page to load
        time.sleep(2)
        
        # WebDriverWait(driver, 10).until(
            # EC.presence_of_element_located((By.ID, site["product_selector"]))
        # )

        # Extract the fully rendered HTML
        html_content = driver.page_source

        print ("Opened : ",site["url"])
        
    else:
        
        response = requests.get(site["url"], headers=headers)  # Adding headers to the request
        html_content = response.content
    
    soup = BeautifulSoup(html_content, "html.parser")

    
    if products is None:
        products = []
    for item in soup.select(site["product_selector"]):
        nom =  item.select_one(site["nom_selector"])
        prix = item.select_one(site["prix_selector"])
        promotion = item.select_one(site["promotion_selector"])
        
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
            
            products.append({
                "nom": nom.text.strip(),
                "prix": cleaned_prix,
                "website": site["website"],
                "source": site["url"],
                "date_scraped": date_now,
                "category": site["category"],
                "promotion": promotion_text
            })
    
    
    next_page = soup.select_one(site["next_page"]+' a:last-child')
    if next_page and 'href' in next_page.attrs:
        next_page_url = next_page['href']
        site["url"] = next_page_url
        collect_data_from_scraping(site, products)
    
    return products


# Function to collect data via API
def collect_data_from_api(site):
    response = requests.get(site["url"], headers=headers)  # Adding headers to the request
    
    if response.status_code == 200:
        data = response.json()
    
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
    
    print(df.columns)  # To inspect the columns in the data
    
    # Safeguard the 'nom' column to ensure it contains strings
    df["nom"] = df["nom"].astype(str).str.replace(r"[,-]$|\(\)$| - White| - Matte White|, Starlight|- Starlight| Starlight|, Space|, Black|, Blue|, Gold|, Gray|, Green|, Purple|, Pink|, Silver| - Space | - Space| - Black | - Blue| - Gold| - Gray| - Green| - Purple| - Pink| - Silver| Space| Black| Blue| Gold| Gray| Green| Purple| Pink| Silver|Space |Black |Blue |Gold |Gray |Green |Purple |Pink |Silver ", "", regex=True)
    
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
    
    # Analyze, visualize, and export data
    
    #print("Average prices in same website by product:")
    #print(analyze_data_in_same_site(data_now))
    #print("\r\nAverage prices in defferents websites by product:")
    #print(analyze_data_by_diff_sites(data_now))
    #plot_data(data_now)
    
    driver.quit()
    
    # Analyze, visualize, and export data
    #analyze_data(df_cleaned)
    #plot_data(df_cleaned)
