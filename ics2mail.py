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
		# for non empty value
		if value != "":
			# line started with " " is the continuation of previous => append
			if value.startswith(" "):
				exec("self.{0} += value.lstrip()").format(attribute)
			else:
				exec("self.{0} = value").format(attribute)

	def inTimeWindow(self, minutes=20):
		# event not at Advatech
		if self.location != "Advatech":
			# startTime not in the past and not in the future more than 20 minutes
			if timedelta(minutes=-minutes) < self.startTime - now < timedelta(minutes=minutes):
				return True
			# editTime not in the past and not in the future more than 30 minutes
			if timedelta(minutes=-minutes-10) < self.editTime - now < timedelta(minutes=minutes+10):
				return True

	def sendEmail(self):
		message = MIMEText(unicode(self.location, 'utf-8'),'plain','utf-8')
		message['From'] = u'Mariusz Słowiński <mslowinski@advatech.pl>'
		message['To'] = args.email
		prefix = ""
		if self.startTime < self.editTime < self.endTime:
			prefix = "[aktualizacja] "
		if self.startTime.hour == 2 and self.startTime.minute == 0:
			# whole day event
			message['Subject'] = self.startTime.strftime("%d.%m: ") + unicode(self.summary, 'utf-8')
		else:
			message['Subject'] = prefix + self.startTime.strftime("%H:%M") + " - " + self.endTime.strftime("%H:%M") + ": " + unicode(self.summary, 'utf-8')
		if args.debug:
			print message.as_string()
		else:
			smtp = smtplib.SMTP('jehu.advatech.pl')
			#smtp.login('login', 'haslo')
			try:
				smtp.sendmail("mslowinski@advatech.pl", [args.email], message.as_string())
			except SMTPException:
				print "Error: unable to send email"
			finally:
				smtp.quit()
		
	def printDetails(self):
		print 'startTime: \t{0}'.format(self.startTime)
		print 'endTime: \t{0}'.format(self.endTime)
		print 'editTime: \t{0}'.format(self.editTime)
		print 'summary: \t{0}'.format(self.summary)
		print 'location: \t{0}'.format(self.location)

parser = argparse.ArgumentParser(description='Send email based on calendar file.')
parser.add_argument('-d', '--debug', help='debug mode', action='store_true')
parser.add_argument('-f', '--file', type=file, metavar='file.ics', dest='icsfile')
parser.add_argument('-t', '--time', type=str, metavar='yyyy-mm-dd HH:MM', dest='now', help='use given time instead of now')
parser.add_argument('-e', '--email', type=str, metavar='', default="wyjscia-warszawa@advatech.pl", dest='email', help='use given email destination instead of %(default)s')
args = parser.parse_args()

if args.icsfile:
	icsfile = args.icsfile
else:
	icsfile = urllib.urlopen(icsurl)

if args.now:
	now = datetime.strptime(args.now, "%Y-%m-%d %H:%M")
	# set to local timezone
	now = now.replace(tzinfo=CEST())
else:
	now = datetime.now(CEST())

print now
bTodayEvent = False
events = []

for line in icsfile.read().splitlines():
	keyval = line.split(':')
	if 'BEGIN' == keyval[0] and 'VEVENT' == keyval[1]:
		bTodayEvent = False
	if keyval[0].startswith("DTSTART") and keyval[1][:8] == now.strftime("%Y%m%d"):
		bTodayEvent = True
		events.append(event())
		events[-1].setTime("startTime", keyval[1])
	if bTodayEvent and keyval[0].startswith("DTEND"):
		events[-1].setTime("endTime", keyval[1])
	if bTodayEvent and keyval[0] == 'LAST-MODIFIED':
		events[-1].setTime("editTime", keyval[1])
	if bTodayEvent and (keyval[0] == "SUMMARY" or keyval[0] == "LOCATION" or keyval[0] == "DESCRIPTION"): 
		# store atrribue name to...
		attribute = keyval[0].lower()
		events[-1].setAttribute(attribute, keyval[1].replace("\\,",","))
	if bTodayEvent and keyval[0].startswith(" "):
		#... append splited lines
		events[-1].setAttribute(attribute, keyval[0].replace("\\,",","))

for event in events:
	if event.inTimeWindow():
		if args.debug:
			event.printDetails()
		event.sendEmail()
