"""
up2stream urlresolver plugin
Copyright (C) 2015 tknorris

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import urllib
import urllib2
from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
from lib import jsunpack

class NoRedirection(urllib2.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response

class Up2StreamResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "up2stream"
    domains = ["www.up2stream.com"]
    pattern = '//((?:www\.)?up2stream.com)/view\.php.+?ref=([0-9a-zA-Z]+)'

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)

        headers = {
                   'User-Agent': common.IOS_USER_AGENT,
                   'Referer': web_url
        }

        html = self.net.http_GET(web_url, headers=headers).content

        for match in re.finditer('(eval\(function.*?)</script>', html, re.DOTALL):
            html += jsunpack.unpack(match.group(1))

        match = re.findall('<source[^>]*src="([^"]+)', html)
        match += re.findall('"src","([^"]+)', html)

        try:
            stream_url = match[-1]

            r = urllib2.Request(stream_url, headers=headers)
            r = int(urllib2.urlopen(r, timeout=15).headers['Content-Length'])

            if r > 1048576:
                stream_url += '|' + urllib.urlencode(headers)
                return stream_url
        except:
            UrlResolver.ResolverError("File Not Playable")

    def get_url(self, host, media_id):
        return 'http://up2stream.com/view.php?ref=%s' % media_id
    
    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r:
            return r.groups()
        else:
            return False

    def valid_url(self, url, host):
        return re.search(self.pattern, url) or 'up2stream' in host
