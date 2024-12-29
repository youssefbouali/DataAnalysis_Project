import pandas as pd

import matplotlib.pyplot as plt




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
    
    
    
    old_data = pd.read_csv("cleaned_data.csv")  # Read the existing data from the file
    # Concatenate the cleaned data to the old data

    
    # Analyze, visualize, and export data
    
    print("Average prices in same website by product:")
    print(analyze_data_in_same_site(old_data))
    print("\r\nAverage prices in defferents websites by product:")
    print(analyze_data_by_diff_sites(old_data))
    plot_data(old_data)