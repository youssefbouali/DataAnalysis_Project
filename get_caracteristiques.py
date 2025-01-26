from bs4 import BeautifulSoup
import re

config = {
    "sites": {
        "bestbuy.com": {  # New site configuration for the updated HTML structure
            "sections": {
                "SPECIFICATIONS": {
                    "sectionSelector": "li.zebra-list-item",  # Targeting the li element with specifications
                    "rowsSelector": ".zebra-row",  # Each specification is within a 'zebra-row'
                    "specNameSelector": ".property",  # Property names are in the 'property' class
                    "specValueSelector": ".w-full"  # Values are inside elements with 'w-full' class
                }
            }
        },
        "sharpusa.com": {  # New site configuration for the updated HTML structure
            "sections": {
                "SPECIFICATIONS": {
                    "sectionSelector": "div.st-spec-cols-2.st-specifications-responsive",  # Target the div with specifications table
                    "rowsSelector": "tr",  # Each specification is within a <tr> element
                    "specNameSelector": "th.st-spec-caption",  # Property names are in <th> with class 'st-spec-caption'
                    "specValueSelector": "td.st-spec-data"  # Values are in <td> with class 'st-spec-data'
                }
            }
        },
        "costco.com": {
            "sections": {
                "SPECIFICATIONS": {
                    "sectionSelector": ".product-info-specs",
                    "rowsSelector": ".row",
                    "specNameSelector": ".spec-name",
                    "specValueSelector": ".col-xs-6.col-md-7.col-lg-8"
                }
            }
        },
        "us-appliance.com": {  # New configuration for BlueStar site (example from the HTML provided)
            "sections": {
                "SPECIFICATIONS": {
                    "sectionSelector": ".tab-content-info--description",  # Targeting the div with the specifications content
                    "rowsSelector": "li",  # Each specification is within a 'li' element
                    "specNameSelector": "b",  # Property names are typically in the <b> element
                    "specValueSelector": "p"  # Values are inside <p> elements
                },
                "DIMENSIONS": {
                    "sectionSelector": ".tab-content-info--description",  # Same section for approximate dimensions
                    "rowsSelector": "p",  # Each dimension in <p> element
                    "specNameSelector": "b",  # Property names in <b> element
                    "specValueSelector": "p"  # Dimension values in <p> element
                }
            }
        },
        "geappliances.com": {
            "sections": {
                "APPEARANCE": {
                    "sectionSelector": ".productTabs-specs--table",
                    "nameSelector": "h3",
                    "rowsSelector": "tbody tr",
                    "specNameSelector": ".specName",
                    "specValueSelector": ".specValues"
                },
                "CAPACITY": {
                    "sectionSelector": ".productTabs-specs--table",
                    "nameSelector": "h3",
                    "rowsSelector": "tbody tr",
                    "specNameSelector": ".specName",
                    "specValueSelector": ".specValues"
                },
                "TECHNICAL": {
                    "sectionSelector": ".productTabs-specs--table",
                    "nameSelector": "h3",
                    "rowsSelector": "tbody tr",
                    "specNameSelector": ".specName",
                    "specValueSelector": ".specValues"
                }
            }
        },
        "sears.com": {  # Added configuration for the new site
            "sections": {
                "SPECIFICATIONS": {
                    "sectionSelector": "#specifications",  # Selector for the specifications tab
                    "rowsSelector": ".specs-ul",  # Each specification is within a 'specs-ul' list
                    "specNameSelector": ".list-key",  # Property names are in 'list-key'
                    "specValueSelector": ".list-value"  # Values are in 'list-value'
                },
                "DIMENSIONS": {
                    "sectionSelector": "#specifications",  # Same section for dimensions
                    "rowsSelector": ".specs-ul",  # Each dimension is in a 'specs-ul' list
                    "specNameSelector": ".list-key",  # Property names in 'list-key'
                    "specValueSelector": ".list-value"  # Dimension values in 'list-value'
                },
                "APPLIANCE_FEATURES": {
                    "sectionSelector": "#specifications",  # Section for appliance features
                    "rowsSelector": ".specs-ul",  # Each appliance feature is in a 'specs-ul' list
                    "specNameSelector": ".list-key",  # Property names in 'list-key'
                    "specValueSelector": ".list-value"  # Feature values in 'list-value'
                }
            }
        },
        "lg.com": {  # New site configuration for a new HTML structure with <ul> and <li>
            "sections": {
                "FEATURES": {
                    "sectionSelector": "ul.css-1he9hsx",  # Targeting the <ul> with the 'css-1he9hsx' class
                    "rowsSelector": "li",  # Each feature is within a 'li' element
                    "specNameSelector": None,  # No separate name; each <li> contains the feature description
                    "specValueSelector": None  # No separate value; the <li> text itself is the feature
                }
            }
        },
        "airportappliance.com": {  # New site configuration for LG
            "sections": {
                "SUMMARY": {
                    "sectionSelector": ".inline_sd_table",  # Table containing the summary section
                    "rowsSelector": "tr.inline_sd_cell_row",  # Each specification is within a 'tr' element
                    "specNameSelector": "td.inline_sd_even_cell, td.inline_sd_odd_cell",  # Spec names are in 'td' elements
                    "specValueSelector": "td.inline_sd_even_cell, td.inline_sd_odd_cell"  # Spec values are in 'td' elements
                },
                "CAPACITY": {
                    "sectionSelector": ".inline_sd_table",  # Table containing the capacity section
                    "rowsSelector": "tr.inline_sd_cell_row",  # Each specification is within a 'tr' element
                    "specNameSelector": "td.inline_sd_even_cell, td.inline_sd_odd_cell",  # Spec names are in 'td' elements
                    "specValueSelector": "td.inline_sd_even_cell, td.inline_sd_odd_cell"  # Spec values are in 'td' elements
                }
            }
        }
    }
}


