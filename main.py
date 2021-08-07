from requests_html import HTMLSession
import sqlite3
from datetime import datetime
import telebot
from time import sleep
import json
import re
import requests
from requests.structures import CaseInsensitiveDict


bot = telebot.TeleBot("1921336823:AAFuNJvCdCbdKvf4hpz_e9eD7LYAbWKHP5g", parse_mode='HTML')
grupo_id = '@amazonchollitos'

token_bitly = '0c8fee80ac9992a329cf79318389750afc05ef15'
con = sqlite3.connect('data.db')
cur = con.cursor()

fecha = datetime.now()
hoy = fecha.strftime('%Y-%m-%d')
fecha_msg = fecha.strftime('%Y-%m-%d %H:%M')
afiliado = '&_encoding=UTF8&tag=yjafiliados-21&linkCode=ur2'
tiempo = 300 #En segundos

emojis = {
	'rayo': "\U000026A1",
	'check': "\U00002705",
    'shop': "\U0001F6CD",
    'eur': "\U0001F4B6",
    'stars': "\U00002B50",
    'fire': "\U0001F525",
    'sparkles': "\U00002728",
    'prohibited': "\U0001F6AB",
    'chart': "\U0001F4C9",
    'link': "\U0001F517",
    'recycling': "\U0000267B"
}

def leerJson():
    urls = None
    with open('urls.json') as file:
        urls = json.load(file)
    return urls

def __existInDB(busq):
    query = "SELECT * FROM articles WHERE title = '{}' AND created_at ='{}'".format(busq, hoy)
    consul = cur.execute(query)
    res = consul.fetchall()
    return {'exists': False, 'data': res} if res == [] else {'exists': True, 'data': res}

def registrarHistorial(products):
    try:
        cur.execute("""INSERT INTO articles  (title, price, pvp, image, discount, stars, url, created_at) 
        VALUES (?,?,?,?,?,?,?,?)""", (products['title'], products['price'], products['pvp'],
        products['image'], products['discount'], products['stars'], products['link'], hoy))
        con.commit()
        return True
    except:
        print('Error al registrar producto.')
        return False
    pass

def acortarURL(link):
    try:
        url = "https://api-ssl.bitly.com/v4/shorten"
        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Bearer {token_bitly}"
        headers["Content-Type"] = "application/json"
        data = {"long_url": f"{link}","domain": "bit.ly"}
        #data = '{"long_url": "{}","domain": "bit.ly"}'.format(url)

        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resJson = resp.json()
        #print(resp.json())
        return resJson['link']
    except:
        return link


def send_message(url_img, text):
    bot.send_photo(grupo_id,url_img, text)

def formatStringFloat(cadena):
    return float(str(cadena).replace(',','.').replace('€',''))

def scrapingOfertasDiarias(content, header, categoria):
    for item in content:
        try:
            precios = item.xpath('//span[@class="a-size-medium"]')
            discount = re.findall(r'\d+\.?\d',
                                  item.xpath('//span[1]/div[1]/a[2]/span[1]/div[1]', first=True).text) if item.xpath(
                '//span[1]/div[1]/a[2]/span[1]/div[1]', first=True) != None else '0'
            stars = item.xpath('//a[@data-testid="link-review-component"]', first=True)
            pvp = item.xpath('//span[1]/div[1]/a[2]/span[1]/div[1]/div[1]/span[1]/span[1]', first=True)
            price = item.xpath('//span[@class="a-price"]/span[2]', first=True).text if item.xpath(
                '//span[@class="a-price"]/span[2]', first=True) != None else 0
            price_discount = 0
            try:
                if len(discount) == 3:
                    discount = discount[2]
                    price_discount = rount(formatStringFloat(price) * (int(str(discount)) / 100), 2)
                else:
                    discount = discount[:1]
                    price_discount = rount(formatStringFloat(price) * (int(str(discount)) / 100), 2)

            except:
                price_discount = '0'

            products = {
                'title': item.xpath('//div[contains(@class, "a-image-container")]', first=True).find('img')[0].attrs[
                    'alt'],
                'price': price,
                'pvp': pvp.text if pvp != None else 0,
                'image': item.xpath('//div[contains(@class, "a-image-container")]', first=True).find('img')[0].attrs[
                    'src'],
                'discount': discount if type(discount) != type(list()) else discount[:1],
                'stars': stars.attrs['aria-label'][13:] if stars != None else 'Ninguna',
                'link': acortarURL(
                    item.xpath('//span[1]/div[1]/a[3]', first=True).attrs['href'] + afiliado) if item.xpath(
                    '//span[1]/div[1]/a[3]', first=True) != None else None
            }

            # SI EL DESCUENTO ES MAYOR O IGUAL AL 30% ENTONCES NOTIFICO POR TELEGRAM Y REGISTRO EN LA BD
            if int(products['discount']) >= 30 and products['link'] != None:
                res = __existInDB(products['title'])
                if res['exists'] == False:
                    msg = f"{emojis['sparkles']} <b>{header}</b> {emojis['sparkles']}\n\n{emojis['rayo']} <b>{products['title']}</b> {emojis['rayo']}\n\n{emojis['check']} <b>Precio Oferta: {products['price']}  {emojis['check']}</b>\n{emojis['fire']} <b>Descuento: {price_discount} € ({products['discount']}%)</b> {emojis['fire']}\n\n{emojis['prohibited']} PVP ≈ {products['pvp']} {emojis['prohibited']}\n\n{emojis['stars']} <b>Estrellas:</b> {products['stars']}\n\n{emojis['link']} Link: {products['link']}"
                    send_message(products['image'], msg)
                    registrarHistorial(products)
                    sleep(tiempo)
        except:
            print('Error al realizar scraping ofertas ' + fecha_msg)

