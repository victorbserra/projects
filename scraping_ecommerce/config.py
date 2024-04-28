import random
import os

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:10.0) Gecko/20100101 Firefox/10.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
    "Mozilla/5.0 (Linux x86_64) AppleWebKit/537.45 (KHTML, like Gecko) Chrome/51.0.2561.330 Safari/536",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 9_8_8; en-US) AppleWebKit/536.15 (KHTML, like Gecko) Chrome/52.0.1881.379 Safari/601",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 7_2_1; like Mac OS X) AppleWebKit/600.35 (KHTML, like Gecko)  Chrome/54.0.1981.285 Mobile Safari/534.8"
]

new_chromedriver_path = 'C:/Users/victo/AI/Cognificadora/cognificar_leiloes/chromedriver.exe'
path = 'C:/Users/victo/AI/Cognificadora/cognificar_leiloes/scraping_ecommerce/info_cache'

session_id = random.randint(2000, 8000)

# Usar residential
proxy_ip_port = 'a'
proxy_user_pass = f'a'



connection_string = "a"