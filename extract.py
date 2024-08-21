import os
import PyPDF2
import logging
import csv
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_first_page(pdf_path):
    logging.debug(f"Opening PDF file: {pdf_path}")
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            first_page = reader.pages[0]
            text = first_page.extract_text()
            logging.debug(f"Successfully extracted text from the first page of {pdf_path}")
            return text
    except Exception as e:
        logging.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""

def format_date(date_str):
    try:
        # Convert date string to datetime object
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        # Convert datetime object to desired format
        return date_obj.strftime("%m/%d/%Y")
    except ValueError:
        logging.error(f"Date conversion failed for '{date_str}'")
        return ""

def parse_text_for_csv(text, filename):
    # Extract dollar value, date, and account number
    dollar_value = ""
    date = ""
    account_number = ""

    # Find and extract dollar value
    total_value_lines = [line for line in text.splitlines() if "TOTAL VALUE" in line]
    if total_value_lines:
        match = re.search(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', total_value_lines[0])
        if match:
            dollar_value = match.group(0).strip().replace('$', '')
            logging.info(f"Found balance: {dollar_value}")  # Info log for found dollar value
    
    # Find and extract date
    period_lines = [line for line in text.splitlines() if "PERIOD" in line]
    if period_lines:
        match = re.search(r'TO\s+([\w\s,]+)', period_lines[0])
        if match:
            date_str = match.group(1).strip()
            # Convert date string to desired format
            date = format_date(date_str)
            logging.info(f"Found date: {date}")  # Info log for found date
    
    # Find and extract account number from the line starting with "Account Number:"
    account_lines = [line for line in text.splitlines() if line.startswith("Account Number:")]
    if account_lines:
        account_line = account_lines[0]
        logging.debug(f"Account line found: {account_line}")  # Debugging output
        # Extract account number assuming it follows "Account Number:"
        match = re.search(r'Account Number:?[\s:]*([\S]+)', account_line)
        if match:
            account_number = match.group(1).strip()
            logging.info(f"Found account number: {account_number}")  # Info log for found account number
        else:
            logging.info("Account number not found in the line starting with 'Account Number:'")
    else:
        logging.info("No line starting with 'Account Number:' found")

    # Log warnings if any field is missing
    if not dollar_value:
        logging.warning(f"Missing dollar value in file: {filename}")
    if not date:
        logging.warning(f"Missing date in file: {filename}")
    if not account_number:
        logging.warning(f"Missing account number in file: {filename}")

    return date, dollar_value, account_number

def write_csv(csv_path, rows):
    # Filter out rows with missing or invalid dates
    valid_rows = []
    for row in rows:
        try:
            # Attempt to parse the date to ensure it's valid
            datetime.strptime(row['date'], "%m/%d/%Y")
            valid_rows.append(row)
        except ValueError:
            logging.warning(f"Invalid or missing date in row: {row}")

    # Sort the valid rows based on the 'date' field, and then by 'account_number'
    valid_rows.sort(key=lambda row: (datetime.strptime(row['date'], "%m/%d/%Y"), row['account_number']))

    # Write the sorted rows back to the CSV file
    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Filename', 'date', 'value', 'account_number'])
        writer.writeheader()
        writer.writerows(valid_rows)

def scan_pdfs_in_directory(directory, csv_path):
    logging.info(f"Scanning directory: {directory} for PDF files")
    pdf_count = 0
    rows = []
    
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            pdf_count += 1
            pdf_path = os.path.join(directory, filename)
            logging.debug(f"Processing file: {filename}")
            text = extract_text_from_first_page(pdf_path)
            if text:
                date, value, account_number = parse_text_for_csv(text, filename)
                logging.debug(f"Adding to rows: {filename}, {date}, {value}, {account_number}")  # Debugging output
                rows.append({'Filename': filename, 'date': date, 'value': value, 'account_number': account_number})
            logging.debug("-" * 80)
                
    if pdf_count == 0:
        logging.warning(f"No PDF files found in the directory: {directory}")

    write_csv(csv_path, rows)

def main():
    directory = '.'  # Current directory
    csv_path = 'output.csv'  # Path to the output CSV file
    logging.info("Starting PDF text extraction and search")
    scan_pdfs_in_directory(directory, csv_path)
    logging.info("Completed PDF text extraction and search")

if __name__ == "__main__":
    main()