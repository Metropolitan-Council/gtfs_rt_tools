from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
from gtfs_rt_tools.download import download_file, get_timestamped_filename
from gtfs_rt_tools.parse import parse_trip_updates, parse_vehicle_positions, parse_alerts
import re

app = Flask(__name__)

# Global variables to store DataFrames
df1 = None
df2 = None
ROWS_PER_PAGE = 50

def get_parser_from_url(url):
    if "tripupdates" in url.lower():
        return parse_trip_updates
    elif "vehiclepositions" in url.lower():
        return parse_vehicle_positions
    elif "alerts" in url.lower():
        return parse_alerts
    else:
        raise ValueError("Unknown feed type in URL. Must contain 'tripupdates', 'vehiclepositions', or 'alerts'.")

def parse_filter_expression(expr, df):
    """Parse and apply a complex filter expression to a DataFrame."""
    if not expr.strip():
        return pd.Series([True] * len(df))
    
    # Convert column values to strings for comparison
    df = df.astype(str)
    
    def evaluate_simple_condition(condition):
        # Match pattern: column_name operator value
        # e.g., "route_id = 10" or "trip_id != 123"
        pattern = r'(\w+)\s*(=|!=|>|<|>=|<=)\s*(\S+)'
        match = re.match(pattern, condition.strip())
        if not match:
            raise ValueError(f"Invalid condition format: {condition}")
        
        column, operator, value = match.groups()
        if column not in df.columns:
            raise ValueError(f"Column not found: {column}")
        
        if operator == '=':
            return df[column].str.contains(value, case=False, na=False)
        elif operator == '!=':
            return ~df[column].str.contains(value, case=False, na=False)
        else:
            # Convert to float for numeric comparisons
            try:
                return eval(f"df[column].astype(float) {operator} float(value)")
            except (ValueError, TypeError):
                raise ValueError(f"Invalid numeric comparison for {column}")

    def evaluate_group(group):
        # Remove outer parentheses
        group = group.strip('()')
        
        # Split by OR, keeping AND groups together
        or_parts = re.split(r'\s+OR\s+', group)
        
        results = []
        for or_part in or_parts:
            # Split by AND
            and_parts = re.split(r'\s+AND\s+', or_part)
            and_result = pd.Series([True] * len(df))
            
            for condition in and_parts:
                and_result &= evaluate_simple_condition(condition.strip())
            
            results.append(and_result)
        
        # Combine OR conditions
        return pd.concat(results, axis=1).any(axis=1)

    # Handle nested parentheses
    def parse_nested_expr(expr):
        stack = []
        current = ''
        level = 0
        
        for char in expr:
            if char == '(':
                if level == 0:
                    if current.strip():
                        stack.append(current.strip())
                        stack.append('AND')
                    current = ''
                else:
                    current += char
                level += 1
            elif char == ')':
                level -= 1
                if level == 0:
                    if current.strip():
                        result = evaluate_group(current)
                        stack.append(result)
                    current = ''
                else:
                    current += char
            else:
                current += char
        
        if current.strip():
            stack.append(current.strip())
        
        # Evaluate remaining stack
        result = pd.Series([True] * len(df))
        for i in range(0, len(stack), 2):
            if isinstance(stack[i], pd.Series):
                curr_result = stack[i]
            else:
                curr_result = evaluate_group(stack[i])
            
            result &= curr_result
        
        return result

    return parse_nested_expr(expr)

def apply_filters(df, filter_expr):
    if not filter_expr:
        return df
    
    try:
        mask = parse_filter_expression(filter_expr, df)
        return df[mask]
    except Exception as e:
        raise ValueError(f"Filter error: {str(e)}")

def get_paginated_data(df, page, rows_per_page=ROWS_PER_PAGE):
    start_idx = (page - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    return df.iloc[start_idx:end_idx]

@app.route('/')
def index():
    return render_template('feed_comparison_index.html', csv1='', csv2='', total_rows1=0, total_rows2=0)

def download_and_parse(url):
    # Create downloads directory if it doesn't exist
    downloads_dir = './downloads'
    os.makedirs(downloads_dir, exist_ok=True)
    
    # Generate a timestamped filename for the .pb file
    pb_filename = get_timestamped_filename(url)
    pb_filepath = os.path.join(downloads_dir, pb_filename)
    
    # Download the .pb file
    download_file(url, pb_filepath)
    
    # Automatically determine the parser based on the URL
    parser = get_parser_from_url(url)
    
    # Parse the .pb file to a Pandas DataFrame using the correct parser
    df = parser(pb_filepath, use_pandas=True, filename_meets_schema=True)
    
    # Only reset and rename index if 'url' isn't already a column
    if 'url' not in df.columns:
        df = df.reset_index()
        df = df.rename(columns={'index': 'url'})
    
    # Convert object columns to strings
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str)
            
    return df

@app.route('/download', methods=['POST'])
def download():
    global df1, df2
    
    url1 = request.form.get('url1')
    url2 = request.form.get('url2')
    
    try:
        # Download and parse both feeds using appropriate parsers
        df1 = download_and_parse(url1)
        df2 = download_and_parse(url2)
        
        # Get first page of data
        page_df1 = get_paginated_data(df1, 1)
        page_df2 = get_paginated_data(df2, 1)
        
        # Convert to HTML with nowrap
        html1 = page_df1.to_html(classes='table table-striped table-bordered', escape=True, index=False)
        html2 = page_df2.to_html(classes='table table-striped table-bordered', escape=True, index=False)
        
        return render_template('feed_comparison_index.html', 
                             csv1=html1, 
                             csv2=html2,
                             total_rows1=len(df1),
                             total_rows2=len(df2),
                             total_pages1=(len(df1) // ROWS_PER_PAGE) + 1,
                             total_pages2=(len(df2) // ROWS_PER_PAGE) + 1,
                             current_page=1)
        
    except Exception as e:
        return render_template('feed_comparison_index.html', 
                             error=str(e),
                             csv1='', 
                             csv2='',
                             total_rows1=0,
                             total_rows2=0)

@app.route('/filter', methods=['POST'])
def filter_data():
    if df1 is None or df2 is None:
        return jsonify({'error': 'No data loaded'})
    
    data = request.json
    page = int(data.get('page', 1))
    filter_expr = data.get('filter_expr', '')
    
    try:
        # Apply filters to both dataframes
        filtered_df1 = apply_filters(df1, filter_expr)
        filtered_df2 = apply_filters(df2, filter_expr)
        
        # Get paginated data
        page_df1 = get_paginated_data(filtered_df1, page)
        page_df2 = get_paginated_data(filtered_df2, page)
        
        # Convert to HTML with nowrap
        html1 = page_df1.to_html(classes='table table-striped table-bordered', escape=True, index=False)
        html2 = page_df2.to_html(classes='table table-striped table-bordered', escape=True, index=False)
        
        return jsonify({
            'csv1': html1,
            'csv2': html2,
            'total_rows1': len(filtered_df1),
            'total_rows2': len(filtered_df2),
            'total_pages1': (len(filtered_df1) // ROWS_PER_PAGE) + 1,
            'total_pages2': (len(filtered_df2) // ROWS_PER_PAGE) + 1,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)