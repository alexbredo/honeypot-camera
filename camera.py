# Copyright (c) 2014 Alexander Bredo
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above
# copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials
# provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import tornado.ioloop
import tornado.web
import os, time

import datetime, math
from PIL import Image, ImageDraw, ImageEnhance


class CameraImageProcessor():
	def __init__(self, in_filename, out_filename, width=640, height=480):
		self.size = (width, height)
		self.in_filename = in_filename
		self.out_filename = out_filename

	def process(self, prefix, postfix):
		now = datetime.datetime.now()
		original = Image.open(self.in_filename)
		original.thumbnail(self.size, Image.ANTIALIAS)
		original = ImageEnhance.Brightness(original).enhance(self.getDaylightIntensity(now.hour)) # overwrite original
		watermark = Image.new("RGBA", original.size)
		waterdraw = ImageDraw.ImageDraw(watermark, "RGBA")
		waterdraw.text((4, 2), "%s @ %s -- %s" % (prefix, now, postfix))
		original.paste(watermark, None, watermark)
		original.save(self.out_filename, "JPEG")

	def getDaylightIntensity(self, hour):
		# D = [0; 24] and W = [0; 1]
		return 0.45 * math.sin(0.25 * hour + 4.5) + 0.5

class CameraHandler(tornado.web.RequestHandler):
	BOUNDARY = '--boundarydonotcross'
	HEADERS = {
        'Cache-Control': 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0',
        'Connection': 'close',
        'Expires': 'Mon, 3 Jan 2000 12:34:56 GMT',
        'Pragma': 'no-cache'
    }

	def get(self):
		for hk, hv in CameraHandler.HEADERS.items():
			self.set_header(hk, hv)

		# TODO: Do not process if current
		cip = CameraImageProcessor("img/Lighthouse.jpg", "img/camera.jpg")
		cip.process("CAM3: COMPANY Facility Management", "(c) 2014 by COMPANY Engineering AG")

		img_filename = "img/camera.jpg"
		for hk, hv in self.image_headers(img_filename).items():
			self.set_header(hk, hv)

		with open(img_filename, "rb") as f:
			self.write(f.read())

	def image_headers(self, filename):
		return {
			'X-Timestamp': int(time.time()),
			'Content-Length': os.path.getsize(filename),
			'Content-Type': 'image/jpeg',
		}

class RootHandler(tornado.web.RequestHandler):
	settings = {
		'title': 'COMPANY Facility Management',
		'refresh': 5,
	}

	def get(self):
		return self.render("templates/index.html", page=RootHandler.settings)

application = tornado.web.Application([
	(r'/camera.jpg', CameraHandler),
	(r'/', RootHandler),
	(r'/(favicon\.ico)', tornado.web.StaticFileHandler, {'path': 'static/'}),
	(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static/'}),
])

if __name__ == "__main__":
	application.listen(80)
	tornado.ioloop.IOLoop.instance().start()
