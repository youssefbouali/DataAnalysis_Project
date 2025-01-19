import pandas as pd
import matplotlib.pyplot as plt
import re
from rapidfuzz import fuzz
import seaborn as sns


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
def find_similar_noms(nom, nom_list, threshold=75):
    similar_noms = []
    for other_nom in nom_list:
        # Compute similarity score between nom and other nom
        score = fuzz.ratio(nom, other_nom)
        if score >= threshold:
            similar_noms.append((nom, other_nom, score))
    return similar_noms


def analyse_get_top_product_price_variation(df):
    # Normalize product names
    df['normalized_nom'] = df['nom'].apply(normalize_text)
    df['normalized_description'] = df['description'].apply(lambda x: normalize_text(x) if pd.notna(x) else "")
    
    df['nom_and_description'] = df['normalized_nom']+" "+df['normalized_description']
    #df['nom_and_description'] = df['normalized_nom']
    
    # Apply fuzzy matching to group similar product names
    unique_noms = df['nom_and_description'].unique()
    nom_groups = {}

    for nom in unique_noms:
        group = find_similar_noms(nom, unique_noms)
        for _, other_nom, _ in group:
            nom_groups[other_nom] = nom  # Group similar product names

    # Map the grouped noms back to the DataFrame
    df['grouped_nom'] = df['nom_and_description'].map(lambda x: nom_groups.get(x, x))
    
    # Remove duplicates based on product name and website before counting occurrences
    df_unique = df.drop_duplicates(subset=['grouped_nom', 'website'])
    
    # Count the occurrences of each product by website
    product_counts = df_unique.groupby(["grouped_nom", "website"]).size().reset_index(name='count')
    
    # Find the product with the maximum count across all websites
    top_product = product_counts.groupby('grouped_nom').agg({'count': 'sum'}).idxmax().iloc[0]

    # Get the details of that top product across websites
    top_product_data = product_counts[product_counts['grouped_nom'] == top_product]
    
    # Extract price variations for that product across websites
    price_variations = df[df['grouped_nom'] == top_product].drop_duplicates(subset=['website'])[['website', 'prix']]

    return top_product, price_variations.sort_values(by='prix', ascending=True)


def visualisation_plot_price_variations(price_variations, product_name):
    # Visualize price variations by website
    plt.figure(figsize=(10, 6))
    plt.bar(price_variations['website'], price_variations['prix'], color='skyblue')
    plt.title(f"Price Variations for {product_name} Across Websites")
    plt.xlabel('Website')
    plt.ylabel('Price')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()



# Analyze data
#def analyze_data_by_diff_sites(df):
#
#    # Apply normalization to product noms
#    df['normalized_nom'] = df['nom'].apply(normalize_text)
#
#    # Apply fuzzy matching to group similar product noms
#    unique_noms = df['normalized_nom'].unique()
#    nom_groups = {}
#
#    for nom in unique_noms:
#        group = find_similar_noms(nom, unique_noms)
#        for _, other_nom, _ in group:
#            nom_groups[other_nom] = nom  # Group noms with high similarity
#
#    # Map the grouped noms back to the DataFrame
#    df['grouped_nom'] = df['normalized_nom'].map(lambda x: nom_groups.get(x, x))
#    
#    # Regrouper les données par nom et site
#    grouped_by_name_and_website = df.groupby(["grouped_nom", "website"])["prix"].agg(
#        min_samesite="min",
#        mean_samesite="mean",
#        max_samesite="max"
#    ).reset_index()
#
#    # Ajouter une colonne contenant le nombre de sites où chaque produit apparaît
#    site_counts = grouped_by_name_and_website.groupby("grouped_nom")["website"].nunique().reset_index(name="site_count")
#    
#
#    # Déterminer le site le plus cher et le moins cher pour chaque produit
#    extreme_sites = grouped_by_name_and_website.loc[
#        grouped_by_name_and_website.groupby("grouped_nom")["max_samesite"].idxmax(),
#        ["grouped_nom", "website"]
#    ].rename(columns={"website": "most_expensive_site"})
#    
#    extreme_sites["cheapest_site"] = grouped_by_name_and_website.loc[
#        grouped_by_name_and_website.groupby("grouped_nom")["min_samesite"].idxmin(),
#        "website"
#    ].values
#
#    # Statistiques générales agrégées par produit
#    final_grouped = grouped_by_name_and_website.groupby("grouped_nom")[["min_samesite", "mean_samesite", "max_samesite"]].agg(
#        min_all_sites=("min_samesite", "min"),
#        mean_all_sites=("mean_samesite", "mean"),
#        max_all_sites=("max_samesite", "max")
#    ).reset_index()
#
#    # Intégrer le nombre de sites et sites les plus chers et les moins chers dans les statistiques finales
#    final_grouped = final_grouped.merge(site_counts, on="grouped_nom", how="left")
#    final_grouped = final_grouped.merge(extreme_sites, on="grouped_nom", how="left")
#
#    # Filtrer les produits qui apparaissent sur plusieurs sites
#    final_grouped = final_grouped[final_grouped["site_count"] > 1]
#    final_grouped = final_grouped[final_grouped["most_expensive_site"] != final_grouped["cheapest_site"] ]
#
#    # Reset the index so 'nom' and 'website' are regular columns
#    final_grouped = final_grouped.reset_index()
#
#    # Get the row with the maximum 'count'
#    final_grouped = final_grouped[final_grouped["site_count"] == final_grouped["site_count"].max()]
#
#    return final_grouped


