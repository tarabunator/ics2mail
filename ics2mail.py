#!/usr/bin/python
# -*- coding: utf8 -*-

from datetime import datetime, timedelta, tzinfo
import urllib
import smtplib
from email.mime.text import MIMEText

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

	def setAttribute(self, attribute, value):
		if value != "":
			if value.startswith(" "):
				exec("self.{0} += value.lstrip()").format(attribute)
			else:
				exec("self.{0} = value").format(attribute)

	def inTimeWindow(self):
		delta = self.startTime - datetime.now()
		# not in the past and not in the future more than 20 minutes
		if timedelta(minutes=-20) < delta < timedelta(minutes=20) and self.location != "Advatech":
			return True

	def sendEmail(self):
		message = MIMEText(unicode(self.location, 'utf-8'),'plain','utf-8')
		message['From'] = u'Mariusz Słowiński <mslowinski@advatech.pl>'
		message['To'] = 'wyjscia-warszawa@advatech.pl'
		if self.startTime.hour == 0 and self.startTime.minute == 0:
			message['Subject'] = self.startTime.strftime("%d.%m: ") + self.summary
		else:
			# add local time difference
			self.startTime += CEST().utcoffset(self.startTime)
			self.endTime += CEST().utcoffset(self.endTime)
			message['Subject'] = self.startTime.strftime("%H:%M") + " - " + self.endTime.strftime("%H:%M") + ": " + self.summary
		print message.as_string()
		smtp = smtplib.SMTP('jehu.advatech.pl')
		smtp.login('login', 'haslo')
		try:
			smtp.sendmail("mslowinski@advatech.pl", ["wyjscia-warszawa@advatech.pl"], message.as_string())
		except SMTPException:
			print "Error: unable to send email"
		finally:
			smtp.quit()
		

events = []

icsfile = urllib.urlopen(icsurl)

for line in icsfile.read().splitlines():
	keyval = line.split(':')
	if 'BEGIN' == keyval[0] and 'VEVENT' == keyval[1]:
		events.append(event())
	if keyval[0].startswith("DTSTART"):
		events[-1].setTime("startTime", keyval[1])
	if keyval[0].startswith("DTEND"):
		events[-1].setTime("endTime", keyval[1])
	if keyval[0] == "SUMMARY" or keyval[0] == "LOCATION" or keyval[0] == "DESCRIPTION": 
		attribute = keyval[0].lower()
		events[-1].setAttribute(attribute, keyval[1].replace("\\,",","))
	if keyval[0].startswith(" "):
		events[-1].setAttribute(attribute, keyval[0].replace("\\,",","))

datetime.now().strftime("%Y-%m-%d %H:%M")

for event in events:
	if event.inTimeWindow():
		event.sendEmail()
