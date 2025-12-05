from dotenv import load_dotenv
import os



print("Loading .env from: ", os.path.abspath('.env'))

load_dotenv()  # Auto-load from current script directory

print("Access Key:", os.getenv("AWS_ACCESS_KEY"))
print("Secret Key:", os.getenv("AWS_SECRET_ACCESS_KEY"))
print("Bucket:", os.getenv("AWS_STORAGE_BUCKET_NAME"))
print("Region:", os.getenv("AWS_DEFAULT_REGION"))