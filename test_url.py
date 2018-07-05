# -*- coding: utf-8 -*-
"""
Created on Thu Jul  5 22:44:35 2018

@author: James
"""
import re
import requests

def parseImgurURL(url):
    image = ''
    image_url = ''

    # Firstly check to see if we need to read the HTML, or if we can 
    # read the file directly
    
    pattern = re.compile(r"^(?:https?\:\/\/)?(?:www\.)?(?:[mi]\.)?imgur\.com\/([a-zA-Z0-9,]+)$")
    m = pattern.match(url)
    if m:
        # we don't know the extension
        # so we have to rip it from the url
        # by reading the HTML, unfortunately.
        response = requests.get(url)
        if response.status_code != requests.codes.ok:
            print("Image download failed: HTML response code {}".format(response.status_code))
            return image, image_url

        html = response.text
        imageURLRegex = re.compile('<img src="(?P<url>(?:https?\:\/\/)?(:?[mi]\.)?imgur\.com\/(?P<image>[a-zA-Z0-9]+\.(?:jpg|jpeg|png|gif)))"')
        image = imageURLRegex.search(html)
        if image:
            image_url = "http:" + image.group("url")
            image = image.group("image")
        else:
            imageURLRegex = re.compile('<link rel="image_src"\s+href="(?:https?\:)?(?P<url>\/\/(:?[mi]\.)?imgur\.com\/(?P<image>[a-zA-Z0-9]+\.(?:jpg|jpeg|png|gif)))[^"]*"')
            image = imageURLRegex.search(html)
            if image:
               image_url = "http:" + image.group("url")
               image = image.group("image")
    else:
        imageURLRegex = re.compile('(https?\:\/\/)?(?:www\.)?(?:[mi]\.)?imgur\.com\/(?P<image>[^.]+\.(:?jpg|jpeg|png|gif))')
        image = imageURLRegex.match(url)
        if image:
            image_url = image.group(0)
            image = image.group("image")
            

    return image_url, image

image_url, image = parseImgurURL('')
print("url: {}\nImage:{}".format(image_url, image))