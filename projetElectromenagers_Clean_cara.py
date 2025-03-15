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

# Fonction pour normaliser le texte en le mettant en minuscule.
def normalize_text(text):
    if isinstance(text, str):
        text = text.lower()  # Convert to lowercase
        # nom = re.sub(r'[^a-z\s]', '', text)  # Uncomment if needed for special character removal
        return text
    else:
        # Convert non-string inputs to a string or handle them appropriately
        return str(text) if text is not None else ""

# Fonction pour trouver des noms similaires à l'aide de RapidFuzz.
def find_similar_noms(nom, nom_list, threshold=95):
    similar_noms = []
    for other_nom in nom_list:
        score = fuzz.ratio(nom, other_nom)
        if score >= threshold:
            similar_noms.append((nom, other_nom, score))
    return similar_noms

# Configure caching options
options = Options()
#options.add_argument("--headless")  # Run in headless mode (without opening a window)

options.page_load_strategy = 'eager'

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

# Fonction pour initialiser un pilote Selenium avec des options spécifiques.
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

# Fonction pour convertir un prix en USD.
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


# Fonction pour récupérer une description de produit avec Selenium et BeautifulSoup.
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

        return description, description_element
    except Exception as e:
        print(f"Error fetching description for {site['url']}: {e}")
        return "", None







# Fonction principale pour collecter les données via web scraping.
async def collect_data_from_scraping(driver, site, products=None, page_limit=2, max_products=30, current_page=1, total_products=0):
    try:
        driver.get(site["url"])
    except Exception as e:
        print(f"Error loading {site['url']}: {e}")
        return None

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


    # Read old data and clean current data
    if products:
        try:
            # Attempt to read the file
            old_data = pd.read_csv("temp2Electromenagerscleaned_data.csv")
        except FileNotFoundError:
            # If the file doesn't exist, initialize as an empty DataFrame
            old_data = pd.DataFrame()
            
        newproducts = pd.DataFrame(products)

        data_now = pd.concat([old_data, newproducts], ignore_index=True)
        try:
            df_cleaned = clean_data(data_now)
            export_data(df_cleaned, "temp2Electromenagerscleaned_data")
            print("Appended site:", site["url"])  # Log the last processed site
        except Exception as e:
            print(f"Error during cleaning or exporting data for site {site['url']}: {e}")
    else:
        print("No products found for site:", site["url"])

    return products


# Fonction pour traiter un produit individuel.
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
        if site.get("description"):
            description, soup = await get_description(driver, {"url": product_url, "description": site["description"]})
        else:
            description = None
            soup = None
        
        #if site.get("sections"):
        #
        #    characteristics = normalize_characteristics(extract_characteristics(item, site))
        #    
        #    text_characteristics = json_to_text(characteristics)
        #    
        #else :
        #    characteristics = ""
        #    
        #    text_characteristics = ""
        
        
        
        # Apply the function to the DataFrame
        #df['characteristics'] = df.apply(
        #    lambda row: normalize_characteristics(extract_characteristics(row['html'], get_site_config(row['website']))) 
        #    if isinstance(row['html'], str) and row['html'].strip() 
        #    else {}, 
        #    axis=1
        #)
        
        #df['text_characteristics'] = df['characteristics'].apply(json_to_text)




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
                "html": soup,
                #"characteristics": characteristics,
                #"text_characteristics": text_characteristics
            }
        print("append product : ", nomt)
        
    return product


