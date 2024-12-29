import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

import matplotlib.pyplot as plt



    #"https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=pcmcat209000050008&id=pcat17071&iht=n&ks=960&list=y&qp=brand_facet%3DBrand~Apple%5Esoldout_facet%3DAvailability~Exclude%20Out%20of%20Stock%20Items&sc=Global&st=categoryid%24pcmcat209000050008&type=page&usc=All%20Categories",
    #"https://www.amazon.com/iPad/s?k=iPad"
    #"https://www.walmart.com/browse/electronics/all-apple-ipad/3944_1229722_1229728_3998838",

# Table of site configurations
sites = [
    
    {
        "url": "https://www.costco.com/ipad.html",
        "website": "costco.com",
        "type": "scraping",
        "product_selector": ".product",
        "title_selector": ".description a",
        "price_selector": ".price"
    },
    {
        "url": "https://www.costco.com/ipad.html?pageSize=24&currentPage=2",
        "website": "costco.com",
        "type": "scraping",
        "product_selector": ".product",
        "title_selector": ".description a",
        "price_selector": ".price"
    },
    {
        "url": "https://www.newegg.com/p/pl?N=100171661%2050001759&Submit=ENE&page=1",
        #"pages": "&page=1",
        "website": "newegg.com",
        "type": "scraping",
        "product_selector": ".item-cell",
        "title_selector": ".item-title",
        "price_selector": ".price-current"
    },
    {
        "url": "https://www.newegg.com/p/pl?N=100171661%2050001759&Submit=ENE&page=2",
        "website": "newegg.com",
        "type": "scraping",
        "product_selector": ".item-cell",
        "title_selector": ".item-title",
        "price_selector": ".price-current"
    },
    {
        "url": "https://www.newegg.com/p/pl?N=100171661%2050001759&Submit=ENE&page=3",
        "website": "newegg.com",
        "type": "scraping",
        "product_selector": ".item-cell",
        "title_selector": ".item-title",
        "price_selector": ".price-current"
    },
    {
        "url": "https://www.newegg.com/p/pl?N=100171661%2050001759&Submit=ENE&page=4",
        "website": "newegg.com",
        "type": "scraping",
        "product_selector": ".item-cell",
        "title_selector": ".item-title",
        "price_selector": ".price-current"
    },
    {
        "url": "https://www.newegg.com/p/pl?N=100171661%2050001759&Submit=ENE&page=5",
        "website": "newegg.com",
        "type": "scraping",
        "product_selector": ".item-cell",
        "title_selector": ".item-title",
        "price_selector": ".price-current"
    },
    {
        "url": "https://www.newegg.com/p/pl?N=100171661%2050001759&Submit=ENE&page=6",
        "website": "newegg.com",
        "type": "scraping",
        "product_selector": ".item-cell",
        "title_selector": ".item-title",
        "price_selector": ".price-current"
    },
    {
        "url": "https://www.newegg.com/p/pl?N=100171661%2050001759&Submit=ENE&page=7",
        "website": "newegg.com",
        "type": "scraping",
        "product_selector": ".item-cell",
        "title_selector": ".item-title",
        "price_selector": ".price-current"
    },
    #{
    #    "url": "https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=pcmcat209000050008&id=pcat17071&iht=n&ks=960&list=y&qp=brand_facet%3DBrand~Apple%5Esoldout_facet%3DAvailability~Exclude%20Out%20of%20Stock%20Items&sc=Global&st=categoryid%24pcmcat209000050008&type=page&usc=All%20Categories",
    #    "website": "bestbuy.com",
    #    "type": "scraping",
    #    "product_selector": ".sku-item",
    #    "title_selector": ".sku-title a",
    #    "price_selector": ".priceView-hero-price span"
    #},
    {
        "url": "https://www.samsclub.com/b/apple-ipad/11260108",
        "website": "samsclub.com",
        "type": "scraping",
        "product_selector": "li .sc-pc-medium-desktop-card-canary.sc-plp-cards-card",
        "title_selector": ".sc-pc-title-medium h3",
        "price_selector": ".sc-price .visuallyhidden"
    },
    #{
    #    "url": "https://www.backmarket.com/en-us/l/apple-ipad/f78ae8f5-4611-4ad0-b2ad-ced07765b847",
    #    "website": "backmarket.com",
    #    "type": "scraping",
    #    "product_selector": ".flex.h-full.flex-col",
    #    "title_selector": ".body-1-bold.line-clamp-2",
    #    "price_selector": ".text-static-default-hi.body-2-bold"
    #}
]

# Headers to mimic a real browser and avoid bot detection
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "TE": "Trailers"
}

# Function to collect data via scraping
def collect_data_from_scraping(site):
    response = requests.get(site["url"], headers=headers)  # Adding headers to the request
    soup = BeautifulSoup(response.content, "html.parser")
    
    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    products = []
    for item in soup.select(site["product_selector"]):
        title = item.select_one(site["title_selector"])
        price = item.select_one(site["price_selector"])
        
        if title and price:
            products.append({
                "nom": title.text.strip(),
                "prix": price.text.strip(),
                "website": site["website"],
                "source": site["url"],
                "date_scraped": date_now,
                "category": "",
                "promotion": ""
            })
    
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
            title = item.get(site["selectors"]["title_key"])
            price = item.get(site["selectors"]["price_key"])
            
            if title and price:
                products.append({
                    "nom": title,
                    "prix": price,
                    "website": site["website"],
                    "source": site["url"],
                    "date_scraped": date_now,
                    "category": "",
                    "promotion": ""
                })
        
        return products
    else:
        print(f"API error: {response.status_code} {response.text}")
        return []

