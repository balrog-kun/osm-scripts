#! /usr/bin/env python2
# vim: set fileencoding=utf8 :
# Py2 version of an API for managing OSM user messages - only sending
# supported at this time and even that may be broken
#
# Copyright (C) 2011  Andrzej Zaborowski
#
# This file is licensed under AGPLv3
#
# Requires libtidy
# Usage: call login(u, p) once, then sendusermsg(u, t, m) as many times
# as needed

import psycopg2, sys, os, xml.etree.cElementTree as ElementTree, \
	httplib, tidy, StringIO, urllib

hmc = None
cookie = {}
proto = None
host = None
ref = None

def reconnect():
	global hmc, cookie, proto, host
	if hmc is not None:
		hmc.close()
	if proto == 'http':
		hmc = httplib.HTTPConnection(host)
	elif proto == 'https':
		hmc = httplib.HTTPSConnection(host)
	else:
		raise Exception('unknown proto ' + proto)
def request(method, body, url):
	global hmc, cookie, proto, host, ref
	while 1:
		newproto, r = url.split('://', 1)
		try:
			newhost, path = r.split('/', 1)
		except:
			newhost, path = r, ''
		if newproto != proto or newhost != host or hmc is None:
			proto, host = newproto, newhost
			reconnect()
		headers = {}
		if cookie:
			headers['Cookie'] = '; '.join(
				[ k + '=' + cookie[k] for k in cookie ])
		if body is not None:
			headers['Content-Type'] = \
				'application/x-www-form-urlencoded'
		if ref is not None:
			headers['Referer'] = ref
		hmc.request(method, '/' + path, body, headers)
		try:
			r = hmc.getresponse()
		except httplib.ResponseNotReady:
			reconnect()
			hmc.request(method, '/' + path, body, headers)
			r = hmc.getresponse()
		loc = None
		for k, v in r.getheaders():
			if k == 'location':
				loc = v
				continue
			if k != 'set-cookie':
				continue
			for vv in v.split(','):
				c = vv.strip().split(';', 1)[0].split('=', 1)
				if len(c) == 2:
					cookie[c[0]] = c[1]
		if r.status not in [ 301, 302 ]:
			ref = url
			return r
		print('redirected to ' + loc)
		if method == 'POST':
			method = 'GET'
			body = None
		url = loc

inptag = '{http://www.w3.org/1999/xhtml}input'

def login(user, passwd):
	r = request('GET', None, 'https://www.openstreetmap.org/login')
	if r.status != 200:
		raise Exception('OSM login status ' + str(r.status))
	fields = {}
	r = StringIO.StringIO(str(tidy.parseString(r.read(), output_xhtml=1,
		add_xml_decl=1)).replace('&nbsp;', ' '))
	for field in ElementTree.parse(r).getiterator(inptag):
		if 'name' in field.attrib and 'value' in field.attrib:
			fields[field.attrib['name']] = field.attrib['value']
	fields['username'] = user
	fields['password'] = passwd
	fields['remember_me'] = 'no'
	for field in fields:
		fields[field] = fields[field].encode('utf-8')
	params = urllib.urlencode(fields)
	r = request('POST', params, 'https://www.openstreetmap.org/login')
	if r.status != 200:
		raise Exception('OSM login POST status ' + str(r.status))

def sendusermsg(user, msgtitle, msg):
	user = urllib.quote(user)
	r = request('GET', None,
		'http://www.openstreetmap.org/message/new/' + user)
	if r.status != 200:
		raise Exception('OSM status ' + str(r.status))
	fields = {}
	r = StringIO.StringIO(str(tidy.parseString(r.read(), output_xhtml=1,
		add_xml_decl=1)).replace('&nbsp;', ' '))
	for field in ElementTree.parse(r).getiterator(inptag):
		if 'name' in field.attrib and 'value' in field.attrib:
			fields[field.attrib['name']] = field.attrib['value']
	fields['message[title]'] = msgtitle
	fields['message[body]'] = msg
	for field in fields:
		fields[field] = fields[field].encode('utf-8')
	params = urllib.urlencode(fields)
	r = request('POST', params,
		'http://www.openstreetmap.org/message/new/' + user)
	if r.status != 200:
		raise Exception('OSM POST status ' + str(r.status))
