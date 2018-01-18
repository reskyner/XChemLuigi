
"""
rowbasedauth.py
"""
# lives at: /var/www/cgi-bin/proasisapi/v1.4

import sys, os
#from p3SConstants import dssPyPath
#if dssPyPath not in sys.path:
#	sys.path.insert(1, dssPyPath)

import string, time, re, csv

BLACKLISTDIR = "/usr/local/Proasis2/Data/BLACKLIST"

def readblcsv(curf):
	retdict = {}

	try:
		with open(curf, 'rb') as csvfile:
			blreader = csv.reader(csvfile, delimiter=',')
			for row in blreader:
				for entry in row:
					retdict.update({str(entry):1})

	except:
		#with open('/dls/science/groups/proasis/test.txt','w') as f:
			#f.write(str(sys.exc_info()))
			print sys.exc_info()
	return retdict



def GetUsername(inpStr):
	"""
	Get username from cookie Proasis3User (or Proasis2User)
	"""

	#with open('/dls/science/groups/proasis/test.txt', 'w') as f:
		#f.write(str(inpStr))

	inpStr = str(inpStr)
	c = dict(re.findall(r'\[(.+?)]=\[(.+?)]', inpStr))

	#with open('/dls/science/groups/proasis/test.txt', 'a') as f:
		#f.write(str(c))

	if "Proasis3User" in c.keys():
		return c["Proasis3User"]
	elif "Proasis2User" in c.keys():
		return c["Proasis2User"]
	else:
		return ""


def GetBlacklist(inpStr):
	"""
	for row based authentication
	"""
	
	retDict = {}
	#with open('/dls/science/groups/proasis/test.txt','w') as f:
	#	f.write(inpStr)
	# get curUser u from inpStr
	u = GetUsername(inpStr)
	u = str(inpStr)
	username = u.replace('username=','')

	# blacklist file has filename BLACKLISTDIR/curUser.dat
	# - it is a python dictionary of type {regnoA:1, regnoB:1, ...}
	# - where hits with regnoA,regnoB cannot be viewed by curUser
	# these files created by separate cron job
	
	curf = "%s/%s%s" % (BLACKLISTDIR, u, ".dat")
		
	curf = curf.replace('username=','')

	if not os.path.isfile(curf):
		return retDict
	
	# get blacklist as python dictionary
	retDict = readblcsv(curf)

	return retDict