# Example usage
bestbuy = """<li class="zebra-list-item mt-500 exposed-spec-container">
    <h5 class="my-200 font-500">Specifications</h5>
    <div class="zebra-row flex p-200 justify-content-between body-copy-lg">
        <div class="property w-full mr-700">Product Height</div>
        <div class="w-full">60.6 inches</div>
    </div>
    <div class="zebra-row flex p-200 justify-content-between body-copy-lg">
        <div class="property w-full mr-700">Product Width</div>
        <div class="w-full">27.6 inches</div>
    </div>
    <div class="zebra-row flex p-200 justify-content-between body-copy-lg">
        <div class="property w-full mr-700">Height To Top Of Refrigerator (Without Hinges)</div>
        <div class="w-full">60 inches</div>
    </div>
    <div class="zebra-row flex p-200 justify-content-between body-copy-lg">
        <div class="property w-full mr-700">Height To Top Of Door Hinge</div>
        <div class="w-full">60.6 inches</div>
    </div>
    <div class="zebra-row flex p-200 justify-content-between body-copy-lg">
        <div class="property w-full mr-700">Depth Without Handle</div>
        <div class="w-full">28.8 inches</div>
    </div>
    <div class="zebra-row flex p-200 justify-content-between body-copy-lg">
        <div class="property w-full mr-700">Depth With Handle</div>
        <div class="w-full">28.8 inches</div>
    </div>
</li>"""


def extract_caracteristiques(html, site_config):
    # Parse the HTML content
    soup = BeautifulSoup(html, 'html.parser')
    
    result = {}

    # Loop through each site in the config
    for site_name, site in site_config['sites'].items():
        for section_name, section_config in site['sections'].items():
            # Select the section based on sectionSelector
            section = soup.select_one(section_config['sectionSelector'])

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
                        result['DIMENSIONS'] = result.get('DIMENSIONS', {})
                        result['DIMENSIONS']['Height'] = height_match.group(1)
                    if width_match:
                        result['DIMENSIONS'] = result.get('DIMENSIONS', {})
                        result['DIMENSIONS']['Width'] = width_match.group(1)

    return result



# Normalization mapping for specification names
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

def normalize_caracteristiques(characteristics):
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



# Extract characteristics for Site 1
caracteristiques_site1 = extract_caracteristiques(bestbuy, config)
print("Site 1 Characteristics:", normalize_caracteristiques(caracteristiques_site1))