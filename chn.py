import pandas as pd
from datetime import datetime
import re

# Load the CSV data into a pandas DataFrame
df = pd.read_csv('Electromenagerscleaned_data.csv')
df2 = pd.read_csv('temp2Electromenagerscleaned_data.csv')

# Function to change the date when it matches the specific pattern
def change_date_pattern(df, pattern_date, new_date):
    for i in range(len(df)):
        current_date = df.loc[i, 'date_scraped']
        if current_date.startswith(pattern_date):  # Check if the date starts with the specified pattern
            df.loc[i, 'date_scraped'] = new_date  # Replace the date with the new one
    return df

# Function to delete rows with a specific date
def delete_rows_with_date(df, specific_date):
    # Filter out rows where 'date_scraped' matches the specific date
    df_cleaned = df[df['date_scraped'] != specific_date]
    return df_cleaned

# Define the pattern to detect and the new date
pattern_date = '2025-01-06 20:05:00'  # The pattern to match   
new_date = '2025-01-06 20:05:47'  # The new date to replace with

# Apply the function to change the date where it matches the pattern
#final_df = change_date_pattern(df, pattern_date, new_date)

# Define the date to delete
date_to_delete = '2025-01-07 04:55:20'  # Example: The date you want to delete 2025-01-14 22:21:39


# Apply the function to delete rows with the specific date
#final_df = delete_rows_with_date(df, date_to_delete)

#final_df = df.drop(df.index[1555:])

# Function to modify the promotion field to "hhh" if website is sharpusa.com
def modify_promotion_for_sharpusa(df):
    # Set 'promotion' to 'hhh' for rows where 'website' is 'sharpusa.com'
    df.loc[df['website'] == 'sharpusa.com', 'promotion'] = ''
    return df


#final_df = modify_promotion_for_sharpusa(df)


#final_df = pd.concat([df, df2], ignore_index=True)

#df['nom'] = df.apply(
#    lambda row: (
#        print(f"Original nom: {row['nom']}"),  # Print original nom value
#        re.sub(r'^\S+\s', '', row['nom']) if row['website'] == "us-appliance.com" and row['nom'] else row['nom']
#    )[1],  # The second element is the modified 'nom'
#    axis=1
#)


df['description'] = df['description'].apply(lambda x: "" if x == "Description not found" else x)

# Save the modified DataFrame back to a CSV file
df.to_csv('Electromenagerscleaned_data.csv', index=False)
df.to_excel("Electromenagerscleaned_data.xlsx", index=False, engine="openpyxl")  # Using openpyxl for Excel support

# Optionally, print the final modified DataFrame
print(df)
