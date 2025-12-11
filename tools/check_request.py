import requests
url='https://www.amazon.in/TATA-Product-Essential-Nutrition-Superfood/dp/B01JCFDX4S/'
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
try:
    r = requests.get(url, headers=headers, timeout=15)
    print('status', r.status_code)
    print('len', len(r.text))
    print(r.text[:800])
except Exception as e:
    print('error', e)
