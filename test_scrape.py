import pandas as pd
import requests

url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
headers = {
  "User-Agent": "Mozilla/5.0"
}
response = requests.get(url, headers=headers)
dfs = pd.read_html(response.text)
print(dfs[0].columns)
