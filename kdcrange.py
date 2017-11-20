import requests, lxml.html, shutil, os, errno, sys

path = "f:"

# establish session
session = requests.session()
#login = session.get('https://www.pornhub.com/')
login = session.get('https://www.kink.com/login')
login_html = lxml.html.fromstring(login.text)
hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
form['username'] = "baeron"
form['password'] = "ringtoss"
response = session.post('https://www.kink.com/login', data=form)

# build list of pages for a particular model
def GetPageList(modelnum):
	url = GetModelURLFromNum(modelnum)
	page = session.get(url)
	modelpage = lxml.html.fromstring(page.text)
	pagecount = modelpage.xpath('//div[@class="page-minimal-numbers"]//a')
	pageurls = []
	if len(pagecount) > 0:
		if len(pagecount) == 1:
			lastpage = pagecount[0].attrib["href"].split("/")[5]
		else:
			lastpage = pagecount[1].attrib["href"].split("/")[5]
		for i in range(1,int(lastpage) + 1):
			pageurl = url + "/page/" + str(i)
			pageurls.append(url + "/page/" + str(i))
		return pageurls
	else:
		pageurls.append(url)
		return pageurls

# get a particular model's url
def GetModelURLFromNum(modelnum):
	page = session.get('https://www.kink.com/model/' + modelnum)
	modelpage = lxml.html.fromstring(page.text)
	urlpath = modelpage.xpath('//div[@class="shoot-thumb-models"]//a[contains(@href,' + modelnum + ')]')
	if len(urlpath) < 1:
		url = "https://www.kink.com/model/" + modelnum
	else:
		url = "https://www.kink.com" + urlpath[0].attrib["href"]
	return url

def GetShootsFromURL(pageurl):
	# https://www.kink.com/shoot/32747
	pageraw = session.get(pageurl)
	page = lxml.html.fromstring(pageraw.text)
	hrefs = page.xpath('//div[@class="script"]//a[contains(@href,"shoot")]')
	shooturls = []
	for child in hrefs:
		shooturls.append("https://www.kink.com" + child.attrib["href"])
	return shooturls

def GetOnlyHDLinkFromPage(pageurl):
	pageraw = session.get(pageurl)
	page = lxml.html.fromstring(pageraw.text)
	link = page.xpath('//div[@class="player"]//span[@data-quality="hd"]')
	data = link[0].attrib["data-url"]
	return data

def GetHDFromShootPage(pageurl,savepath):
	pageraw = session.get(pageurl)
	page = lxml.html.fromstring(pageraw.text)
	link = page.xpath('//div[@class="player"]//span[@data-quality="hd"]')
	data = link[0].attrib["data-url"]
	recoded = data.replace("/", "?")
	filename = recoded.split("?")[9]
	print "Retreiving " + filename + " from " + pageurl
	# start the download
	sdl = session.get(data, stream=True)
	if sdl.status_code == 200:
		if not os.path.exists(savepath + "/" + filename):
			with open(savepath + "/" + filename, 'wb') as f:
				sdl.raw.decode_content = True
				shutil.copyfileobj(sdl.raw, f)
		else:
			print savepath + "/" + filename + "already exists, skipping..."

def GetModelDetails(modelnum):
	modelurl = GetModelURLFromNum(modelnum)
	pageraw = session.get(modelurl)
	page = lxml.html.fromstring(pageraw.text)
	modelname = page.xpath('//meta[@name="description"]')
	mname = modelname[0].attrib["content"]
	model = Model(modelnum,modelurl,mname)
	return model
	
class Model:
	def __init__(self,number,url,name):
		self.name = name
		self.number = number
		self.url = url
	def show(self):
		print "Name: " + self.name
		print "Number: " + self.number
		print "URL: " + self.url
		
def GetModelContent(modelnum):
	model = GetModelDetails(modelnum)
	
	# create the model directory
	if not os.path.exists(model.name):
		os.makedirs(model.name)
	
	# build a list of model shoots
	pages = GetPageList(model.number)
	allshoots = []
	for page in pages:
		shoots = GetShootsFromURL(page)
		for shoot in shoots:
			allshoots.append(shoot)
	
	# use the list of shoots to build a list of HD links to iterate through
	urllist = []
	for shoot in allshoots:
		GetHDFromShootPage(shoot,model.name)

##
## Main loop
##
if len(sys.argv) <= 1:
	print "Requires a filename with a list of numbers for download"
	sys.exit()

filename = sys.argv[1]
f = open(filename)
for modelnumber in f:
	model = GetModelDetails(modelnumber)
	print "\n"
	print "--------------"
	model.show()	
	pages = GetPageList(modelnumber)
	print str(len(pages)) + " of content"
	allshoots = []
	for page in pages:
		shootlist = GetShootsFromURL(page)
		for shoot in shootlist:
			allshoots.append(shoot)
	
	print str(len(allshoots)) + " files for " + model.name
	
	# Do the download
	contentlist = GetModelContent(modelnumber)
f.close()