#!/usr/bin/env python
# encoding: utf-8

import praw
import argparse
import requests
import os
import imguralbum as ia
import re
import json
from PIL import Image
from io import BytesIO


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

def parseImgurURL(url, args):
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
            
            p = re.compile('_d\.(jpg|jpeg|png|gif)')
            md = p.search(image)
            
            if md:
                p = re.compile('(?P<prefix>^.*)_d\.(?P<suffix>jpg|jpeg|png|gif).*$')
                image_url = p.sub('\g<prefix>\g<suffix>', image_url)
                image = p.sub('\g<prefix>\g<suffix>', image)
 
    return image_url, image
    
def isCorrectExtension(image, args):
    regex = re.compile(r"^[a-zA-Z0-9]+\.(.*)$")
    fileExtn = regex.match(image)
    
    if fileExtn:
        fileExtn = fileExtn.group(1)
        fileExtnRegex = re.compile('^' + args.extn + '$')
        m = fileExtnRegex.match(fileExtn)
        if not m:
            print("Image {} is has extension {} which does not match the pattern {}. Change the --extn argument if this is not correct".format(image, fileExtn, args.extn))
            return False
        else:
            return True
    else:
        print("Image {} does not match the pattern {}. Change the --extn argument if this is not correct".format(image, args.extn))
        return False




def download_images(url, args):
    # Check if it's an album
    # NOTE: This no longer work as this isn't how Imgur handles albums
    #       Ideally it should be handled through the Imgur API, but the 
    #       Python library for this is now unsupported as Imgur wants 
    #       users to use OAuth2 and their API.
    #       There is a hack around this which will work, but I haven't 
    #       implemented it yet
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

        image_url, image = parseImgurURL(url, args)
        
        if not image_url:
            #print("Image url {} could not be properly parsed.".format(url, image))
            with open('notparsed.txt', 'a') as f1:
                f1.write("{}\n".format(url))
            return
        
        if not os.path.exists(args.output):
            os.makedirs(args.output)
            
        if not isCorrectExtension(image, args):
            return
            
        p = os.path.join(args.output, image)
        
        if(os.path.isfile(p)):
           #print("File {} exists, skipping.".format(p))
           return
        
        if(args.output2):
            p2 = os.path.join(args.output2, image)
            if(os.path.isfile(p2)):
                #print("File {} exists, skipping.".format(p2))
                return
               
       
       # if not args.quiet:
       #     print("Downloading image {} to {}".format(image_url, p))

        imageRequest = requests.get(image_url)
        imageData = imageRequest.content
       
        im = Image.open(BytesIO(imageData))
        w, h = im.size
        im.close()
        if not (w == 161 and h == 81): # this is the imgur image not found jpg
            with open(p, 'wb') as fobj:
                fobj.write(imageData)

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Credit goes to:
        User Greenstick (https://stackoverflow.com/users/2206251/greenstick) for this answer
        https://stackoverflow.com/a/34325723/3746992
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()


def redditor_retrieve(r, args):
    user = r.redditor(args.username)
    method = getattr(user, "sumissions().{}".format(args.sort))
    gen = method(limit=args.limit)

    links = get_urls(gen, args)
    for link in links:
        download_images(link, args)


def subreddit_retrieve(r, args):
    print(args.subreddit)
    subreddits = args.subreddit.split(',')
    for sub in subreddits:
        print("=======================\n")
        print("Subreddit: {}\n".format(sub))
        print("=======================\n")
        
        sub = r.subreddit(sub)
        method = getattr(sub, "{}".format(args.sort))
        gen = method(limit=args.limit)
        links = get_urls(gen, args)
        numLinks = len(links)
        printProgressBar(0, numLinks, prefix = 'Progress:', suffix = 'Complete', length = 50)

        for l, link in enumerate(links):
            printProgressBar(l + 1, numLinks, prefix = 'Progress:', suffix = 'Complete', length = 50)
            download_images(link, args)


def post_retrieve(r, args):
    submission_id = ""

    p = re.compile(r"(?:https?\:\/\/)?(?:www\.)?reddit.com\/r\/(?P<sub>\w+)\/comments\/(?P<id>\w+).+")
    m = p.match(args.post)

    if m:
        submission_id = m.group("id")
    else:
        p = re.compile(r"(?:https?\:\/\/)?redd\.it\/(?P<id>\w+)")
        m = p.match(args.post)
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

def read_subreddit_list_file(args):
    fname = args.subreddit_list_file
    
    with open(fname) as f:
        content = f.readlines()
        
    content = [line.rstrip('\n') for line in content]
        
    return ",".join(content)

def read_config_file(args):
    fname = args.config
    
    with open(fname) as f:
        content = f.readlines()
        
    content = [line.rstrip('\n') for line in content]
    content = ['--' + line for line in content]     
    return content



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
    parser.add_argument("--config", help="Configuration file which contains any valid command line arguments.",
                        metavar="cfg_file")
    parser.add_argument("--username", help="username to scrap and download from", metavar="user")
    parser.add_argument("--subreddit", help="subreddit(s) to scrap and download from", metavar="sub")
    parser.add_argument("--subreddit_list_file", help="A text file containing subreddit(s) to scrap and download from", 
                        metavar="sub_list_file")
    parser.add_argument("--post", help="post to scrap and download from", metavar="url")

    parser.add_argument("--sort", help="choose the sort order for submissions (default: new)",
                        choices=["hot", "new", "controversial", "top"], metavar="type", default="new")

    parser.add_argument("--limit", type=int, help="number of submissions to look for (default: 100)",
                        default=100, metavar="num")
    
    parser.add_argument("--extn", help="a | delimited list of file extensions, e.g. jpg|gif", metavar="extn",
                        default = "jpg|jpeg|png|gif")

    parser.add_argument("-q", "--quiet", action="store_true", help="doesn't print image download progress")
    parser.add_argument("-o", "--output", help="where to output the downloaded images", metavar="", default=".")
    parser.add_argument("-o2", "--output2", help="A second location to check file hasn't already been download", metavar="")
    parser.add_argument("--no-nsfw", action="store_true", help="only downloads images not marked nsfw")

    parser.add_argument("--score", help="minimum score of the image to download (default: 1)", type=int,
                        metavar="num", default=1)

    parser.add_argument("-l", "--length", help="skips album downloads over this length (default: 30)", type=int,
                        default=30, metavar="num")

    args = parser.parse_args()
    
    if args.config:
        newArgs = read_config_file(args)
        args = parser.parse_args(newArgs)
    

    if args.username:
        redditor_retrieve(r, args)

    if args.subreddit:
        subreddit_retrieve(r, args)
        
    if args.subreddit_list_file:
        args.subreddit = read_subreddit_list_file(args)
        subreddit_retrieve(r, args)

    if args.post:
        post_retrieve(r, args)
        
        
