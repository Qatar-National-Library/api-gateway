import pandas as pd
import requests
import json
from typing import Literal

def perform_api_requests_and_update_excel(
    file_path: str = "tests.xlsx",
    sheet_name: str = 0,
    output_file_path: str = "updated_requests.xlsx"
):
    """
    Reads API request details from an Excel file, performs the requests, 
    and updates the file with Status Code, JSON Response, and Raw Content 
    (in case of JSON decoding error).

    Args:
        file_path (str): Path to the input Excel file.
        sheet_name (Union[str, int]): Sheet name or index to read from.
        output_file_path (str): Path to save the updated Excel file.
    """
    try:
        # 1. Read the Excel file into a pandas DataFrame
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except FileNotFoundError:
        print(f"❌ Error: File not found at {file_path}")
        return
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return

    # Initialize new columns
    df['Status_Code'] = None
    df['JSON_Response'] = None
    df['Raw_Content'] = None # <--- New Column for request.content

    print(f"🚀 Starting API requests for {len(df)} rows...")

    # Iterate over each row (request) in the DataFrame
    for index, row in df.iterrows():
        url = row['URL']
        method: Literal['GET', 'POST', 'PUT', 'DELETE'] = str(row['Method']).upper()
        
        # Safely parse Headers and Body
        try:
            headers = json.loads(row['Headers']) if pd.notna(row['Headers']) and str(row['Headers']).strip() else {}
        except json.JSONDecodeError:
            print(f"⚠️ Row {index + 2}: Invalid JSON in Headers column. Skipping request.")
            df.loc[index, 'Status_Code'] = 'Error'
            df.loc[index, 'JSON_Response'] = 'Invalid Headers JSON'
            continue
        
        request_body = None
        if method in ['POST', 'PUT']:
            try:
                request_body = json.loads(row['Body']) if pd.notna(row['Body']) and str(row['Body']).strip() else {}
            except json.JSONDecodeError:
                print(f"⚠️ Row {index + 2}: Invalid JSON in Body column for {method}. Skipping request.")
                df.loc[index, 'Status_Code'] = 'Error'
                df.loc[index, 'JSON_Response'] = f'Invalid Body JSON for {method}'
                continue
        
        # 2. Perform the Web Request
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=request_body if request_body is not None else None,
                timeout=15
            )
            
            # 3. Update the DataFrame with results
            df.loc[index, 'Status_Code'] = response.status_code
            df.loc[index, 'JSON_Response'] = json.dumps(response.json(), indent=2, ensure_ascii=False)
            df.loc[index, 'Raw_Content'] = None # Clear raw content if JSON is successful
            
        except requests.exceptions.JSONDecodeError:
            # If response.json() fails, the response is not valid JSON
            df.loc[index, 'JSON_Response'] = f"Non-JSON Response (Content-Type: {response.headers.get('Content-Type', 'N/A')})"
            
            # Record the raw content (string decoded from bytes)
            raw_content_str = response.content
            
            # Use request.text for string content, truncate if too long
            df.loc[index, 'Raw_Content'] = raw_content_str

        # --- MODIFIED LOGIC END ---

            print(f"✅ Row {index + 2} ({method} {url}): Status {response.status_code}")

        except requests.exceptions.RequestException as req_err:
            # Handle network errors, connection timeouts, etc.
            df.loc[index, 'Status_Code'] = 'Failed'
            df.loc[index, 'JSON_Response'] = f"Request Error: {req_err}"
            df.loc[index, 'Raw_Content'] = None
            print(f"❌ Row {index + 2} ({method} {url}): Request failed: {req_err}")
        except Exception as general_err:
            df.loc[index, 'Status_Code'] = 'Error'
            df.loc[index, 'JSON_Response'] = f"Unexpected Error: {general_err}"
            df.loc[index, 'Raw_Content'] = None
            print(f"❌ Row {index + 2} ({method} {url}): Unexpected error: {general_err}")


    # 4. Save the updated DataFrame to a new Excel file
    try:
        df.to_excel(output_file_path, index=False)
        print(f"\n🎉 Successfully saved updated data to **{output_file_path}**")
    except Exception as e:
        print(f"❌ Error saving Excel file: {e}")
        
perform_api_requests_and_update_excel("tests.xlsx",0)