#
# This script creates an input list, telnets to each device, logs on, gathers data and tests dial backup.
# It can be run using:	python isdn.test.py
#
#
# by:	TCDH
# on:	01/11/06
# release#11
# revised:	02/20/07	Changed logon loop testing.
#		03/19/07	Changed notificatio to SNMP.

import random, re, smtplib, socket, string, telnetlib, threading, time
from pysnmp import role, v2c, asn1
from time import strftime
from threading import Thread


class ISDNTest(threading.Thread):
	def __init__(self, host):
		""" This instantiates the class and tries to open a connection to the device,
		with error checking. """
		Thread.__init__(self)
		self.host = host
		self.data = ""
		try:
			self.tn = telnetlib.Telnet(self.host)
		except socket.error, err:
			if "Operation timed out" in err:
				dialTestResult[self.host] = ["connection timed out"]
				return
			elif "getaddrinfo failed" in err:
				dialTestResult[self.host] = ["DNS resolution failed"]
				return
			elif "No route to host" in err:
				dialTestResult[self.host] = ["device unreachable"]
				return
			elif "Network is unreachable" in err:
				dialTestResult[self.host] = ["device unreachable"]
				return
			else:
				dialTestResult[self.host] = ["unspecified network error"]
				return

	def run(self):
		""" This function is the main function. It calls the Logon, CheckL1, CheckForConnection, 
		GetDialString, GetInterface and DialTest functions. """
		connect_status = self.Logon()
		if connect_status  == "authfail":
			dialTestResult[self.host] = ["authentication failed"]
			self.tn.close()
			return
		L1_status = self.CheckL1()
		if "DEACTIVATED" in L1_status:
			dialTestResult[self.host] = ["L1 DEACTIVATED"]
			return
		on_dbu = self.CheckForConnection()
		if on_dbu == "connected":
			dialTestResult[self.host] = ["already on dial backup"]
			return
		dialString = self.GetDialString()
		if dialString == "missing":
			dialTestResult[self.host] = ["dial string missing"]
			return
		interface = self.GetInterface()
		interfaces = interface.split('\r\n')
		for x in range(len(interfaces)):
			if ":" not in interfaces[x]:
				continue
			dialResult = self.DialTest(dialString, interfaces[x])
			if dialResult == "ISDN connection failed":
				dialTestResult[str(self.host + "_" +interfaces[x])] = "ISDN connection failed"
				self.tn.write("cle int vi1\n")
				time.sleep(14)
			elif dialResult == "EIGRP neighbor relationship failed":
				dialTestResult[str(self.host + "_" +interfaces[x])] = "EIGRP neighbor relationship failed"
				self.tn.write("cle int vi1\n")
				time.sleep(14)
			else:
				continue
		self.tn.write("exit\n")
		self.tn.close()

	def Logon(self):
		""" This function attempts to logon to the device 3 times."""
		for x in range(2):
			self.tn.read_until("Username:", 7)
			self.tn.write(user + "\n")
			(index, match, read) = self.tn.expect(["Password:"], 7)
			self.tn.write(pswd + "\n")
			(index, match, read) = self.tn.expect([self.host.upper()], 7)
			if match:
				return "connected"
		return "authfail"

	def CheckL1(self):
		""" This function checks for an active layer 1 connection."""
		self.tn.write("term len 0\n")
		self.tn.expect([self.host.upper()], 7)
		self.tn.write("sh isdn stat | i ACTIV\n")
		rc = self.tn.read_until(self.host.upper() + "#", 7)
		return rc

	def CheckForConnection(self):
		""" This function checks for an active ISDN connection."""
		self.tn.write("term len 0\n")
		self.tn.expect([self.host.upper()], 7)
		self.tn.write("sh dialer | i Connected\n")
		(index, match, read) = self.tn.expect(['LAKATMBK', 'L17REFTB'], 7)
		if match:
			return "connected"
		return

	def GetDialString(self):
		""" This function extracts the dial string."""
		self.tn.write("term len 0\n")
		self.tn.expect([self.host.upper() + "#"], 7)
		self.tn.write("sh dialer\n")
		self.data = self.tn.read_until(self.host.upper() + "#", 7)
		match = re.search("\d\d\d\d\d\d\d+", self.data)
		if match is not None:
			rc = match.group()
		else:
			rc = "missing"
		return rc

	def GetInterface(self):
		""" This function extracts all the dial interfaces."""
		self.tn.write("term len 0\n")
		self.tn.expect([self.host.upper()], 7)
		self.tn.write("sh dialer | i = ISDN\n")
		rc = self.tn.read_until(self.host.upper() + "#", 7)
		rc = rc.replace(" - dialer type = ISDN", "")
		return rc

	def DialTest(self, dS, int):
		""" This function uses all the previous information to execute a dial backup test on
		the specified interface with the appropiate dial string. It checks to see if a connection
		establishes. It then checks to see if an EIGRP neighbor connection establishes."""
		if "#" in int:
			return
		elif ":23" in int:
			return
		else:
			pass
		self.tn.write("isdn test call int " +int + " " + dS + "\n")
		time.sleep(10)
		self.tn.write("sh dialer | i Connected\n")
		(index, match, read) = self.tn.expect(["LAKATMBK", "L17REFTB"], 7)
		if not match:
			self.tn.write("cle int vi1\n")
			time.sleep(5)
			self.tn.write("isdn test call int " +int + " " + dS + "\n")
			time.sleep(10)
			self.tn.write("sh dialer | i Connected\n")
			(index, match, read) = self.tn.expect(["LAKATMBK", "L17REFTB"], 7)
			if not match:
				return "ISDN connection failed"
		time.sleep(10)
		self.tn.write("sh ip eigrp nei\n")
		(index, match, read) = self.tn.expect(["10.100.10.1", "10.251.250.2"], 7)
		if not match:
			return "EIGRP neighbor relationship failed"
		self.tn.write("cle int vi1\n")
		time.sleep(15)

