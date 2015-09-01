﻿#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Crunchyroll Export Script DX - Last Updated 2014/07/16
Removes need for rtmpExplorer
ORIGINAL SOURCE:
  http://www.darkztar.com/forum/showthread.php?219034-Ripping-videos-amp-subtitles-from-Crunchyroll-%28noob-friendly%29
"""

# import lxml
import os
import re
import shutil
import subprocess
import sys
import HTMLParser

import altfuncs
from bs4 import BeautifulSoup
from crunchyDec import CrunchyDec
from unidecode import unidecode

# ----------

print '''
--------------------------
---- Start New Export ----
--------------------------

CrunchyRoll Downloader Toolkit DX v0.98

Crunchyroll hasn't changed anything.

If you don't have a premium account, go and sign up for one now. It's well worthit, and supports the animators.

----------
'''

# ----------

print 'Booting up...'
try:
    page_url = sys.argv[1]
except IndexError:
    page_url = raw_input('Please enter Crunchyroll video URL:\n')

try:
    seasonnum, epnum = sys.argv[2:4]
except ValueError:
    try:
        epnum = str(int(sys.argv[2]))
        seasonnum = ''
    except IndexError:
        # sys.exit('No season or episode numbers.')
        seasonnum, epnum = '', ''
        pass


# ----------

try:
    int(page_url)
    page_url = 'http://www.crunchyroll.com/media-' + page_url
except ValueError:
    if not page_url.startswith('http://') and not page_url.startswith('https://'):
        page_url = 'http://' + page_url
    try:
        int(page_url[-6:])
    except ValueError:
        if bool(seasonnum) and bool(epnum):
            page_url = altfuncs.vidurl(page_url, seasonnum, epnum)
        elif bool(epnum):
            page_url = altfuncs.vidurl(page_url, 1, epnum)
        else:
            page_url = altfuncs.vidurl(page_url, False, False)

subprocess.call('title ' + page_url.replace('http://www.crunchyroll.com/', ''), shell=True)

# ----------

lang1, lang2 = altfuncs.config()
player_revision = altfuncs.playerrev(page_url)
html = altfuncs.gethtml(page_url)

h = HTMLParser.HTMLParser()
title = re.findall('<title>(.+?)</title>', html)[0].replace('Crunchyroll - Watch ', '')
if len(os.getcwd()+'\\export\\'+title+'.flv') > 255:
    title = re.findall('^(.+?) \- ', title)[0]

# title = h.unescape(unidecode(title)).replace('/', ' - ').replace(':', '-').
# replace('?', '.').replace('"', "''").replace('|', '-').replace('&quot;',"''").strip()

### Taken from http://stackoverflow.com/questions/6116978/python-replace-multiple-strings ###
rep = {' / ': ' - ', '/': ' - ', ':': '-', '?': '.', '"': "''", '|': '-', '&quot;': "''", 'a*G':'a G', '*': '#', u'\u2026': '...'}

rep = dict((re.escape(k), v) for k, v in rep.iteritems())
pattern = re.compile("|".join(rep.keys()))
title = unidecode(pattern.sub(lambda m: rep[re.escape(m.group(0))], title))

### End stolen code ###

subprocess.call('title ' + title.replace('&', '^&'), shell=True)

# ----------

media_id = page_url[-6:]
xmlconfig = BeautifulSoup(altfuncs.getxml('RpcApiVideoPlayer_GetStandardConfig', media_id), 'xml')

try:
    if '4' in xmlconfig.find_all('code')[0]:
        print xmlconfig.find_all('msg')[0].text
        sys.exit()
except IndexError:
    pass

vid_id = xmlconfig.find('media_id').string

# ----------

try:
    host = xmlconfig.find('host').string
except AttributeError:
    print 'Downloading 2 minute preview.'
    media_id = xmlconfig.find('media_id').string
    xmlconfig = BeautifulSoup(altfuncs.getxml('RpcApiVideoEncode_GetStreamInfo', media_id), 'xml')
    host = xmlconfig.find('host').string

if re.search('fplive\.net', host):
    url1 = re.findall('.+/c[0-9]+', host).pop()
    url2 = re.findall('c[0-9]+\?.+', host).pop()
else:
    url1 = re.findall('.+/ondemand/', host).pop()
    url2 = re.findall('ondemand/.+', host).pop()
filen = xmlconfig.find('file').string

# ----------


def video():
    print 'Downloading video...'
    cmd = '.\\video-engine\\rtmpdump -r "' + url1 + '" -a "' \
          + url2 + '" -f "WIN 11,8,800,50" -m 15 -W "http://static.ak.crunchyroll.com/flash/' \
          + player_revision + '/ChromelessPlayerApp.swf" -p "' + page_url + '" -y "' + filen + \
          '" -o "' + title + '.flv"'
    error = subprocess.call(cmd)
    # error = 0

    num = 1
    while error != 0 and num < 4:
        if error == 1:
            print '\nVideo failed to download, trying again. (' + str(num) + '/3)'
            error = subprocess.call(cmd)
            num += 1
        if error == 2:
            print '\nVideo download is incomplete, resuming. (' + str(num) + '/3)'
            error = subprocess.call(cmd + ' -e')
            num += 1

    if error != 0:
        print '\nVideo failed to download. Writing error...'
        if os.path.exists('error.log'):
            log = open('error.log', 'a')
        else:
            log = open('error.log', 'w')
        log.write(page_url + '\n')
        log.close()
        os.remove('.\\' + title + '.flv"')
        sys.exit()

# ----------


def subtitles(eptitle):
    global sub_id

    xmllist = altfuncs.getxml('RpcApiSubtitle_GetListing', media_id)
    xmllist = unidecode(xmllist).replace('><', '>\n<')

    global hardcoded
    if '<media_id>None</media_id>' in xmllist:
        print 'The video has hardcoded subtitles.'
        hardcoded = True
        sub_id = False
    else:
        try:
            sub_id = re.findall("id=([0-9]+)' title='\["+re.escape(unidecode(lang1)), xmllist)[0]
            hardcoded = False
            lang = lang1
        except IndexError:
            try:
                sub_id = re.findall("id=([0-9]+)' title='\["+re.escape(unidecode(lang2)), xmllist)[0]
                print 'Language not found, reverting to ' + lang2 + '.'
                hardcoded = False
                lang = lang2
            except IndexError:
                try:
                    sub_id = re.findall("id=([0-9]+)' title='\[English", xmllist)[0]  # default back to English
                    print 'Backup language not found, reverting to English.'
                    hardcoded = False
                    lang = 'English'
                except IndexError:
                    print "The video's subtitles cannot be found, or are region-locked."
                    hardcoded = True
                    sub_id = False

    if not hardcoded:
        xmlsub = altfuncs.getxml('RpcApiSubtitle_GetXml', sub_id)
        formattedsubs = CrunchyDec().returnsubs(xmlsub)
        subfile = open(eptitle + '.ass', 'wb')
        subfile.write(formattedsubs.encode('utf-8-sig'))
        subfile.close()
        shutil.move(eptitle + '.ass', os.path.join(os.getcwd(), 'export', ''))

if 'subs' in sys.argv:
    subtitles(title)
    subs_only = True
    hardcoded = True  # bleh
else:
    video()
    subtitles(title)
    shutil.move(title + '.flv', os.path.join(os.getcwd(), 'export', ''))

    print 'Starting mkv merge'
    if hardcoded:
        subprocess.call('"video-engine\mkvmerge.exe" -o ".\export\\' + title + '.mkv" --language 1:jpn -a 1 -d 0 ' +
                        '".\export\\' + title + '.flv"')
    else:
        sublang = {u'Español (Espana)': 'spa', u'Français (France)': 'fre', u'Português (Brasil)': 'por',
                   u'English': 'eng', u'Español': 'spa', u'Türkçe': 'tur', u'Italiano': 'ita',
                   u'العربية': 'ara', u'Deutsch': 'deu'}[lang]
        subprocess.call('"video-engine\mkvmerge.exe" -o ".\export\\' + title + '.mkv" --language 1:jpn -a 1 -d 0 ' +
                        '".\export\\' + title + '.flv" --language 0:' + sublang + ' -s 0 ".\export\\'+title+'.ass"')
    print 'Merge process complete'
    subs_only = False

print
print '----------'
print

print 'Starting Final Cleanup'
if not subs_only:
    os.remove(os.path.join(os.getcwd(), 'export', '') + title + '.flv')
if not hardcoded or not subs_only:
    os.remove(os.path.join(os.getcwd(), 'export', '') + title + '.ass')
print 'Cleanup Complete'
