#!/usr/bin/env python
# encoding: utf-8

import praw
import argparse
import requests
import os
import imguralbum as ia
import re
import json


def is_valid(thing):
    # Could make this a single boolean statement
    # but that's a maintenance nightmare.
    if not thing.is_self:
        if thing.over_18 and args.no_nsfw:
            return False
        if thing.score < args.score:
            return False
        if "imgur.com" in thing.url:
            return True

    return False


def get_urls(generator, args):
    urls = []
    for thing in generator:
        if is_valid(thing) and thing.url not in urls:
            urls.append(thing.url)
    return urls


def download_images(url, args):
    # Check if it's an album
    try:
        downloader = ia.ImgurAlbumDownloader(url)

        if downloader.num_images() > args.length:
            return

        if not args.quiet:
            def image_progress(index, image_url, dest):
                print(
                    "Downloading image {} of {} from album {} to {}".format(index, downloader.num_images(), url, dest))

            downloader.on_image_download(image_progress)
        downloader.save_images(args.output)
    except ia.ImgurAlbumException as e:
        # Not an album, unfortunately.
        # or some strange error happened.
        if not e.msg.startswith("URL"):
            print(e.msg)
            return

        # Check if it's a silly url.
        pat = re.compile(r"(?:https?\:\/\/)?(?:www\.)?(?:m\.)?imgur\.com\/([a-zA-Z0-9]+)")
        m = pat.match(url)
        image = ''
        image_url = ''
        if m:
            # we don't know the extension
            # so we have to rip it from the url
            # by reading the HTML, unfortunately.
            response = requests.get(url)
            if response.status_code != requests.codes.ok:
                print("Image download failed: HTML response code {}".format(response.status_code))
                return

            html = response.text
            imageURLRegex = re.compile('<img src="(\/\/i\.imgur\.com\/([a-zA-Z0-9]+\.(?:' + args.extn + ')))"')
            image = imageURLRegex.search(html)
            if image:
                image_url = "http:" + image.group(1)
            else:
                imageURLRegex = re.compile('<link rel="image_src" +href="(?:https?\:)?(\/\/i\.imgur\.com\/([a-zA-Z0-9]+\.(?:' + args.extn + ')))"')
                image = imageURLRegex.search(html)
                if image:
                    image_url = "http:" + image.group(1)
            
        else:
            imageURLRegex = '(https?\:\/\/)?(?:www\.)?(?:m\.)?i\.imgur\.com\/([a-zA-Z0-9]+\.(?:' + args.extn + '))'
            image = re.match(imageURLRegex, url)
            if image:
                image_url = image.group(0)

        if not image_url:
            print("Image url {} could not be properly parsed.".format(url, image))
            return

        if not os.path.exists(args.output):
            os.makedirs(args.output)

        p = os.path.join(args.output, image.group(2))

        if not args.quiet:
            print("Downloading image {} to {}".format(image_url, p))

        imageRequest = requests.get(image_url)
        imageData = imageRequest.content
        with open(p, 'wb') as fobj:
            fobj.write(imageData)


def redditor_retrieve(r, args):
    user = r.redditor(args.username)
    method = getattr(user, "sumissions().{}".format(args.sort))
    gen = method(limit=args.limit)

    links = get_urls(gen, args)
    for link in links:
        download_images(link, args)


def subreddit_retrieve(r, args):
    sub = r.subreddit(args.subreddit)
    method = getattr(sub, "{}".format(args.sort))
    gen = method(limit=args.limit)
    links = get_urls(gen, args)
    for link in links:
        download_images(link, args)


def post_retrieve(r, args):
    submission_id = ""

    m = re.match(r"(?:https?\:\/\/)?(?:www\.)?reddit.com\/r\/(?P<sub>\w+)\/comments\/(?P<id>\w+).+", args.post)

    if m:
        submission_id = m.group("id")
    else:
        m = re.match(r"(?:https?\:\/\/)?redd\.it\/(?P<id>\w+)", args.post)
        if m:
            submission_id = m.group("id")

    submission = r.get_submission(submission_id=submission_id)

    if (is_valid(submission)):
        download_images(submission.url, args)
    else:
        print("Invalid URL given: {}".format(submission.url))


def read_credentials():
    ## This function expects to read a json file
    ## which contains a dictionary with five fields/keys:
    ## client_id, client_secret, user_agent, username, password
    ## All entries are strings. The first two keys are 14 and 27
    ## characters long respectively and come from the reddit API
    ## when you create a new app (there are some instructions in the main
    ## section below on how to do this.)
    ## The user_agent is the name of your reddit app,
    ## username and password are your reddit username and password
    with open('credentials.txt', 'r') as f1:
        creds: object = json.loads(f1.read())
        return creds


if __name__ == "__main__":
    # user_agent = "Image retriever 1.0.0 by /u/Rapptz"
    # r = praw.Reddit(user_agent=user_agent)

    #  UNCOMMENT this is if you need to login to reddit
    # To use this you will first need to register on Reddit
    # It does not appear to be possible with the new Reddit design
    # So you need to:
    # 1. click on 'Vist old-reddit'
    # 2. Log in
    # 3. Click on preferences
    # 4. Click on apps
    # 5. Scroll to the bottom and click on create another app
    # 6. Give your app a name (this goes in the user_agent field)
    # 7. Click on the script radio button
    # 8. Add http://localhost:8080 to the redirect uri
    # 9. Copy the "personal use script" code (14 chars), and the secret code (27 chars)
    #    These are your client_id and client_secret respectively
    #
    creds = read_credentials()

    r = praw.Reddit(client_id=creds['client_id'],
                    client_secret=creds['client_secret'],
                    user_agent=creds['user_agent'],
                    username=creds['username'],
                    password=creds['password'])

    parser = argparse.ArgumentParser(description="Downloads imgur images from a user, subreddit, and/or post.",
                                     usage="%(prog)s [options...]")
    parser.add_argument("--username", help="username to scrap and download from", metavar="user")
    parser.add_argument("--subreddit", help="subreddit to scrap and download from", metavar="sub")
    parser.add_argument("--post", help="post to scrap and download from", metavar="url")

    parser.add_argument("--sort", help="choose the sort order for submissions (default: new)",
                        choices=["hot", "new", "controversial", "top"], metavar="type", default="new")

    parser.add_argument("--limit", type=int, help="number of submissions to look for (default: 100)",
                        default=100, metavar="num")
    
    parser.add_argument("--extn", help="a | delimited list of file extensions, e.g. jpg|gif", metavar="extn",
                        default = "jpg|jpeg|png|gif")

    parser.add_argument("-q", "--quiet", action="store_true", help="doesn't print image download progress")
    parser.add_argument("-o", "--output", help="where to output the downloaded images", metavar="", default=".")
    parser.add_argument("--no-nsfw", action="store_true", help="only downloads images not marked nsfw")

    parser.add_argument("--score", help="minimum score of the image to download (default: 1)", type=int,
                        metavar="num", default=1)

    parser.add_argument("-l", "--length", help="skips album downloads over this length (default: 30)", type=int,
                        default=30, metavar="num")

    args = parser.parse_args()

    if args.username:
        redditor_retrieve(r, args)

    if args.subreddit:
        subreddit_retrieve(r, args)

    if args.post:
        post_retrieve(r, args)
