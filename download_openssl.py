import urllib.request
import os

url = "https://www.openssl.org/source/openssl-1.1.1w.tar.gz"
output_path = r"D:\openharness-enterprise\deploy\openssl-1.1.1w.tar.gz"

# Delete existing file if exists
if os.path.exists(output_path):
    try:
        os.remove(output_path)
        print(f"Deleted existing file")
    except:
        pass

print(f"Downloading OpenSSL 1.1.1w...")
print(f"URL: {url}")
print(f"Output: {output_path}")

# Download with progress
def report_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
    print(f"\rProgress: {percent:.1f}% ({downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB)", end="")

urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
print("\nDownload complete!")

# Verify
size = os.path.getsize(output_path)
print(f"File size: {size/1024/1024:.2f} MB")