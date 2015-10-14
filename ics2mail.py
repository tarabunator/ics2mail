#!/usr/bin/python
# -*- coding: utf8 -*-

import argparse
from datetime import datetime, timedelta, tzinfo
import urllib
import smtplib
from email.mime.text import MIMEText

# must be set staticaly because crontab can't handle long command
icsurl='https://www.google.com/calendar/ical/t6domouc4g5krr6rfq2ojuchfg%40group.calendar.google.com/private-da82764557c2c4000c6da23019bbcfbd/basic.ics'

class CEST(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=+2)

	def tzname(self, dt):
		return "CEST"

	def dst(self, dt):
		return timedelta(0)

class event:
	"""calendar event class"""
	def __init__(self):
		self.summary = ""
		self.location = "Advatech"
		self.description = ""

	def setTime(self, attribute, time):
		if not time.endswith("Z"):
			time += "T0000Z"
		exec('self.{0} = datetime.strptime(time, "%Y%m%dT%H%M%SZ")'.format(attribute))
		# set to local timezone
		exec('self.{0} = self.{0}.replace(tzinfo=CEST())'.format(attribute))
		# set to local time
		exec('self.{0} += CEST().utcoffset(self.{0})'.format(attribute))

	def setAttribute(self, attribute, value):
		if value != "":
			if value.startswith(" "):
				exec("self.{0} += value.lstrip()").format(attribute)
			else:
				exec("self.{0} = value").format(attribute)

	def inTimeWindow(self, minutes=20):
		delta = self.startTime - datetime.now(CEST())
		# not in the past and not in the future more than 20 minutes
		if timedelta(-minutes) < delta < timedelta(minutes) and self.location != "Advatech":
			return True

	def sendEmail(self):
		message = MIMEText(unicode(self.location, 'utf-8'),'plain','utf-8')
		message['From'] = u'Mariusz Słowiński <mslowinski@advatech.pl>'
		message['To'] = 'wyjscia-warszawa@advatech.pl'
		if self.startTime.hour == 2 and self.startTime.minute == 2:
			# whole day event
			message['Subject'] = self.startTime.strftime("%d.%m: ") + self.summary
		else:
			message['Subject'] = self.startTime.strftime("%H:%M") + " - " + self.endTime.strftime("%H:%M") + ": " + self.summary
		print message.as_string()
		smtp = smtplib.SMTP('jehu.advatech.pl')
		#smtp.login('login', 'haslo')
		try:
			smtp.sendmail("mslowinski@advatech.pl", ["wyjscia-warszawa@advatech.pl"], message.as_string())
		except SMTPException:
			print "Error: unable to send email"
		finally:
			smtp.quit()
		
	def printDetails(self):
		print 'startTime: \t{0}'.format(self.startTime)
		print 'endTime: \t{0}'.format(self.endTime)
		print 'summary: \t{0}'.format(self.summary)
		print 'location: \t{0}'.format(self.location)

parser = argparse.ArgumentParser(description='Send email based on calendar file.')
parser.add_argument('-d', '--debug', help='debug mode', action='store_true')
parser.add_argument('-v', '--verbose', help='verbose mode', action='store_true')
parser.add_argument('-f', '--file', type=file, metavar='file.ics', dest='icsfile')
args = parser.parse_args()

if args.debug:
	print args

if args.icsfile:
	icsfile = args.icsfile
else:
	icsfile = urllib.urlopen(icsurl)

bTodayEvent = False
today = datetime.now(CEST()).strftime("%Y%m%d")
events = []

for line in icsfile.read().splitlines():
	keyval = line.split(':')
	if 'BEGIN' == keyval[0] and 'VEVENT' == keyval[1]:
		bTodayEvent = False
	if keyval[0].startswith("DTSTART") and keyval[1][:8] == today:
		bTodayEvent = True
		events.append(event())
		events[-1].setTime("startTime", keyval[1])
	if bTodayEvent and keyval[0].startswith("DTEND"):
		events[-1].setTime("endTime", keyval[1])
	if bTodayEvent and (keyval[0] == "SUMMARY" or keyval[0] == "LOCATION" or keyval[0] == "DESCRIPTION"): 
		# store atrribue name to...
		attribute = keyval[0].lower()
		events[-1].setAttribute(attribute, keyval[1].replace("\\,",","))
	if bTodayEvent and keyval[0].startswith(" "):
		#... append splited lines
		events[-1].setAttribute(attribute, keyval[0].replace("\\,",","))

for event in events:
	if args.debug:
		event.printDetails()
	if event.inTimeWindow():
		if args.verbose:
			event.printDetails()
		event.sendEmail()
