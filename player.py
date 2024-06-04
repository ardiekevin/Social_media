import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define scope and credentials path
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = r'C:\Users\ardie.asilo\Desktop\Social Media\social-media-424000-9f4ccd37260a.json'

# Authorize Google Sheets API
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
except Exception as e:
    print(f"Error with credentials: {e}")
    exit()

# Open the Google Sheet and select the worksheet
try:
    sheet = client.open_by_key('19U0iLgpy3TZHpVyk9gq9UndIGyPOvMoPQixYSDX96kc')  ###################################  replace sheet ID ################################### 
    worksheet = sheet.worksheet('*Daily_Data (Player)')
except gspread.exceptions.APIError as e:
    print(f"API Error: {e}")
    exit()
except PermissionError:
    print("Permission Error: Make sure the service account has access to the Google Sheet.")
    exit()

# Define folder path and get CSV files
folder_path = r"C:\Users\ardie.asilo\Desktop\Social Media\file"
csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]

all_data = []

# Process each CSV file
for file_name in csv_files:
    try:
        df = pd.read_csv(os.path.join(folder_path, file_name))

        # Filter out rows containing 'Grand Total'
        df = df[~df.apply(lambda row: row.astype(str).str.contains('Grand Total').any(), axis=1)]
        
        columns_to_keep = ['Affiliate Username', 'Currency', 'Username', 'Total Deposit', 
                           'Total Withdrawal', 'Total Number of Bets', 'Total Turnover', 
                           'Total Profit&Loss', 'Total Bonus']
        
        # Check if required columns exist
        if all(column in df.columns for column in columns_to_keep):
            df_selected = df[columns_to_keep]
            
            # Extract date from file name and format it to dd/mm/yyyy
            date_str = os.path.splitext(file_name)[0]
            date_formatted = pd.to_datetime(date_str, format='%d-%m-%Y').strftime('%d/%m/%Y')
            
            # Insert formatted date and empty column
            df_selected.insert(0, 'File Name', date_formatted)
            df_selected.insert(1, 'Empty Column', '')
            
            all_data.append(df_selected)
        else:
            print(f"File {file_name} does not contain the required columns.")
    except Exception as e:
        print(f"Error processing file {file_name}: {e}")

# Combine all data into a single DataFrame
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Sort data by date (File Name column)
    final_df['File Name'] = pd.to_datetime(final_df['File Name'], format='%d/%m/%Y')
    final_df = final_df.sort_values(by='File Name')
    final_df['File Name'] = final_df['File Name'].dt.strftime('%d/%m/%Y')
    
    final_df = final_df.fillna('')
    
    existing_data = worksheet.get_all_values()
    last_row = len(existing_data)

    new_row_count = last_row + len(final_df)
    current_row_count = worksheet.row_count
    
    # Add rows if needed
    if new_row_count > current_row_count:
        worksheet.add_rows(new_row_count - current_row_count)
    
    # Update Google Sheet
    try:
        worksheet.update(f'A{last_row + 1}', final_df.values.tolist())
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")
else:
    print("No valid data to upload.")
