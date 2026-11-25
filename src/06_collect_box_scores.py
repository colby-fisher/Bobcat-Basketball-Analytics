
import pandas as pd
import requests

from bs4 import BeautifulSoup
from io import StringIO
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re

# Official Montana State schedule
schedule_url = (
    "https://msubobcats.com/sports/"
    "mens-basketball/schedule/2025-26"
)

# Download schedule
response = requests.get(schedule_url, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Find individual box score links
box_score_links = []

for link in soup.find_all("a", href=True):

    full_url = urljoin(schedule_url, link["href"])
    path = urlparse(full_url).path

    if re.search(
        r"/boxscore/\d+/?$", path, re.IGNORECASE
    ):
        if full_url not in box_score_links:
            box_score_links.append(full_url)

print("BOX SCORE DATA COLLECTION")
print("=" * 45)

print("\nBox scores found:", len(box_score_links))

print("\nFirst five box score links:")

for link in box_score_links[:5]:
    print(link)

# Save discovered links
output = Path("data/raw")
output.mkdir(parents=True, exist_ok=True)

pd.DataFrame({
    "Box_Score_URL": box_score_links
}).to_csv(
    output / "box_score_links_2025_26.csv",
    index=False
)

# Test extraction using Colorado game
test_url = (
    "https://msubobcats.com/sports/"
    "mens-basketball/stats/2025-26/"
    "colorado/boxscore/7453"
)

response = requests.get(test_url, timeout=30)
response.raise_for_status()

tables = pd.read_html(StringIO(response.text))

print("\nTesting Colorado box score:")
print("Tables found:", len(tables))

# Inspect available tables
for i, table in enumerate(tables):

    print("\nTable:", i)
    print("Shape:", table.shape)
    print("Columns:", table.columns.tolist())

    # Preview smaller tables
    if len(table) <= 30:
        print(table.tail(3).to_string(index=False))

print("\nBox score inspection complete!")
