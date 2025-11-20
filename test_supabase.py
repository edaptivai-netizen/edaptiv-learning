from decouple import config
import psycopg2

DATABASE_URL = config('DATABASE_URL')

print('Testing Supabase database connection...')
print(f"Connecting to database at: {DATABASE_URL[:60]}...")

try:
    #Connecting to database
    conn = psycopg2.connect(DATABASE_URL)
    print('Connection successful!')

    #test query
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f"\n PostgreSQL version: ")
    print(version[0][:100])

    #Close connection
    cursor.close()
    conn.close()
    print('\nDatabase connection closed.')

except Exception as e:
    print(f"\n ERROR: {e}")
    print('Failed to connect to the database.')
    print("\nTroubleshooting:")
    print("1. Check DATABASE_URL in .env file.")
    print("2. Verify password is correct")
    print("3.Ensure Supabase project is active")