# Analyze data
def analyse_promotions_par_categorie(df):
    # Filter products on promotion
    promotion_df = df[df['promotion'] != ""]

    # Count promotions by category
    promotions_par_categorie = promotion_df.groupby(['category', 'promotion'])['promotion'].size().reset_index(name="count")

    # Sort by 'count' in descending order and get the top 5
    top_promotions = promotions_par_categorie.sort_values(by='count', ascending=False).head(10).sort_values(by='count', ascending=True)

    return top_promotions


def visualisation_plot_promotions(promotions_par_categorie, title="Promotion Count by Category and Promotion Type", xlabel="Category", ylabel="Promotion Count"):
    # Create a Seaborn barplot for better visual representation
    plt.figure(figsize=(12, 6))
    sns.barplot(data=promotions_par_categorie, 
        x='category', 
        y='count', 
        hue='promotion', 
        palette="Set2")
    
    # Customize the plot
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()



# Function to group by 'nom', 'website', and 'date_scraped', and sort by count
def analyse_group_by_nom_website_date(df):
    # Group by 'nom' and 'website' and calculate min, mean, max, and count of 'prix'
    avg_prices = df.groupby(["nom", "website"])["prix"].agg(["min", "mean", "max", "count"])

    # Filter out rows where the min price is equal to the max price
    grouped = avg_prices[avg_prices["min"] != avg_prices["max"]]

    # Sort by 'count' in descending order to get the top products
    grouped_sorted = grouped.sort_values(by='count', ascending=False)

    # Get the top 5 products with the most occurrences
    products_by_date = grouped_sorted.groupby('nom').head(1).sort_values(by='count', ascending=False).head(10)

    # Reset the index so 'nom' becomes a column again
    products_by_date = products_by_date.reset_index()

    return products_by_date


