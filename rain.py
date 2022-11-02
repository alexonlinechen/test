import requests
import re
url = 'https://www.cwb.gov.tw/Data/js/rainfall/RainfallImg_Day.js'
data = requests.get(url).text
final = re.search(r'20.*J8', data)
print(final.group(0))
