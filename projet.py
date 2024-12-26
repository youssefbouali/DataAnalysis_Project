import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt

# Étape 1 : Collecte des données depuis 4 sites

#https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=pcmcat209000050008&id=pcat17071&iht=n&ks=960&list=y&qp=brand_facet%3DBrand~Apple%5Esoldout_facet%3DAvailability~Exclude%20Out%20of%20Stock%20Items&sc=Global&st=categoryid%24pcmcat209000050008&type=page&usc=All%20Categories
#https://www.amazon.com/iPad/s?k=iPad
#https://www.walmart.com/browse/electronics/all-apple-ipad/3944_1229722_1229728_3998838
#https://www.newegg.com/p/pl?Submit=ENE&IsNodeId=1&N=100171661%2050001759&cm_sp=Cat_Tablets_2-_-TopNav-_-iPads_5

# Sites à scraper ou utiliser une API
sites = [
    #"https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=pcmcat209000050008&id=pcat17071&iht=n&ks=960&list=y&qp=brand_facet%3DBrand~Apple%5Esoldout_facet%3DAvailability~Exclude%20Out%20of%20Stock%20Items&sc=Global&st=categoryid%24pcmcat209000050008&type=page&usc=All%20Categories",
    #"https://www.amazon.com/iPad/s?k=iPad"
    #"https://www.walmart.com/browse/electronics/all-apple-ipad/3944_1229722_1229728_3998838",
    "https://www.newegg.com/p/pl?Submit=ENE&IsNodeId=1&N=100171661%2050001759&cm_sp=Cat_Tablets_2-_-TopNav-_-iPads_5"
]

response = requests.get("https://www.newegg.com/p/pl?Submit=ENE&IsNodeId=1&N=100171661%2050001759&cm_sp=Cat_Tablets_2-_-TopNav-_-iPads_5")
soup = BeautifulSoup(response.content, "html.parser")



# Fonction pour récupérer les données via API
def collect_data_from_api(api_url, api_key, category, limit=50):
    params = {
        "category": category,
        "limit": limit
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(api_url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur API : {response.status_code} {response.text}")
        return []

# Fonction pour faire du web scraping
def collect_data_from_scraping(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    produits = []
    for item in soup.select(".item-cell"):
        nom = item.select_one(".item-title").text.strip()
        prix = item.select_one(".price-current").text.strip()
        produits.append({"nom": nom, "prix": prix})
    
    return produits

# Collecte des données de tous les sites (API et scraping)
def collect_all_data(api_url, api_key, category):
    data = []
    for site in sites:
        if "example" in site:  # Exemple de condition pour l'API
            data += collect_data_from_api(api_url, api_key, category)
        else:  # Autres sites utilisant du scraping
            data += collect_data_from_scraping(site)
    return data

# Étape 2 : Nettoyage des données
def clean_data(raw_data):
    df = pd.DataFrame(raw_data)
    
    # Nettoyage des noms de produits
    df["nom"] = df["nom"].str.replace(r" Rouge| Bleu", "", regex=True)
    
    # Nettoyage des prix
    # Ensure that all unwanted characters are removed properly
    df["prix"] = df["prix"].str.replace(" USD", "", regex=False)  # Remove ' USD' if present
    df["prix"] = df["prix"].str.replace('$', '', regex=False)      # Remove the dollar sign
    df["prix"] = df["prix"].str.replace('\xa0', '', regex=False)    # Remove non-breaking space
    df["prix"] = df["prix"].str.replace('–', '', regex=False)       # Remove en dash
    df["prix"] = df["prix"].str.replace(',', '', regex=False)       # Remove commas (thousands separator)


    # Convert the cleaned string to float
    df["prix"] = df["prix"].astype(float)
    
    return df

# Étape 3 : Analyse des données
def analyze_data(df):
    moyennes = df.groupby("nom")["prix"].mean()
    print("Moyennes des prix par produit :")
    print(moyennes)
    
    return moyennes

# Étape 4 : Visualisation des données
def plot_data(df):
    plt.plot(df["nom"], df["prix"], marker="o")
    plt.title("Évolution des prix des produits")
    plt.xlabel("Produits")
    plt.ylabel("Prix (USD)")
    plt.xticks(rotation=90)  # Pour une meilleure lisibilité des noms de produits
    plt.tight_layout()
    plt.show()

# Étape 5 : Exportation des données nettoyées
def export_data(df):
    df.to_csv("donnees_nettoyees.csv", index=False)
    print("Données exportées sous 'donnees_nettoyees.csv'")

# Paramètres API et catégorie
API_URL = "https://api.example.com/products"
API_KEY = "votre_api_key"
CATEGORY = "electronics"  # Exemple de catégorie

# Collecte des données
raw_data = collect_all_data(API_URL, API_KEY, CATEGORY)

# Nettoyage des données
df_cleaned = clean_data(raw_data)

# Analyse des données
moyennes = analyze_data(df_cleaned)

# Visualisation des données
plot_data(df_cleaned)

# Export des données nettoyées
export_data(df_cleaned)
print (df_cleaned)