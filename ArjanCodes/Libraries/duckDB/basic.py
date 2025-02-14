# DuckDB Basic Examples
# This guide will help you get started with DuckDB using simple examples.

import duckdb  # Make sure you have DuckDB installed (`pip install duckdb`)
import pandas as pd

def main():
    # Create an in-memory DuckDB connection
    db = duckdb.connect(':memory:')

    # Example 1: Creating a Table and Inserting Data
    print("\n--- Example 1: Creating and Inserting Data ---")
    db.execute('''
        CREATE TABLE users (
            id INTEGER,
            name VARCHAR,
            age INTEGER
        );
    ''')
    db.execute("INSERT INTO users VALUES (1, 'Alice', 30), (2, 'Bob', 25), (3, 'Charlie', 35);")

    # Example 2: Querying the Table
    print("\n--- Example 2: Querying Data ---")
    result = db.execute("SELECT * FROM users;").fetchall()
    for row in result:
        print(row)

    # Example 3: Filtering Data
    print("\n--- Example 3: Filtering Data ---")
    result = db.execute("SELECT * FROM users WHERE age > 30;").fetchall()
    for row in result:
        print(row)

    # Example 4: Aggregation
    print("\n--- Example 4: Aggregating Data ---")
    result = db.execute("SELECT AVG(age) AS average_age FROM users;").fetchall()
    print(f"Average age: {result[0][0]}")

    # Example 5: Using DataFrames (DuckDB can query Pandas DataFrames)
    print("\n--- Example 5: Querying a Pandas DataFrame ---")
    data = {
        'id': [4, 5, 6],
        'name': ['Dave', 'Eve', 'Frank'],
        'age': [40, 22, 28]
    }
    df = pd.DataFrame(data)

    # Query the DataFrame directly using DuckDB
    df_result = db.execute("SELECT * FROM df WHERE age < 30;").df()
    print(df_result)

    # Example 6: Persistent Storage and CSV Integration
    print("\n--- Example 6: Persistent Storage and CSV Integration ---")
    # Connect to a persistent DuckDB database file
    db = duckdb.connect('example_db.duckdb')

    # Create a new table and insert data
    csv_file = 'example_data.csv'

    # Writing sample data to a CSV file for demonstration
    sample_data = """id,name,age
    7,Grace,31
    8,Hank,45
    9,Ivy,29
    """
    with open(csv_file, 'w') as f:
        f.write(sample_data)

    # Load the CSV file into DuckDB
    db.execute(f"CREATE TABLE IF NOT EXISTS users_from_csv AS SELECT * FROM read_csv_auto('{csv_file}');")

    # Query the new table
    csv_result = db.execute("SELECT * FROM users_from_csv;").fetchall()
    print("Data from CSV:")
    for row in csv_result:
        print(row)

    # Closing the connection
    db.close()

if __name__ == "__main__":
    main()