# Function to plot price variations by 'date_scraped' for the top 5 products
def visualisation_plot_price_variations_by_date(df, products_by_date):
    # Filter the original dataframe to include only the top 5 products
    filtered_df = df[df['nom'].isin(products_by_date['nom'])].copy()

    # Replace NaN values in the 'promotion' column with 'No promo' using .loc
    filtered_df.loc[:, 'promotion'] = filtered_df['promotion'].fillna("No promo")

    # Create the Seaborn plot showing price variation by date
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=filtered_df, x='date_scraped', y='prix', hue='nom', marker='o')

    # Add promotion names as annotations on the plot
    for _, row in filtered_df.iterrows():
        plt.text(row['date_scraped'], row['prix'], row['promotion'], 
                 color='black', fontsize=9, ha='center', va='bottom')

    # Customize the plot
    plt.title("Price Variation by Date for Top Products")
    plt.xlabel("Date Scraped")
    plt.ylabel("Price (USD)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()




# Analyze data
#def analyze_data_in_same_site(df):
#    # Same product in month
#    avg_prices = df.groupby(["nom", "website"])["prix"].agg(["min", "mean", "max", "count"])
#    avg_prices = avg_prices[avg_prices["min"] != avg_prices["max"]]
#
#    # Reset the index so 'nom' and 'website' are regular columns
#    avg_prices = avg_prices.reset_index()
#
#    # Get the row with the maximum 'count'
#    max_count_row = avg_prices[avg_prices["count"] == avg_prices["count"].max()]
#
#    return max_count_row



# Analyze data
#def analyze_data_in_all_days(df, nom=None, website=None):
#
#    #same product in month
#    grouped = df.groupby(["nom", "website"]).agg(count=("prix", "count"))
#    
#    if not nom and not website:
#        filtered = grouped[grouped["count"] > 1]
#    elif nom and website:
#        filtered = grouped[grouped["count"] > 1 and grouped["nom"] == nom and grouped["website"] == website]
#    elif nom:
#        filtered = grouped[grouped["count"] > 1 and grouped["nom"] == nom]
#    elif website:
#        filtered = grouped[grouped["count"] > 1 and grouped["website"] == website]
#
#    # Add 'date_scraped' back if needed (ensure it's a column in the original dataframe)
#    if "date_scraped" in df.columns:
#        filtered = filtered.reset_index().merge(df[["nom", "website", "date_scraped", "prix"]], on=["nom", "website"])
#        grouped_by_date = filtered.groupby(["date_scraped"]).agg(total_products=("count", "sum"),sum_prix=("prix", "sum"))
#        return grouped_by_date
#
#    return grouped_by_date



# Analyze data
def analyse_data_in_same_site_grouped_sites(df, nom=None, website=None):
    # Group by 'nom' and 'website' to get the average prices and count
    avg_prices = df.groupby(["nom", "website"])["prix"].agg(["min", "mean", "max", "count"])

    # Filter out rows where min equals max
    avg_prices_filtered = avg_prices[avg_prices["min"] != avg_prices["max"]]

    # Group by 'website' and calculate mean of 'min', 'mean', and 'max'
    grouped_by_date = avg_prices.groupby(["website"]).agg({
        'mean': 'mean',
        'min': 'mean',
        'max': 'mean'
    }).reset_index()

    # Return the result sorted by 'min' in ascending order
    return grouped_by_date.sort_values(by='min', ascending=True)


# Plot data
def visualisation_plot_data(avg_prices, nom="Average Prices by Product", xlabel="Product", ylabel="Price (USD)", x=None, y=None):
    # Ensure the DataFrame is indexed properly for plotting
    avg_prices = avg_prices.reset_index()  # Reset index for clean plotting
    
    # Plot the data
    avg_prices.plot(kind="bar", title=nom, xlabel=xlabel, ylabel=ylabel, x=x, y=y)
    
    # Adjust layout for better display
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()



# Main execution
if __name__ == "__main__":
    old_data = pd.read_csv("Electromenagerscleaned_data.csv")  # Read the existing data from the file
    # Concatenate the cleaned data to the old data
    df_cleaned = old_data

    # Analyze, visualize
    #print("\r\nAverage prices in defferents websites by product:")
    #print(analyze_data_by_diff_sites(df_cleaned))
    #plot_data(analyze_data_by_diff_sites(df_cleaned)[["grouped_nom", "min_all_sites", "mean_all_sites", "max_all_sites", "cheapest_site", "most_expensive_site"]], "Average defferents websites Prices by Product", "Product", "Price (USD)", "grouped_nom", ["min_all_sites", "mean_all_sites", "max_all_sites"])
    
    

    # Analyze data and visualize
    # Get the top product and price variations
    top_product, price_variations = analyse_get_top_product_price_variation(df_cleaned)
    
    print(f"Top Product: {top_product}")
    print("Price variations by website:")
    print(price_variations)
    # Plot the price variations
    visualisation_plot_price_variations(price_variations, top_product)
    
    
    print("\r\nAverage promotion par group:")
    print(analyse_promotions_par_categorie(df_cleaned))
    visualisation_plot_promotions(analyse_promotions_par_categorie(df_cleaned), 
        title="Promotion Count by Category and Promotion Type", 
        xlabel="Category", 
        ylabel="Promotion Count")

    
    #print("\r\nAverage prices in same website by product:")
    #print(analyze_data_in_same_site(df_cleaned))
    #plot_data(analyze_data_in_same_site(df_cleaned), "Average prices in same website by product", "Product", "Price (USD)", "nom", ["min", "max"])
    
    products_by_date = analyse_group_by_nom_website_date(df_cleaned)
    print("\r\nTop 5 Products by Occurrence:")
    print(products_by_date)
    # Plot price variations by date for the top 5 products
    visualisation_plot_price_variations_by_date(df_cleaned, products_by_date)
    
    
    print("\r\nPrices by sites:")
    print(analyse_data_in_same_site_grouped_sites(df_cleaned))
    visualisation_plot_data(analyse_data_in_same_site_grouped_sites(df_cleaned), "Prices by sites", "Product", "Price (USD)", "website", ["min", "mean", "max"])