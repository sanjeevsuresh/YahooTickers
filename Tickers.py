import urllib2
import re
import os
import sys
import datetime as DateTime
from datetime import timedelta
from bs4 import BeautifulSoup
input = raw_input

class TickerError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def createFolder(folderName):
    try:
        os.makedirs(folderName)
    except FileExistsError:
        print("Folder already exists")

def handler(signalNum,  frame):
    raise KeyboardInterrupt


def raw_input_with_timeout(prompt, timeout=5):
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    astring = None
    try:
        # timer.start()
        astring = input(prompt)
    except KeyboardInterrupt:
        print("\nTimedOut!")
    # timer.cancel()
    signal.alarm(0)
    return astring


def ask(prompt,  timeout):
    answer = raw_input_with_timeout(prompt, timeout)
    return answer

def askForTickers():
    inputExtensions = input("Enter any Tickers I should look for: ")
    inputExtensions = re.split('\W+', inputExtensions)
    otherExtensions = "checkIfUserIsDone"
    while(otherExtensions not in ["n", "no", ""]):
        otherExtensions = input("Any others? [Enter them or Respond (n/no)]: ")
        if(otherExtensions not in ["n", "no", ""]):
            extras = re.split('\W+', otherExtensions)
            inputExtensions.extend(extras)
    return correctIssues(inputExtensions)


def correctIssues(userDefinedExtensions):
    requestedExtensions = "These are the extensions I'm looking for:\n{0}"
    requestedExtensions = requestedExtensions.format(userDefinedExtensions)
    print(requestedExtensions)
    issues = input("Any issues? (y/n): ")
    if issues in ['y', 'yes']:
        print("Restarting...")
        return askForExtensions()
    return userDefinedExtensions

def parodyBrowser(url):
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML,  like Gecko) Chrome/23.0.1271.64 Safari/537.11', 'Accept': 'text/html, application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Charset': 'ISO-8859-1, utf-8;q=0.7,*;q=0.3', 'Accept-Encoding': 'none', 'Accept-Language': 'en-US, en;q=0.8', 'Connection': 'keep-alive'}
    req = urllib2.Request(url, headers=hdr)
    return req

def findCurrentDate():
    x = DateTime.date.today()
    month = str(x.month - 1)
    if(int(month) < 10):
        month = "0{0}".format(str(x.month - 1))
    return month, str(x.day), str(x.year)

def DateBefore(deltaDays=10):
    x = DateTime.date.today()
    delta = timedelta(days=deltaDays)
    x = x - delta
    month = str(x.month - 1)
    if(int(month) < 10):
        month = "0{0}".format(str(x.month - 1))
    return month, str(x.day), str(x.year)

def HistoricalPricesPage(ticker):
    """
    @param ticker is the ticker of a company
    finds the current date, and formats the url for
    the historical prices for the past 10 ten days.

    @returns the url of the Historical Prices Page eg shown:
    http://finance.yahoo.com/q/hp?s=AAPL
    &a=08&b=1&c=2014
    &d=09&e=12&f=2014&g=d
    """
    url = "http://finance.yahoo.com/q/hp?s=" + ticker 
    month, day, year = findCurrentDate()
    startM, startD, startY = DateBefore(deltaDays=10)
    url += "&a=" + startM + "&b=" + startD + "&c=" + startY
    url += "&d=" + month + "&e=" + day + "&f=" + year
    url += "&g=d" # d means daily information
    return url
    
def HtmlTableToList(descendants):
    """
    Takes in a weird Pattern of html
    returns a list of lists
    with each week's information  
    """
    offset = 4
    weekCounter = 1
    index = offset
    dailyData = []
    allData = [] 
    while(index < len(descendants)):
            #print("{0}\t{1}".format(index, str(descendants[index])) + "\n\n\n\n")
            dailyData.append(str(descendants[index]).strip())
            if(weekCounter % 7 == 0):
               allData.append(dailyData)
               dailyData = []
               index+=1
            weekCounter+=1
            index+=2
    return allData

def findCorrectTable(tables):
    """
    @param tables is the result of Beautiful Soup find_all('table')s
    """
    historicalPrices = None
    for table in tables:
        if 'class' in table.attrs and 'yfnc_datamodoutline1' in table['class']:
            print("Found table of Historical Prices\n")
            return table
    raise TickerError("Could not find the correct historical prices table in html page")     

def fetchHtmlResponse(req, tries, errorResponse):
    if tries == 0:
        raise TickerError("Could not fetch html page after five tries!\n{0}".format(errorResponse))
    try:
        return urllib2.urlopen(req)
    except urllib2.HTTPError as e:
        return fetchHtmlResponse(req, tries - 1, e)
        

def mainDownloadPrices(ticker):
    """
    This function:
    I. Generates the request with the use of func HistoricalPricesPage
    II. Opens the Webpage
    III. Passes the response to the BeautifulSoup parser ...
    IV. The parser finds the correct html table
    V. Calls HtmlTableToList to do exactly that ...
    
    @return a tuple of (HtmlTable, List) 
    """
    webpageRequest = parodyBrowser(HistoricalPricesPage(ticker))
    try:
        htmlPageResponse = fetchHtmlResponse(webpageRequest, 5, None)
        soup = BeautifulSoup(htmlPageResponse)
        tables = soup.find_all('table') 
        historicalPrices = findCorrectTable(tables)

        descendants = list(historicalPrices.children)
        if 'tr' in map(lambda tag: tag.name, descendants) and len(descendants) == 1:
            descendants = list(descendants[0].descendants)
            if 'td' in map(lambda tag: tag.name, descendants) and len(descendants) == 1:
                 descendants = descendants[0].descendants
        print(len(descendants))
        for index in range(1, len(descendants)):
            print("{0}\t{1}".format(index, str(descendants[index])) + "\n\n\n\n")
        allData = HtmlTableToList(descendants)
        for row in allData:
            print(row)
        return historicalPrices, allData
    except TickerError as e:
        raise TickerError("Ticker {0} failed!\n{1}".format(ticker, e))

def main():
    tickers = ["AAPL", "GOOG", "SKM", "KT", "DCM", "SCTY", "VLKAY"]
    #tickers = []
    #tickers.extend(askForTickers())
    infoFile = open("Results.html", "w") 
    for ticker in tickers:
        html, data = mainDownloadPrices(ticker)
        infoFile.write("<h2 style=\"text-align: center;\">{0}<h2>".format(ticker))
        infoFile.write(html.prettify())
main()