class InputList(threading.Thread):
	def __init__(self, host):
		""" This instantiates the class and tries to open a connection to the device,
		with error checking. """
		Thread.__init__(self)
		self.host = host
		try:
			self.tn = telnetlib.Telnet(self.host)
		except socket.error, err:
			if "Operation timed out" in err:
				dialTestResult[self.host] = ["connection timed out"]
				return
			elif "getaddrinfo failed" in err:
				dialTestResult[self.host] = ["DNS resolution failed"]
				return
			elif "No route to host" in err:
				dialTestResult[self.host] = ["device unreachable"]
				return
			elif "Network is unreachable" in err:
				dialTestResult[self.host] = ["device unreachable"]
				return
			else:
				dialTestResult[self.host] = ["unspecified network error"]
				return

	def run(self):
		""" This function is the main function. It calls the Logon and CreateList functions. """
		connect_status = self.Logon()
		if connect_status  == "authfail":
			dialTestResult[self.host] = ["authentication failed"]
			self.tn.close()
			return
		list = self.CreateList()
		self.tn.write("exit\n")
		self.tn.close()

	def Logon(self):
		""" This function attempts to logon to the device 3 times."""
		for x in range(2):
			self.tn.read_until("Username:", 7)
			self.tn.write(user + "\n")
			(index, match, read) = self.tn.expect(["Password:"], 7)
			self.tn.write(pswd + "\n")
			(index, match, read) = self.tn.expect([self.host.upper()], 7)
			if match:
				return "connected"
			if not match:
				if x == 2:
					return "authfail"
				else:
					continue

	def CreateList(self):
		""" This function creates the input list for the ISDN test. """
		self.tn.write("term len 0\n")
		self.tn.expect([self.host.upper()], 7)
		self.tn.write("conf t\n")
		self.tn.expect([self.host.upper() + "(config)"], 7)
		self.tn.write("no snmp-server host 192.168.136.52 public isdn config snmp\n")
		self.tn.expect([self.host.upper() + "(config)"], 7)
		self.tn.write("exit\n")
		self.tn.expect([self.host.upper()], 7)
		self.tn.write("sh start | i username\n")
		list = self.tn.read_until(self.host.upper() + "#", 20)
		lists = list.split("username ")
		for x in range(len(lists)):
			match = re.search("^\w+", lists[x])
			if match:
				input[match.group()] = [self.host]
				
