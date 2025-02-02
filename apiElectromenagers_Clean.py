from flask import Flask, jsonify, request, send_file, render_template_string
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from rapidfuzz import fuzz
import seaborn as sns
    
from difflib import SequenceMatcher

from flask_cors import CORS  # <-- Import CORS

app = Flask(__name__)
CORS(app)

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
def find_similar_noms(nom, nom_list, threshold=70):
    similar_noms = []
    for other_nom in nom_list:
        score = fuzz.ratio(nom, other_nom)
        if score >= threshold:
            similar_noms.append((nom, other_nom, score))
    return similar_noms

# Function to find similar noms using RapidFuzz with token sort ratio
#def find_similar_noms(nom, nom_list, threshold=70):
#    similar_noms = []
#    for other_nom in nom_list:
#        # Compute similarity score using token sort ratio
#        score = fuzz.token_sort_ratio(nom, other_nom)
#        if score >= threshold:
#            similar_noms.append((nom, other_nom, score))
#    return similar_noms


# Function to find similar noms using difflib
def find_similar_noms_difflib(nom, nom_list, threshold=0.7):
    similar_noms = []
    for other_nom in nom_list:
        score = SequenceMatcher(None, nom, other_nom).ratio()
        if score >= threshold:
            similar_noms.append((nom, other_nom, score))
    return similar_noms
 

# Analyze promotions by category
def promotions_par_categorie(df):
    promotion_df = df[df['promotion'] != ""]
    promotions = (
        promotion_df.groupby(['category', 'promotion'])
        .size()
        .reset_index(name="count")
    )
    return promotions.to_dict(orient='records')


def analyse_get_top_product_price_variation(df):
    # Normalize product names
    #df['normalized_nom'] = df['nom'].apply(normalize_text)
    #df['normalized_description'] = df['description'].apply(lambda x: normalize_text(x) if pd.notna(x) else "")
    
    #df['nom_and_description'] = df['normalized_nom']+" "+df['normalized_description']
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
    #plt.xticks(rotation=45, ha="right")

    img_stream = BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    return img_stream


# Analyze data
def analyse_promotions_par_categorie(df):
    # Filter products on promotion
    promotion_df = df[df['promotion'] != ""]

    # Count promotions by category
    promotions_par_categorie = promotion_df.groupby(['category', 'promotion'])['promotion'].size().reset_index(name="count")

    # Sort by 'count' in descending order and get the top 5
    top_promotions = promotions_par_categorie.sort_values(by='count', ascending=False).head(10)

    return top_promotions


def visualisation_plot_promotions(promotions_par_categorie, title="Promotion Count by Category and Promotion Type", xlabel="Category", ylabel="Promotion Count"):
    # Create a Seaborn barplot for better visual representation
    plt.figure(figsize=(12, 6))
    sns.barplot(data=promotions_par_categorie.sort_values(by='count', ascending=True), 
        x='category', 
        y='count', 
        hue='promotion', 
        palette="Set2")
    
    # Customize the plot
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")

    img_stream = BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    return img_stream


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
    filtered_df.loc[:, 'promotion'] = filtered_df['promotion'].fillna("")

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

    img_stream = BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    return img_stream


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

    img_stream = BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    return img_stream



@app.route('/search_similar_products', methods=['GET'])
def search_similar_products():
    # Parse input JSON
    product_name = request.args.get('product_name', '').lower()

    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    # Load dataset
    try:
        df = pd.read_csv("Electromenagerscleaned_data.csv")
    except FileNotFoundError:
        return jsonify({"error": "Dataset not found"}), 500

    # Normalize noms in the dataset
    df['normalized_nom'] = df['nom'].apply(normalize_text)

    # Find similar noms using difflib
    similar_noms = find_similar_noms_difflib(product_name, df['normalized_nom'].unique())

    if not similar_noms:
        return jsonify({"message": "No similar products found"}), 404

    # Filter the dataframe for matching noms
    matching_noms = [nom[1] for nom in similar_noms]
    filtered_df = df[df['normalized_nom'].isin(matching_noms)]

    # Group results by nom and website, preserving original indexes
    grouped_results = (
        filtered_df.groupby(["nom", "website"], as_index=False)
        .agg(
            mean_price=("prix", "mean"),
            min_price=("prix", "min"),
            max_price=("prix", "max"),
            count=("prix", "count"),
            original_indexes=("normalized_nom", lambda x: (filtered_df.loc[x.index].index + 2).tolist())
        )
    ).sort_values(by="min_price")

    # Convert results to dictionary
    result_data = grouped_results.to_dict(orient='records')

    #return jsonify({
    #    "input_product": product_name,
    #    "similar_products": result_data
    #})

    return jsonify(result_data)


