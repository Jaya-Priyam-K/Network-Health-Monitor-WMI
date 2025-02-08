import sqlite3
from tabulate import tabulate

# Connect to the SQLite database
conn = sqlite3.connect("monitoring_data.db")
cursor = conn.cursor()

# Ask the user if they want to see the entire data or data for a specific time period
user_choice = input("Do you want to see the entire dataset or data for a specific time period? (Enter 'all' for entire data or 'period' for specific time period): ").strip().lower()

if user_choice == 'all':
    # Query to select the entire dataset
    cursor.execute("SELECT * FROM monitoring_data")
    
elif user_choice == 'period':
    # Ask for start and end timestamps
    start_time = input("Enter the start timestamp (YYYY-MM-DD HH:MM:SS): ")
    end_time = input("Enter the end timestamp (YYYY-MM-DD HH:MM:SS): ")

    # Query to select data within the specified time period
    cursor.execute("SELECT * FROM monitoring_data WHERE timestamp BETWEEN ? AND ?", (start_time, end_time))

else:
    print("Invalid choice. Please enter 'all' or 'period'.")
    conn.close()
    exit()

# Fetch all the rows based on the query
rows = cursor.fetchall()

# Fetch column names
column_names = [description[0] for description in cursor.description]

# Display the results in a table format
if rows:
    print(tabulate(rows, headers=column_names, tablefmt="grid"))
else:
    print("No data found for the selected time period.")

# Close the connection
conn.close()
