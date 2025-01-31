import pandas as pd
from datetime import datetime
import re

# Load the CSV data into a pandas DataFrame
df = pd.read_csv('temp2Electromenagerscleaned_data.csv')
#df2 = pd.read_csv('temp3Electromenagerscleaned_data.csv')

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


# #df['description'] = df['description'].apply(lambda x: "" if x == "Description not found" else x)

#df["description"] = df["description"].fillna("").astype(str).str.replace(r"specifications |specifications product ", "", regex=True)


# Function to normalize text
def normalize_text(text):
    if isinstance(text, str):
        text = text.lower()  # Convert to lowercase
        # nom = re.sub(r'[^a-z\s]', '', text)  # Uncomment if needed for special character removal
        return text
    else:
        # Convert non-string inputs to a string or handle them appropriately
        return str(text) if text is not None else ""
        
#df['normalized_nom'] = df['nom'].apply(normalize_text)
#df['normalized_description'] = df['nom'].apply(lambda x: normalize_text(x) if pd.notna(x) else "")


#df['nom_and_description'] = df['nom']+" "+df['description']
#df = df.drop(columns=['nom_and_description'])


# List of columns to check and replace if empty
#columns_to_check = ['url', 'description', 'html', 'normalized_description', 'nom_and_description']
#
# # Loop through each row and check if the specified columns are empty
#for index, row in df.iterrows():
#    for column in columns_to_check:
#        if pd.isna(row[column]) or row[column] == '':
#            # Find a non-empty value for the same column from rows with the same 'nom'
#            replacement = df[(df['nom'] == row['nom']) & (df['website'] == row['website']) & df[column].notna() & (df[column] != '')]
#            if not replacement.empty:
#                # Replace the empty field with the first non-empty value found
#                df.at[index, column] = replacement.iloc[0][column]



#df = df.drop(columns=['caracteristiques'])
#df = df.drop(columns=['text_caracteristiques'])

# Apply the function to the DataFrame
#final_df = df


#df['normalized_description'] = df['description'].apply(lambda x: normalize_text(x) if pd.notna(x) else "")
#df['normalized_nom']+" "+df['normalized_description']
#df['normalized_nom'] = df['nom'].apply(normalize_text)
#df['normalized_description'] = df['description'].apply(lambda x: normalize_text(x) if pd.notna(x) else "")
df['nom_and_description'] = df['normalized_nom']+" "+df['normalized_description']

# Save the modified DataFrame back to a CSV file
df.to_csv('temp2Electromenagerscleaned_data.csv', index=False)
df.to_excel("temp2Electromenagerscleaned_data.xlsx", index=False, engine="openpyxl")  # Using openpyxl for Excel support

# Optionally, print the final modified DataFrame
print(df)