def scrapingReacondicionados(content, header, categoria):
    for item in content:
        elem_pvp = item.xpath('.//span[contains(@class, "a-text-price")]/span[1]', first=True)
        elem_price = item.xpath('.//span[@class="a-price"]/span[1]', first=True)
        elem_stars = item.xpath('.//div[1]/span[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/div[2]/div[1]/span[1]', first=True)
        elem_link = item.xpath('.//div[1]/span[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]', first=True)

        if elem_pvp != None and elem_price != None and elem_stars != None and elem_link != None:
            try:
                pvp = elem_pvp.text
                price = formatStringFloat(elem_price.text[:5])
                price_discount = 0
                discount = 0
                stars = elem_stars.attrs['aria-label']
                if pvp != None and price != None:
                    discount = round(price / formatStringFloat(pvp[:5]),2) * 100
                    price_discount = price * (discount/100)

                products = {
                        'title': item.xpath('//img[@data-image-latency="s-product-image"]', first=True).find('img')[0].attrs['alt'],
                        'price': elem_price.text,
                        'pvp': pvp,
                        'image': item.xpath('//img[@data-image-latency="s-product-image"]', first=True).find('img')[0].attrs['src'],
                        'discount': discount,
                        'stars': stars,
                        'link': acortarURL('https://www.amazon.es/' + elem_link.find('a')[0].attrs['href'] + afiliado)
                    }

                if discount > 30:
                    res = __existInDB(products['title'])
                    if res['exists'] == False:
                        msg = f"{emojis['recycling']} <b>{header}</b> {emojis['recycling']}\n\n{emojis['rayo']} <b>{products['title']}</b> {emojis['rayo']}\n\n <b>{emojis['check']} Precio Oferta: {products['price']}  {emojis['check']}</b>\n{emojis['fire']} <b>Descuento: {price_discount} € ({products['discount']}%)</b> {emojis['fire']}\n\n{emojis['prohibited']} PVP ≈ {products['pvp']} {emojis['prohibited']}\n\n{emojis['stars']} <b>Estrellas:</b> {products['stars']}\n\n{emojis['link']} Link: {products['link']}"
                        send_message(products['image'], msg)
                        registrarHistorial(products)
                        sleep(tiempo)
            except:
                print('Error al realizar scraping para productos reacondicionados ' + fecha_msg)
                pass


def getProducts(data):
    div_content = ''

    if data['categoria'] == 'ofertas':
        div_content = '//div[@role="main"]/div/div'
    elif data['categoria'] == 'reacondicionado':
        div_content = '//div[contains(@class, "s-result-item")]'

    s = HTMLSession()
    r = s.get(data['url'])
    r.html.render(sleep=2)
    content = r.html.xpath(div_content)
    print(len(content))
    if data['categoria'] == 'ofertas':
        print(f"Inicio el analisis (ofertas) para: {data['url']}")
        scrapingOfertasDiarias(content, data['titulo'], data['categoria'])
    elif data['categoria'] == 'reacondicionado':
        print(f"Inicio el analisis (reacondicionado) para: {data['url']}")
        scrapingReacondicionados(content, data['titulo'], data['categoria'])



    #print(products)

print('Esto en ejecución...')

urls = leerJson()
for url in urls:
    try:
        print('Analizando la url para ' + url['categoria'])
        getProducts(url)
    except:
        print('Error al analizar el sitio web')
