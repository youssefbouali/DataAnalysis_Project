from flask import Flask, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from rapidfuzz import fuzz
import re

# Import functions from your existing code
def normalize_title(title):
    title = title.lower()
    return title

def find_similar_titles(title, title_list, threshold=70):
    similar_titles = []
    for other_title in title_list:
        score = fuzz.ratio(title, other_title)
        if score >= threshold:
            similar_titles.append((title, other_title, score))
    return similar_titles

def analyze_data_by_diff_sites(df):
    df['normalized_title'] = df['nom'].apply(normalize_title)
    unique_titles = df['normalized_title'].unique()
    title_groups = {}
    for title in unique_titles:
        group = find_similar_titles(title, unique_titles)
        for _, other_title, _ in group:
            title_groups[other_title] = title
    df['grouped_title'] = df['normalized_title'].map(lambda x: title_groups.get(x, x))
    grouped_by_name_and_website = df.groupby(["grouped_title", "website"])["prix"].agg(
        mean_samesite="mean",
        min_samesite="min",
        max_samesite="max"
    ).reset_index()
    site_counts = grouped_by_name_and_website.groupby("grouped_title")["website"].nunique().reset_index(name="site_count")
    extreme_sites = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("grouped_title")["max_samesite"].idxmax(),
        ["grouped_title", "website"]
    ].rename(columns={"website": "most_expensive_site"})
    extreme_sites["cheapest_site"] = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("grouped_title")["min_samesite"].idxmin(),
        "website"
    ].values
    final_grouped = grouped_by_name_and_website.groupby("grouped_title")[["mean_samesite", "min_samesite", "max_samesite"]].agg(
        mean_all_sites=("mean_samesite", "mean"),
        min_all_sites=("min_samesite", "min"),
        max_all_sites=("max_samesite", "max")
    ).reset_index()
    final_grouped = final_grouped.merge(site_counts, on="grouped_title", how="left")
    final_grouped = final_grouped.merge(extreme_sites, on="grouped_title", how="left")
    final_grouped = final_grouped[final_grouped["site_count"] > 1]
    return final_grouped

app = Flask(__name__)

@app.route('/analyze', methods=['GET'])
def analyze():
    # Receive raw data
    raw_data = request.json
    df_cleaned = clean_data(raw_data)
    
    # Get analysis results
    result = analyze_data_by_diff_sites(df_cleaned)
    
    # Return as JSON response
    return jsonify(result.to_dict(orient="records"))

@app.route('/plot', methods=['GET'])
def plot():
    # Receive raw data for plotting
    raw_data = request.json
    df_cleaned = clean_data(raw_data)
    
    # Generate analysis data
    plot_data = analyze_data_by_diff_sites(df_cleaned)[["grouped_title", "mean_all_sites", "min_all_sites", "max_all_sites", "cheapest_site", "most_expensive_site"]]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_data.plot(kind="bar", ax=ax, title="Average Prices by Product")
    ax.set_xlabel('Product')
    ax.set_ylabel('Price (USD)')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Save the plot to a BytesIO object and encode as base64
    img_stream = BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_base64 = base64.b64encode(img_stream.getvalue()).decode('utf-8')

    return jsonify({'image': img_base64})

if __name__ == '__main__':
    app.run(debug=True)