@app.route('/all_promotions_par_categorie', methods=['GET'])
def analyze_promotions():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    analysis_results = promotions_par_categorie(df)
    return jsonify(analysis_results)




@app.route('/analyse_top_product', methods=['GET'])
def api_analyse_top_product():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    top_product, price_variations = analyse_get_top_product_price_variation(df)
    return jsonify({
        'top_product': top_product,
        'price_variations': price_variations.to_dict(orient='records')
    })

@app.route('/plot_analyse_top_product', methods=['GET'])
def plot_analyse_top_product():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    top_product, price_variations = analyse_get_top_product_price_variation(df)
    img_stream = visualisation_plot_price_variations(price_variations, top_product)
    return send_file(img_stream, mimetype='image/png')
    

@app.route('/analyse_promotions', methods=['GET'])
def api_analyse_promotions():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    top_promotions = analyse_promotions_par_categorie(df)
    return jsonify({'top_promotions': top_promotions.to_dict(orient='records')})

@app.route('/plot_analyse_promotions', methods=['GET'])
def plot_analyse_promotions():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    img_stream = visualisation_plot_promotions(analyse_promotions_par_categorie(df), 
        title="Promotion Count by Category and Promotion Type", 
        xlabel="Category", 
        ylabel="Promotion Count")
    return send_file(img_stream, mimetype='image/png')


@app.route('/products_by_date', methods=['GET'])
def products_by_date():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    products_by_date = analyse_group_by_nom_website_date(df_cleaned)
    return jsonify({'products_by_date': products_by_date.to_dict(orient='records')})

@app.route('/plot_products_by_date', methods=['GET'])
def plot_products_by_date():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    img_stream = visualisation_plot_price_variations_by_date(df, analyse_group_by_nom_website_date(df))
    return send_file(img_stream, mimetype='image/png')


@app.route('/site_grouped_sites', methods=['GET'])
def site_grouped_sites():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    site_grouped_sites = analyse_data_in_same_site_grouped_sites(df)
    return jsonify({'site_grouped_sites': site_grouped_sites.to_dict(orient='records')})

@app.route('/plot_site_grouped_sites', methods=['GET'])
def plot_site_grouped_sites():
    df = pd.read_csv("Electromenagerscleaned_data.csv")
    img_stream = visualisation_plot_data(analyse_data_in_same_site_grouped_sites(df), "Prices by sites", "Product", "Price (USD)", "website", ["min", "mean", "max"])
    return send_file(img_stream, mimetype='image/png')


