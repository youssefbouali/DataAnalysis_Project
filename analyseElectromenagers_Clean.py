import pandas as pd

import matplotlib.pyplot as plt

import re
from rapidfuzz import fuzz, process

# Function to normalize text
def normalize_title(title):
    title = title.lower()    # Convert to lowercase
    #title = re.sub(r'[^a-z\s]', '', title) # Remove special characters and digits
    return title

# Function to find similar titles using RapidFuzz
def find_similar_titles(title, title_list, threshold=70):
    similar_titles = []
    for other_title in title_list:
        # Compute similarity score between title and other title
        score = fuzz.ratio(title, other_title)
        if score >= threshold:
            similar_titles.append((title, other_title, score))
    return similar_titles


# Analyze data
def analyze_data_by_diff_sites(df):

    # Apply normalization to product titles
    df['normalized_title'] = df['nom'].apply(normalize_title)

    # Apply fuzzy matching to group similar product titles
    unique_titles = df['normalized_title'].unique()
    title_groups = {}

    for title in unique_titles:
        group = find_similar_titles(title, unique_titles)
        for _, other_title, _ in group:
            title_groups[other_title] = title  # Group titles with high similarity

    # Map the grouped titles back to the DataFrame
    df['grouped_title'] = df['normalized_title'].map(lambda x: title_groups.get(x, x))
    
    # Regrouper les données par nom et site
    grouped_by_name_and_website = df.groupby(["grouped_title", "website"])["prix"].agg(
        mean_samesite="mean",
        min_samesite="min",
        max_samesite="max"
    ).reset_index()

    # Ajouter une colonne contenant le nombre de sites où chaque produit apparaît
    site_counts = grouped_by_name_and_website.groupby("grouped_title")["website"].nunique().reset_index(name="site_count")
    

    # Déterminer le site le plus cher et le moins cher pour chaque produit
    extreme_sites = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("grouped_title")["max_samesite"].idxmax(),
        ["grouped_title", "website"]
    ].rename(columns={"website": "most_expensive_site"})
    
    extreme_sites["cheapest_site"] = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("grouped_title")["min_samesite"].idxmin(),
        "website"
    ].values

    # Statistiques générales agrégées par produit
    final_grouped = grouped_by_name_and_website.groupby("grouped_title")[["mean_samesite", "min_samesite", "max_samesite"]].agg(
        mean_all_sites=("mean_samesite", "mean"),
        min_all_sites=("min_samesite", "min"),
        max_all_sites=("max_samesite", "max")
    ).reset_index()

    # Intégrer le nombre de sites et sites les plus chers et les moins chers dans les statistiques finales
    final_grouped = final_grouped.merge(site_counts, on="grouped_title", how="left")
    final_grouped = final_grouped.merge(extreme_sites, on="grouped_title", how="left")

    # Filtrer les produits qui apparaissent sur plusieurs sites
    final_grouped = final_grouped[final_grouped["site_count"] > 1]

    return final_grouped


# Analyze data
def promotions_par_categorie(df):

    # Filtrer les produits en promotion
    promotion_df = df[df['promotion'] != ""]

    # Compter les promotions par catégorie
    promotions_par_categorie = promotion_df.groupby(['category','promotion'])['promotion'].count()

    return promotions_par_categorie


# Analyze data
def analyze_data_in_same_site(df):

    #same product in month
    avg_prices = df.groupby(["nom", "website"])["prix"].agg(["mean", "min", "max", "count"])
    
    avg_prices_filtered = avg_prices[avg_prices["min"] != avg_prices["max"]]

    return avg_prices_filtered


# Analyze data
def analyze_data_in_all_days(df, nom=None, website=None):

    #same product in month
    grouped = df.groupby(["nom", "website"]).agg(count=("prix", "count"))
    
    if not nom and not website:
        filtered = grouped[grouped["count"] > 1]
    elif nom and website:
        filtered = grouped[grouped["count"] > 1 and grouped["nom"] == nom and grouped["website"] == website]
    elif nom:
        filtered = grouped[grouped["count"] > 1 and grouped["nom"] == nom]
    elif website:
        filtered = grouped[grouped["count"] > 1 and grouped["website"] == website]

    # Add 'date_scraped' back if needed (ensure it's a column in the original dataframe)
    if "date_scraped" in df.columns:
        filtered = filtered.reset_index().merge(df[["nom", "website", "date_scraped", "prix"]], on=["nom", "website"])
        grouped_by_date = filtered.groupby(["date_scraped"]).agg(total_products=("count", "sum"),sum_prix=("prix", "sum"))
        return grouped_by_date

    return grouped_by_date


# Analyze data
def analyze_data_in_same_site_grouped_sites(df, nom=None, website=None):

    avg_prices = df.groupby(["nom", "website"])["prix"].agg(["mean", "min", "max", "count"])
    
    avg_prices_filtered = avg_prices[avg_prices["min"] != avg_prices["max"]]

    grouped_by_date = avg_prices.groupby(["website"]).agg({
    'mean': ['mean'],
    'min': ['mean'],
    'max': ['mean']})
    return grouped_by_date

# Plot data
def plot_data(avg_prices, title="Average Prices by Product", grouped_title="Product"):
    # Plot the data
    avg_prices.plot(kind="bar", title=title, xlabel=grouped_title, ylabel="Price (USD)")
    
    # Set x-tick labels to the index of avg_prices, assuming it's the grouped title
    plt.xticks(ticks=range(len(avg_prices)), labels=avg_prices.index, rotation=45, ha="right")
    
    # Adjust layout for better display
    plt.tight_layout()
    plt.show()


# Main execution
if __name__ == "__main__":
    old_data = pd.read_csv("Electromenagerscleaned_data.csv")  # Read the existing data from the file
    # Concatenate the cleaned data to the old data
    df_cleaned = old_data

    # Analyze, visualize
    print("\r\nAverage prices in defferents websites by product:")
    print(analyze_data_by_diff_sites(df_cleaned))
    plot_data(analyze_data_by_diff_sites(df_cleaned)[["grouped_title", "mean_all_sites", "min_all_sites", "max_all_sites", "cheapest_site", "most_expensive_site"]], "Average defferents websites Prices by Product")
    
    print("\r\nAverage promotion par group:")
    print(promotions_par_categorie(df_cleaned))
    plot_data(promotions_par_categorie(df_cleaned), "Average promotion par group")
    
    print("\r\nAverage prices in same website by product:")
    print(analyze_data_in_same_site(df_cleaned))
    plot_data(analyze_data_in_same_site(df_cleaned), "Average prices in same website by product")
    
    print("\r\nPrices by sites:")
    print(analyze_data_in_same_site_grouped_sites(df_cleaned))
    plot_data(analyze_data_in_same_site_grouped_sites(df_cleaned), "Prices by sites")