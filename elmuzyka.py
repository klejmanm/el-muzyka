from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
#import webbrowser
import requests
import json
import pickle
import os.path
import os
import wget
import sys
import getopt
from bs4 import BeautifulSoup

PROGRAM_ID=5403
SAVE_PATH='/temp/'

# procesowanie parametrów z linii komend
clstartPage=None
clendPage=None
clId=None
clPath=None
argumentList = sys.argv[1:]
options = "hseip:"
long_options=['help','start=','end=','id=','path=']
try:
    arguments, values = getopt.getopt(argumentList, options, long_options)
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-h", "--help"):
            print('usage: --help --start [start page] --end [end page] --id [program id] --path [save path]')
            sys.exit()
        elif currentArgument in ("-s", "--start"):
            clstartPage=int(currentValue)
        elif currentArgument in ("-e", "--end"):
            clendPage=int(currentValue)
        elif currentArgument in ("-i", "--id"):
            clId=currentValue
        elif currentArgument in ("-p", "--path"):
            clPath=currentValue
except getopt.error as err:
    print (str(err))
class Audycja:
    tytul=''
    adres=''
    mp3adres=''
    data=''
    godzina=''
    id=None
    categoryId=''
    categoryName=''

def znajdzMP3(audycja: Audycja):
    page = requests.get(audycja.adres)
    mp3soup = BeautifulSoup(page.content, 'html.parser')
    res=mp3soup.find('script',id="__NEXT_DATA__",type="application/json")
    js=json.loads(res.contents[0])
    try:
        audycja.tytul=js['props']['pageProps']['post']['title']
    except Exception as e:
        audycja.tytul=''
    try:
        audycja.categoryId=js['props']['pageProps']['post']['categoryId']
    except Exception as e:
        audycja.categoryId=''
    try:
        audycja.categoryName=js['props']['pageProps']['post']['categoryName']
    except Exception as e:
        audycja.categoryName=''
    try:
        audycja.data=js['props']['pageProps']['post']['datePublic'][:10]
    except Exception as e:
        audycja.data=''
    try:
        audycja.godzina=js['props']['pageProps']['post']['datePublic'][11:]
    except Exception as e:
        audycja.godzina=''
    try:
        audycja.id=js['props']['pageProps']['post']['id']
    except Exception as e:
        audycja.id=''
    try:
        filetype=js['props']['pageProps']['post']['attachments'][1]['fileType']
    except Exception as e:
        filetype=''
    if filetype=='Audio':
        try:
            audycja.mp3adres=js['props']['pageProps']['post']['attachments'][1]['file'].replace('.file','.mp3')
        except Exception as e:
            audycja.mp3adres=''
    try:
        filetype=js['props']['pageProps']['post']['attachments'][0]['fileType']
    except Exception as e:
        filetype=''
    if filetype=='Audio':
        try:
            audycja.mp3adres=js['props']['pageProps']['post']['attachments'][0]['file'].replace('.file','.mp3')
        except Exception as e:
            audycja.mp3adres=''

audycje=[]
licznikAudycji=0

#if os.path.exists('audycje.list'):
#    file=open('audycje.list','rb')
#    if os.path.getsize(file.name) > 0:   
#        audycje = pickle.load(file)
#    file.close()

# załadowanie strony audycji w przeglądarce chrome
driver = webdriver.Chrome()
if clId==None:
    clId=PROGRAM_ID
audycjaURL='https://trojka.polskieradio.pl/audycja/'+str(clId).strip()
driver.get(audycjaURL)

# kliknięcie 'accept' na wyskakującym okienku 'privacy'
try:
    button=driver.find_element(By.ID,'onetrust-accept-btn-handler')
    button.click()
except NoSuchElementException:
    pass

# sprawdzenie łącznej liczby stron zawierających wszystkie audycje
page=driver.page_source
soup=BeautifulSoup(page,'lxml')
pagination = soup.find('div', class_='pagination')
paginationNext=pagination.next_element
strontxt=paginationNext.next_sibling.text
liczbaStron=int(strontxt[2:])

# iteracja po kolejnych stronach zawierających audycje
if clstartPage==None:
    clstartPage=1
if clendPage==None:
    clendPage=liczbaStron
print('strona startowa:[{}], strona końcowa:[{}]'.format(clstartPage,clendPage))
for licznikStron in range(clstartPage,clendPage+1):
    page=driver.page_source
    soup=BeautifulSoup(page,'lxml')
    page_auditions = soup.find_all('div', class_='span-4 span-md-6 span-sm-12')
    for page_audition in page_auditions:
        audycja=Audycja()
        page_audition_link=page_audition.next
        audycja.tytul=page_audition_link.text
        audycja.adres='https://trojka.polskieradio.pl{}'.format(page_audition_link.attrs['href'])
        audycja.plikadres=znajdzMP3(audycja)
        licznikAudycji=licznikAudycji+1
        # zrzut listy audycji do pliku
        result = next((obj for obj in audycje if obj.id == audycja.id),None)
        if result is None:
            audycje.append(audycja)
            file=open('audycje.list','wb')
            pickle.dump(audycje,file)
            file.close()
        print('[{}]:[{}]:[{}]:[{}]:[{}]'.format(licznikStron,audycja.id,audycja.data,audycja.tytul,audycja.mp3adres))
        if not(audycja.mp3adres==''):
            if clPath==None:
                clPath=SAVE_PATH
            savedir=os.path.join(clPath,'')
            if not(os.path.exists(savedir)):
                os.mkdir(savedir)           
            savedir=os.path.join(clPath,audycja.categoryName,'')
            if not(os.path.exists(savedir)):
                os.mkdir(savedir)
            targetfilename='{}{}.{} [{}].mp3'.format(savedir,audycja.data,audycja.categoryName,audycja.id)
            if not(os.path.exists(targetfilename)):
                response=wget.download(audycja.mp3adres,targetfilename)
                print('\n')
    try:
        button=driver.find_element(By.CSS_SELECTOR,'[aria-label="{}"]'.format("Page "+str(licznikStron+1).strip()))
        button.click()
        time.sleep(3)
    except NoSuchElementException:
        sys.exit()
