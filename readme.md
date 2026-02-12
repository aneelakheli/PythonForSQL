"""
Fetch Comments by Post IDs

This script connects to a PostgreSQL database, loads post IDs from a CSV file, retrieves all related records from the `database table` table,
and exports the results to `output.csv`.

Steps:

1. Load database credentials from environment variables (.env).
2. Read unique post IDs from the CSV file.
3. Query the Comment table using those IDs.
4. Save the fetched comments to a new CSV file.

Requirements:

- pandas
- python-dotenv
- sqlalchemy
- psycopg2-binary
  """
