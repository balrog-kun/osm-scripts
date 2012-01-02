#! /usr/bin/env python2
# vim: set fileencoding=utf8 :
# Reverse geocode a location using Nominatim
#
# Copyright (C) 2011  Andrzej Zaborowski
#
# This file is licensed under AGPLv3

import psycopg2, sys, os, xml.etree.cElementTree as ElementTree, httplib

# FIXME: a single connection can be used for many queries

def reverse(ll, lingos='pl', zoom=15, email='balrogg@gmail.com'):
	hc = httplib.HTTPConnection('nominatim.openstreetmap.org')
	hc.request('GET', '/reverse?lat=' + str(ll[0]) + '&lon=' + str(ll[1]) +
		'&accept-language=' + lingos + '&zoom=' + str(zoom) +
		'&addressdetails=0&email=' + email)
	r = hc.getresponse()
	if r.status == 200:
		r = ElementTree.parse(r).getroot()
		if r.tag == 'reversegeocode' and r[0].tag == 'result':
			hc.close()
			return r[0].text.strip()
		else:
			hc.close()
			raise Exception(repr(r))
	else:
		hc.close()
		raise Exception(repr(r))