# Fonction pour collecter des données via une API.
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
        
    df = df.dropna(subset=["nom"])

    df["nom"] = df["nom"].astype(str).str.replace(r"[,-]$|\(\)$|(?: - |, )?(Matte Black|Copper|Slate|Brown|biscuit|Champagne|Tuscan stainless steel|Brushed Black|Brushed Navy|Carbon Graphite|Chrome|Forest Green|Graphite Steel|Ivory|Alpine White|Grey|Sapphire Blue|Specialty|Dark Steel|Essence White|Midnight Steel|Mirror|Satin Green|Silver Steel|Titanium|Beige & Bisque|Metallic|Red|Specialty|Black Slate|Black slate|Black Stainless|Multi-color|Black steel|Bronze|Nickel|Diamond Gray|Platinum Glass|Platinum|Graphite Steel|Graphite steel|Green|Orange|Yellow|Stainless steel look|Black stainless steel|Bisque|CleanSteel|Black Glass|Graphite|Slate|Matte Black|Matte black|Custom Panel Ready|Custom Panel Required|Custom Panel|Stainless Steel|SmudgeProof Stainless Steel|Smudge Proof Stainless Steel|White Glass|PrintShield Black Stainless Steel|Stainless Steel with Brushed Stainless Steel Handles|Stainless Steel|Stainless steel|Stainless Look|Matte Black with Brushed Stainless Steel Handles and Knobs|High Gloss White|White|Matte White|Matte white|Starlight|Space|Black|Blue|Gold|Gray|Green|Purple|Pink|Silver|Fingerprint Resistant Black Stainless Steel|Fingerprint Resistant Stainless Steel)", "", regex=True)
    
    # Normalize different forms of appliance names
    df["nom"] = re.sub(r"\b(frigo|réfrigérateur|frigidaire)\b", "réfrigérateur", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(congélateur|freezer)\b", "congélateur", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(lave[- ]?vaisselle|machine à vaisselle)\b", "lave-vaisselle", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(lave[- ]?linge|machine à laver|lessiveuse)\b", "lave-linge", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(sèche[- ]?linge|sécheuse)\b", "sèche-linge", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(micro[- ]?ondes|four à micro[- ]?ondes)\b", "micro-ondes", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(plaque de cuisson|table de cuisson|cuisinière)\b", "plaque de cuisson", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(four électrique|four à gaz|four encastrable)\b", "four", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(hotte aspirante|hotte de cuisine|hotte)\b", "hotte", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(four à pain|machine à pain)\b", "machine à pain", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(robot de cuisine|mixer|blender|mixeur)\b", "robot de cuisine", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(cafetiere|machine à café)\b", "machine à café", df["nom"], flags=re.IGNORECASE)
    df["nom"] = re.sub(r"\b(bouilloire électrique|bouilloire)\b", "bouilloire", df["nom"], flags=re.IGNORECASE)
    
    # Remove extra spaces
    df["nom"] = re.sub(r"\s+", " ", df["nom"]).strip()
    
    df['normalized_nom'] = df['nom'].apply(normalize_text)
    df['normalized_description'] = df['description'].apply(lambda x: normalize_text(x) if pd.notna(x) else "")
    
    df['nom_and_description'] = df['normalized_nom']+" "+df['normalized_description']
    
    df = df.drop_duplicates(subset=["normalized_nom", "website", "date_scraped"], keep="first")
    
    df_cleaned = df
    try:
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
    except KeyError as e:
        print(f"Erreur : {e}")
    #df = df.drop(columns=['nom_and_description'])
    
    return df_cleaned




# Export cleaned data
def export_data(df, filename="Electromenagerscleaned_data"):
    df.to_csv(filename+".csv", index=False)
    df.to_excel(filename+".xlsx", index=False, engine="openpyxl")
    print(f"Data exported to '{filename}'")






def extract_characteristics(html, site_config):
    # Parse the HTML content
    soup = BeautifulSoup(html, 'html.parser')
    
    result = {}

    # Loop through each site in the config
    for section_name, section_config in site_config['sections'].items():
        # Select the section based on sectionSelector
        section = soup.select_one(section_config['sectionSelector'])
        if not section:
            continue

        if section:
            # For sites like BlueStar, get the section name (only if 'nameSelector' exists)
            section_heading = None
            if 'nameSelector' in section_config:
                section_heading = section.select_one(section_config['nameSelector'])
                section_heading = section_heading.get_text(strip=True) if section_heading else None

            # Initialize result for this section
            if section_heading:
                if section_heading not in result:
                    result[section_heading] = {}
            else:
                if section_name not in result:
                    result[section_name] = {}

            # Extract rows from the section
            rows = section.select(section_config['rowsSelector'])
            for row in rows:
                if section_config['specNameSelector']:
                    spec_name = row.select_one(section_config['specNameSelector'])
                    spec_value = row.select_one(section_config['specValueSelector'])

                    if spec_name and spec_value:
                        spec_name = spec_name.get_text(strip=True)
                        spec_value = spec_value.get_text(strip=True)

                        # Handle <br> tags for certain sites
                        if spec_value and '<br' in spec_value:
                            spec_value = spec_value.replace('<br>', ', ').replace('<br/>', ', ').replace('<br />', ', ')

                        if section_heading:
                            result[section_heading][spec_name] = spec_value
                        else:
                            result[section_name][spec_name] = spec_value
                else:
                    # For sites with no specNameSelector, directly store the list items as features (strings)
                    feature = row.get_text(strip=True)
                    if feature:
                        # Ensure result[section_name] is a list
                        if section_name not in result:
                            result[section_name] = []
                        elif not isinstance(result[section_name], list):
                            result[section_name] = [result[section_name]]  # Convert to list if it's a dict

                        result[section_name].append(feature)

            dimensions_text = section.get_text(strip=True)
            if 'Approximate Dimensions' in dimensions_text:
                # Use regex to find height and width
                height_match = re.search(r'Height:\s*(\d+[\d/]*\s?[a-zA-Z]*)', dimensions_text)
                width_match = re.search(r'Width:\s*(\d+[\d/]*\s?[a-zA-Z]*)', dimensions_text)

                # If matches are found, store them in the result
                if height_match:
                    result['SPECIFICATIONS'] = result.get('DIMENSIONS', {})
                    result['SPECIFICATIONS']['Height'] = height_match.group(1)
                if width_match:
                    result['SPECIFICATIONS'] = result.get('DIMENSIONS', {})
                    result['SPECIFICATIONS']['Width'] = width_match.group(1)

    # Normalize the extracted characteristics before returning
    return result


# Define the normalization mapping
normalized_names = {
    'Height': [
        'Product Height', 
        'Height To Top Of Refrigerator (Without Hinges)', 
        'Height To Top Of Door Hinge',
        'Maximum Height', 
        'Minimum Height'
    ],
    'Width': [
        'Product Width',
        'Width',
        'Width :',
        'Cutout Dimensions:',
        'Shipping Width :',
        'Shipping Depth :'
    ],
    'Depth': [
        'Depth Without Handle', 
        'Depth With Handle', 
        'Depth with Door Closed :', 
        'Shipping Depth :'
    ],
    'Finish': ['Finish', 'Fingerprint Resistant', 'Color Appearance'],
    'Material': ['Tub Material', 'Handle Color'],
    'Control Panel Location': ['Control Panel Location', 'Type of Control'],
    'Noise Level': ['Noise Level'],
    'Energy Rating': ['ENERGY STAR® Rated'],
    'Voltage': ['Voltage', 'Voltage :'],
    'Capacity': ['Total Place Settings', 'Freezer Capacity', 'Overall Capacity', 'Refrigerator Capacity'],
    'Rack Features': ['Height Adjustable Upper Rack', 'Lower Rack'],
    'Child Lock': ['Child Lock'],
    'Water Consumption': ['Water Consumption Per Cycle'],
    'Energy Consumption': ['Energy Consumption (kWh / Year)'],
    'Cycle Options': ['Number of Wash Cycles', 'Number of Options'],
    'Sprayers': ['Number of Sprayers'],
    'Warranty': ['Parts', 'Labor'],
    'Weight': ['Product Weight / Shipping Weight', 'Weight'],
}


def normalize_name(raw_name):
    """Normalize the specification name based on the mapping."""
    for normalized, aliases in normalized_names.items():
        if raw_name in aliases:
            return normalized
    return raw_name  # Return as-is if no match is found


def normalize_characteristics(characteristics):
    """Normalize the specification dictionary keys across multiple sites."""
    normalized_characteristics = {}
    
    for category, data in characteristics.items():
        if isinstance(data, dict):
            # Normalize specifications in this category
            normalized_category = {}
            for spec_name, spec_value in data.items():
                normalized_name = normalize_name(spec_name)
                
                # If the normalized name already exists, append the new value to a list
                if normalized_name in normalized_category:
                    if not isinstance(normalized_category[normalized_name], list):
                        normalized_category[normalized_name] = [normalized_category[normalized_name]]
                    normalized_category[normalized_name].append(spec_value)
                else:
                    normalized_category[normalized_name] = spec_value
            normalized_characteristics[category] = normalized_category
        elif isinstance(data, list):
            # Handle the list case, just store as-is
            normalized_characteristics[category] = data
        else:
            normalized_characteristics[category] = data
    
    return normalized_characteristics


def sort_json_by_key(characteristics):
    """Sort the JSON dictionary by keys (a->z)."""
    if isinstance(characteristics, dict):
        return {k: sort_json_by_key(v) if isinstance(v, dict) else v for k, v in sorted(characteristics.items())}
    elif isinstance(characteristics, list):
        return [sort_json_by_key(item) for item in characteristics]
    return characteristics


def json_to_text(data, parent_key=""):
    data = sort_json_by_key(data)
    result = ""
    
    for key, value in data.items():
        # Construct the full key path if there's a parent key
        full_key = f"{key}" if parent_key else key
        
        if isinstance(value, dict):
            # If the value is a dictionary, recurse with the updated key
            result += json_to_text(value, full_key)
        else:
            # Append the key-value pair to the result
            result += f"{full_key}: {value}, "
    
    return result


def get_site_config(website_name):
    for site in sites:
        if site['website'] == website_name:
            return site
    return None


# Export cleaned data
def extract_cara(df_cleaned):
    # Apply the function to the DataFrame
    df_cleaned['characteristics'] = df_cleaned.apply(
        lambda row: normalize_characteristics(extract_characteristics(row['html'], get_site_config(row['website']))) 
        if isinstance(row['html'], str) and row['html'].strip() 
        else {}, 
        axis=1
    )

    df_cleaned['text_characteristics'] = df_cleaned['characteristics'].apply(json_to_text)
    
    return df_cleaned


# Main execution
if __name__ == "__main__":
    # Get the event loop
    raw_data = asyncio.run(collect_all_data())

    df_cleaned = clean_data(raw_data)
    

    df_cleaned = extract_cara(df_cleaned)
    
    # Create or update columns dynamically
    #for index, row in df.iterrows():
    #    characteristics = row['characteristics']
    #    if not isinstance(characteristics, dict):
    #        continue
    #    
    #    for category, data in characteristics.items():
    #        if isinstance(data, dict):  # For nested dictionaries
    #            for spec_name, spec_value in data.items():
    #                column_name = f"charac_{spec_name}"
    #                if column_name in df.columns:
    #                    df.at[index, column_name] = spec_value
    #                else:
    #                    df[column_name] = None  # Initialize the column if it doesn't exist
    #                    df.at[index, column_name] = spec_value
    #        else:  # For simple values or lists
    #            if category in df.columns:
    #                df.at[index, category] = data
    #            else:
    #                df[category] = None  # Initialize the column if it doesn't exist
    #                df.at[index, category] = data


    # Save the resulting DataFrame to a new CSV
    #df.to_csv('test_characteristics.csv', index=False)
    #df.to_excel("test_characteristics.xlsx", index=False, engine="openpyxl")


    try:
        old_data = pd.read_csv("Electromenagerscleaned_data.csv")
        data_now = pd.concat([old_data, df_cleaned], ignore_index=True)
    except FileNotFoundError:
        data_now = df_cleaned


    export_data(data_now)
    print("\r\nEnd..")