class FixConfig(threading.Thread):
	def __init__(self, host):
		""" This instantiates the class and tries to open a connection to the device,
		with error checking. """
		Thread.__init__(self)
		self.host = host
		try:
			self.tn = telnetlib.Telnet(self.host)
		except socket.error, err:
			if "Operation timed out" in err:
				dialTestResult[self.host] = ["connection timed out"]
				return
			elif "getaddrinfo failed" in err:
				dialTestResult[self.host] = ["DNS resolution failed"]
				return
			elif "No route to host" in err:
				dialTestResult[self.host] = ["device unreachable"]
				return
			elif "Network is unreachable" in err:
				dialTestResult[self.host] = ["device unreachable"]
				return
			else:
				dialTestResult[self.host] = ["unspecified network error"]
				return

	def run(self):
		""" This function is the main function of teh class. It calls the Logon and AddSNMP 
		function."""
		connect_status = self.Logon()
		if connect_status  == "authfail":
			dialTestResult[self.host] = ["authentication failed; config update failed"]
			self.tn.close()
			return
		updateConfig = self.AddSNMP()
		if updateConfig  == "config write failed":
			dialTestResult[self.host] = ["config write failed"]
			return
		self.tn.write("exit\n")
		self.tn.close()


	def Logon(self):
		""" This function attempts to logon to the device 3 times."""
		for x in range(2):
			self.tn.read_until("Username:", 7)
			self.tn.write(user + "\n")
			(index, match, read) = self.tn.expect(["Password:"], 7)
			self.tn.write(pswd + "\n")
			(index, match, read) = self.tn.expect([self.host.upper()], 7)
			if match:
				return "connected"
			if not match:
				if x == 2:
					return "authfail"
				else:
					continue
		
	def AddSNMP(self):
		""" This function adds the snmp-server host statement back into the routers' config. """
		self.tn.write("term len 0\n")
		self.tn.expect([self.host.upper()], 7)
		self.tn.write("conf t\n")
		self.tn.expect([self.host.upper() + "(config)"], 7)
		self.tn.write("snmp-server host 192.168.136.52 public isdn config snmp\n")
		self.tn.expect([self.host.upper() + "(config)"], 7)
		self.tn.write("exit\n")
		self.tn.expect([self.host.upper()], 7)
		self.tn.write("wr\n")
		(index, match, read) = self.tn.expect(["[OK]"], 15)
		if not match:
			return "config write failed"
		
def countActive():
	""" This function returns the number of Getter threads that are alive """
	numActive = 0
	for thread in threadList:
		if thread.isAlive():
			numActive += 1
	return numActive

def emailResult(e, s, r, m):
	""" This function send emails based on the input. """
	mailServer = smtplib.SMTP(e)
	mailServer.sendmail(s, r, m)
	mailServer.quit()

def SendTrap(msg, PayloadOID):
	req = v2c.TRAPREQUEST()
	req['encoded_oids'] = [
		asn1.OBJECTID().encode('.1.3.6.1.2.1.1.3.0'),  # uptime
		asn1.OBJECTID().encode('.1.3.6.1.6.3.1.1.4.1.0'),  # trap OID
		asn1.OBJECTID().encode(PayloadOID)  # your payload
		]
	
	req['encoded_vals'] = [
		asn1.TIMETICKS().encode(int(time.time())),
		asn1.OBJECTID().encode('1.3.6.1.4.1.3.1.1'),
		asn1.OCTETSTRING().encode(msg)
		]
	role.manager(('192.168.136.51', 162)).send(req.encode())

backupRouters = ["lakatmbk1", "l17reftbk1"]
emailsrvr = "######"
dialTestResult = {}
input = {}
log = (file(r"c:\logs\isdn.test.log", "a"))
maxThreads = 20
pswd = "#####"
receiverList = ["#####", "#####"]
#receiverList = ["<chris.hallman@publix.com>"]
sender = "#####"
subject = "ISDN test call results"
text = ""
threads = []
threadList = []
user = "#####"
log.write("\nisdn.test script started -" + strftime(" %H:%M:%S %x") + "\n")
log.flush()

for entry in backupRouters:
	threads = InputList(entry)
	threadList.append(threads)
	threads.start()

for thread in threadList:
	thread.join()

for k, v in input.iteritems():
	if "support" in k:
		continue
	if "LAKATMBK" in k:
		continue
	while countActive() >= maxThreads:
		time.sleep(1)
	threads = ISDNTest(k)
	threadList.append(threads)
	threads.start()

for thread in threadList:
	thread.join()

for entry in backupRouters:
	threads = FixConfig(entry)
	threadList.append(threads)
	threads.start()

for thread in threadList:
	thread.join()

dialTestResultSorted = sorted(dialTestResult.items())
for x in range(len(dialTestResultSorted)):
	SendTrap("NET0202 - " + str(dialTestResultSorted[x]).replace("[", "").replace("]", "").replace("'", "").replace("(", "").replace(")", "").replace(",", "\t"), "1.3.6.1.4.1.9.42.43.1")
	text = text + str(dialTestResultSorted[x]) + "\n\r"
text = text.replace("[", "").replace("]", "").replace("'", "").replace("(", "").replace(")", "").replace(",", "\t")
log.write(text)
log.flush()

SendTrap("NET0202 - ISDN dial backup test completed", "1.3.6.1.4.1.9.42.7.1")

log.write("\nisdn.test script completed -" + strftime(" %H:%M:%S %x") + "\n")
log.flush()
log.close()