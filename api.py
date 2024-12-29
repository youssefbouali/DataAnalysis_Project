from flask import Flask, jsonify, request
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)

# Helper functions (same as your provided code)
def analyze_data_in_same_site(df):
    avg_prices = df.groupby(["nom", "website"])["prix"].agg(["mean", "min", "max", "count"])
    return avg_prices.to_dict()

def analyze_data_by_diff_sites(df):
    grouped_by_name_and_website = df.groupby(["nom", "website"])["prix"].agg(
        mean_samesite="mean",
        min_samesite="min",
        max_samesite="max"
    ).reset_index()

    site_counts = grouped_by_name_and_website.groupby("nom")["website"].nunique().reset_index(name="site_count")

    extreme_sites = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("nom")["max_samesite"].idxmax(),
        ["nom", "website"]
    ].rename(columns={"website": "most_expensive_site"})

    extreme_sites["cheapest_site"] = grouped_by_name_and_website.loc[
        grouped_by_name_and_website.groupby("nom")["min_samesite"].idxmin(),
        "website"
    ].values

    final_grouped = grouped_by_name_and_website.groupby("nom")[["mean_samesite", "min_samesite", "max_samesite"]].agg(
        mean_all_sites=("mean_samesite", "mean"),
        min_all_sites=("min_samesite", "min"),
        max_all_sites=("max_samesite", "max")
    ).reset_index()

    final_grouped = final_grouped.merge(site_counts, on="nom", how="left")
    final_grouped = final_grouped.merge(extreme_sites, on="nom", how="left")
    
    return final_grouped.to_dict()

def plot_data(df):
    avg_prices = analyze_data_by_diff_sites(df)
    avg_prices_df = pd.DataFrame(avg_prices)  # Convert dict back to DataFrame for plotting
    avg_prices_df.plot(kind="bar", title="Average Prices by Product", xlabel="Product", ylabel="Price (USD)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("avg_prices_plot.png")  # Save the plot as a file
    return "Plot saved as avg_prices_plot.png"

def export_data(df, filename="cleaned_data.csv"):
    df.to_csv(filename, index=False)
    df.to_excel("cleaned_data.xlsx", index=False, engine="openpyxl")
    return f"Data exported to '{filename}'"

# API Routes
@app.route('/analyze_same_site', methods=['GET'])
def api_analyze_same_site():
    df = pd.read_csv("cleaned_data.csv")  # Load the data from CSV
    result = analyze_data_in_same_site(df)
    return jsonify(result)

@app.route('/analyze_diff_sites', methods=['GET'])
def api_analyze_diff_sites():
    df = pd.read_csv("cleaned_data.csv")  # Load the data from CSV
    result = analyze_data_by_diff_sites(df)
    return jsonify(result)

@app.route('/plot_data', methods=['GET'])
def api_plot_data():
    df = pd.read_csv("cleaned_data.csv")  # Load the data from CSV
    plot_result = plot_data(df)
    return plot_result

@app.route('/export_data', methods=['GET'])
def api_export_data():
    df = pd.read_csv("cleaned_data.csv")  # Load the data from CSV
    export_result = export_data(df)
    return export_result

if __name__ == '__main__':
    app.run(debug=True)