# Function to collect data from all sites
def collect_all_data():
    data = []
    for site in sites:
        if site["type"] == "scraping":
            data.extend(collect_data_from_scraping(site))
        elif site["type"] == "API":
            data.extend(collect_data_from_api(site))
    return data

# Data cleaning function
def clean_data(raw_data):
    df = pd.DataFrame(raw_data)
    
    # Clean product names
    df["nom"] = (
        df["nom"]
        .astype(str)
        .str.replace(" Rouge", "", regex=False)
        .str.replace("Bleu", "", regex=False)
        .str.replace("Refurbished ", "", regex=False)
        .str.replace("Apple ", "", regex=False)
        .str.replace(" - Excellent Condition", "", regex=False)
        .str.replace(" - Good Condition", "", regex=False)
        .str.replace(" - Very Good Condition", "", regex=False)
        .str.replace(", Choose Color", "", regex=False)
        .str.replace("2021 ", "", regex=False)
        .astype(str)
    )
    
    # Clean prices
    df["prix"] = (
        df["prix"]
        .astype(str)
        .str.replace(" USD", "", regex=False)
        .str.replace("current price: ", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("\xa0", "", regex=False)
        .str.replace("–", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )
    
    return df



# Analyze data
def analyze_data_in_same_site(df):
    #avg_prices = df.groupby("nom")["prix"].mean()


    #same product in month
    avg_prices = df.groupby(["nom", "website"])["prix"].agg(["mean", "min", "max", "count"])
    
    
    #avg_prices_filtered = final_grouped[final_grouped["count"] > 0]

    return avg_prices

# Analyze data
def analyze_data_by_diff_sites(df):
    #avg_prices = df.groupby("nom")["prix"].mean()


    #same product in month
    #avg_prices = df.groupby(["nom", "website"])["prix"].agg(["mean", "min", "max", "count"])
    
    
    # new price of product only
    #df_sorted = df.sort_values(by="date_scraped", ascending=False)
    #df_unique = df_sorted.drop_duplicates(subset="nom", keep="first")
    #avg_prices = df_unique.groupby("nom")["prix"].agg(["mean", "min", "max", "count"])
    
    
    
    
    # min max mean in same site in month and group by name for min max mean
    
    # تجميع البيانات حسب الاسم والموقع
    # تجميع البيانات حسب الاسم والموقع
    grouped_by_name_and_website = df.groupby(["nom", "website"])["prix"].agg(
        mean_samesite="mean",
        min_samesite="min",
        max_samesite="max"
    ).reset_index()

    # إضافة عمود يحتوي على عدد المواقع التي يظهر فيها كل منتج
    site_counts = grouped_by_name_and_website.groupby("nom")["website"].nunique().reset_index(name="site_count")

    # تحديد المواقع الأغلى والأرخص لكل منتج
    extreme_sites = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("nom")["max_samesite"].idxmax(),
        ["nom", "website"]
    ].rename(columns={"website": "most_expensive_site"})
    
    extreme_sites["cheapest_site"] = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("nom")["min_samesite"].idxmin(),
        "website"
    ].values

    # تجميع الإحصائيات العامة حسب المنتج
    final_grouped = grouped_by_name_and_website.groupby("nom")[["mean_samesite", "min_samesite", "max_samesite"]].agg(
        mean_all_sites=("mean_samesite", "mean"),
        min_all_sites=("min_samesite", "min"),
        max_all_sites=("max_samesite", "max")
    ).reset_index()

    # دمج عدد المواقع والمواقع الأغلى والأرخص مع الإحصائيات النهائية
    final_grouped = final_grouped.merge(site_counts, on="nom", how="left")
    final_grouped = final_grouped.merge(extreme_sites, on="nom", how="left")

    # تصفية المنتجات التي تظهر في أكثر من موقع واحد
    #final_grouped = final_grouped[final_grouped["site_count"] > 1]




    
    
    #avg_prices_filtered = final_grouped[final_grouped["count"] > 0]

    return final_grouped



# Analyze data
def analyze_data(df):
    avg_prices = df.groupby("nom")["prix"].mean()
    print("Average prices by product:")
    print(avg_prices)
    return avg_prices

# Plot data
def plot_data(df):
    avg_prices = analyze_data_by_diff_sites(df)
    avg_prices.plot(kind="bar", title="Average Prices by Product", xlabel="Product", ylabel="Price (USD)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

# Export cleaned data
def export_data(df, filename="cleaned_data.csv"):
    df.to_csv(filename, index=False)
    
    df.to_excel("cleaned_data.xlsx", index=False, engine="openpyxl")  # Using openpyxl for Excel support
    print(f"Data exported to '{filename}'")

# Main execution
if __name__ == "__main__":
    raw_data = collect_all_data()
    df_cleaned = clean_data(raw_data)
    
    
    
    # Replace append() with concat()
    try:
        old_data = pd.read_csv("cleaned_data.csv")  # Read the existing data from the file
        # Concatenate the cleaned data to the old data
        data_now = pd.concat([old_data, df_cleaned], ignore_index=True)
    except FileNotFoundError:
        # If the file doesn't exist, use the cleaned data as the initial dataset
        data_now = df_cleaned
        
    
    
    # Concatenate the cleaned data to the old data

    
    # Analyze, visualize, and export data
    
    print("Average prices in same website by product:")
    print(analyze_data_in_same_site(data_now))
    print("\r\nAverage prices in defferents websites by product:")
    print(analyze_data_by_diff_sites(data_now))
    plot_data(data_now)

    
    # Analyze, visualize, and export data
    #analyze_data(df_cleaned)
    #plot_data(df_cleaned)
    
    
    export_data(data_now)
