import pandas as pd
from bs4 import BeautifulSoup
import re
import json

# Load the CSV data
df = pd.read_csv('Electromenagerscleaned_data.csv')

# Load site configurations
with open('platformes.json', 'r') as file:
    sites = json.load(file)







# Define the extraction function
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


mask = df['date_scraped'] == "2025-02-02 22:03:30"

# Update only the matching rows
df.loc[mask, 'characteristics'] = df.loc[mask].apply(
    lambda row: normalize_characteristics(extract_characteristics(row['html'], get_site_config(row['website']))) 
    if isinstance(row['html'], str) and row['html'].strip()
    else {}, 
    axis=1
)

df.loc[mask, 'text_characteristics'] = df.loc[mask, 'characteristics'].apply(json_to_text)





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
df.to_csv('Electromenagerscleaned_data.csv', index=False)
df.to_excel("Electromenagerscleaned_data.xlsx", index=False, engine="openpyxl")





# Inspect the results
print(df.loc[mask, ['website', 'html', 'characteristics']])