@app.route('/')
def home():
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Data Analysis Web App</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .container { width: 80%; margin: 0 auto; padding: 20px; }
                .button { margin: 10px 0; padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                .results { margin-top: 20px; }
                pre { background-color: #f4f4f4; padding: 10px; }
                .plot { margin-top: 20px; text-align: center; }
                #loader { display: none; }
                .result-item { margin: 10px 0; padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9; }
                .result-item h3 { margin: 0; }
                .result-item .key { font-weight: bold; }
                .result-item .value { margin-left: 10px; }
                .search-bar { margin-right: 10px; }
            </style>
        </head>
        <body>

            <div class="container">
                <h1>Products Analysis Web App</h1>

                <!-- Search Bar and Button -->
                <input type="text" id="searchInput" class="search-bar" placeholder="Search Similar Products">
                <button class="button" onclick="searchSimilarProducts()">Search Similar Products</button>
                <button class="button" onclick="getData('analyse_promotions')">Analyze Promotions by Category</button>
                <button class="button" onclick="getData('analyse_top_product')">Analyze Product by Different Sites</button>
                <button class="button" onclick="getData('site_grouped_sites')">Analyze Products in Same Site by Date</button>
                <button class="button" onclick="getData('site_grouped_sites')">Analyze Prices by All Sites</button>
                
                <br />
                <button class="button" onclick="generatePlot('plot_analyse_promotions')">Visualize Promotions by Category</button>
                <button class="button" onclick="generatePlot('plot_analyse_top_product')">Visualize Product by Different Sites</button>
                <button class="button" onclick="generatePlot('plot_products_by_date')">Visualize Products in Same Site by Date</button>
                <button class="button" onclick="generatePlot('plot_site_grouped_sites')">Visualize Prices by All Sites</button>

                <div id="loader">Loading...</div>
                <div class="plot" id="plotContainer"></div>

                <div class="results">
                    <h2>Results</h2>
                    <div id="resultOutput"></div>
                </div>

            </div>

            <script>
                const apiBaseUrl = 'http://localhost:5000/';  // Assuming your Flask server is running locally

                // Function to show loader
                function showLoader() {
                    document.getElementById('loader').style.display = 'block';
                }

                // Function to hide loader
                function hideLoader() {
                    document.getElementById('loader').style.display = 'none';
                }

                // Function to call Flask API and display results
                function getData(endpoint) {
                    showLoader();  // Show loader before the request

                    fetch(apiBaseUrl + endpoint)
                        .then(response => response.json())
                        .then(data => {
                            hideLoader();  // Hide loader once data is fetched
                            displayData(data);  // Function to display data in divs
                        })
                        .catch(error => {
                            hideLoader();  // Hide loader in case of an error
                            document.getElementById('resultOutput').innerHTML = `Error: ${error}`;
                        });
                }

                // Function to handle Search Similar Products request with search query
                function searchSimilarProducts() {
                    const query = document.getElementById('searchInput').value;  // Get the search query

                    if (query) {
                        showLoader();  // Show loader before the request

                        fetch(apiBaseUrl + 'search_similar_products?product_name=' + encodeURIComponent(query))
                            .then(response => response.json())
                            .then(data => {
                                hideLoader();  // Hide loader once data is fetched
                                displayData(data);  // Function to display data in divs
                            })
                            .catch(error => {
                                hideLoader();  // Hide loader in case of an error
                                document.getElementById('resultOutput').innerHTML = `Error: ${error}`;
                            });
                    } else {
                        alert('Please enter a search term.');
                    }
                }

                // Function to display JSON data in divs
                function displayData(data) {
                    const resultDiv = document.getElementById('resultOutput');
                    resultDiv.innerHTML = '';  // Clear previous results

                    // Recursive function to display data as divs
                    function createDivs(item, parentDiv) {
                        if (Array.isArray(item)) {
                            item.forEach((subItem, index) => {
                                const div = document.createElement('div');
                                div.className = 'result-item';
                                div.innerHTML = `<h3>Item ${index + 1}:</h3>`;
                                createDivs(subItem, div); // Recursively handle array elements
                                parentDiv.appendChild(div);
                            });
                        } else if (typeof item === 'object' && item !== null) {
                            Object.keys(item).forEach(key => {
                                const div = document.createElement('div');
                                div.className = 'key-value-pair';
                                div.innerHTML = `<span class="key">${key}:</span>`;
                                const valueDiv = document.createElement('div');
                                valueDiv.className = 'value';
                                
                                // Recursively handle nested objects or arrays
                                createDivs(item[key], valueDiv);
                                
                                div.appendChild(valueDiv);
                                parentDiv.appendChild(div);
                            });
                        } else {
                            const div = document.createElement('div');
                            div.className = 'value';
                            div.innerHTML = `${item}`; // Display the value if it's a simple data type
                            parentDiv.appendChild(div);
                        }
                    }

                    // Call the recursive function on the data
                    createDivs(data, resultDiv);
                }


                // Function to generate plot
                function generatePlot(endpoint) {
                
                    showLoader();  // Show loader before the request

                    fetch(apiBaseUrl + endpoint)
                        .then(response => response.blob())
                        .then(imageBlob => {
                            hideLoader();  // Hide loader once the plot is generated
                            const imageUrl = URL.createObjectURL(imageBlob);
                            document.getElementById('resultOutput').innerHTML = `<img src="${imageUrl}" alt="Generated Plot" />`;
                        })
                        .catch(error => {
                            hideLoader();  // Hide loader in case of an error
                            document.getElementById('resultOutput').innerHTML = `Error generating plot: ${error}`;
                        });
                        
                        
                }
            </script>

        </body>
        </html>
    """)


if __name__ == "__main__":
    app.run(debug=True)
