# Import Library
import PupperSource #header
import re, praw, requests, os, glob, sys, stat, facebook, uuid, logging #main libraries
from twython import Twython, TwythonError

debug = False
showTitle = False

twitter = PupperSource.getTwython()

# Logging setup
logging.basicConfig(format ='%(asctime)s [%(levelname)s] %(message)s', filename = '\Logs\DailyPuppers.log', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

# Bools for Social Media
facebookPost = False
twitterPost = True
	
#
# Post finding
#

# Define user agent and get /r/funny
imgurUrlPattern = re.compile(r'(http://i.imgur.com/(.*))(\?.*)?')
user_agent = ("PP 1.0")
r = praw.Reddit(user_agent = user_agent)
usablePost = False;

# Search /r/puppies first
subredditTarget = "puppies+puppysmiles+shiba+corgi"
subreddit = r.get_subreddit(subredditTarget)

# Scan subreddit until top post is found
for submission in subreddit.get_hot(limit = 200):

	if usablePost is True:
		break;

	# Store metadata
	score = submission.score
	url = submission.url
	title = submission.title
	name = str(submission.author)
	postID = str(submission.id)
	subredditTitle = str(submission.subreddit)
	
	if score > 50:
		if PupperSource.charCount(title + name) > 128:
			if debug: logging.info("Skipping post titled: %s, too many characters." % (title))
			continue
		
		if PupperSource.curseCheck(title) is True:
			if debug: logging.info("Skipping post titled: %s, invalid word found." % (title))
			continue
			
		if PupperSource.prevPost(postID) is True:
			if debug: logging.info("Skipping post ID: %s, already sent." % (postID))
			continue
		
		if 'gallery' in url:
			if debug: logging.info("Skipping post titled: %s, gallery." % (title))
			continue
			
		if 'topic' in url:
			if debug: logging.info("Skipping post titled: %s, topic." % (title))
			continue
			
		if 'gifv' in url:
			url = url.strip('gifv') + 'gif'
		
		# Skip non-imgur submissions
		if "imgur.com/" not in url:
			continue

		# Skip albums
		if 'http://imgur.com/a/' in url:
			continue
			
		# Skip gifs
		if 'gif' in url:
			continue

		# Direct image link
		elif 'http://i.imgur.com/' in url:
		
			# The URL is a direct link to the image.
			mo = imgurUrlPattern.search(url)

			imgurFilename = mo.group(2)
			if '?' in imgurFilename:
				imgurFilename = imgurFilename[:imgurFilename.find('?')]

			localFileName = "reddit_%s" % (submission.id)
			PupperSource.downloadImage(url, localFileName)
			
			if PupperSource.getFileSize(localFileName) > 5000000:
				os.remove(localFileName)
				continue
			else:
				usablePost = True;
				logging.info("Usable post found.")
				break
		
		# Imgur page link		
		elif 'http://imgur.com/' in url:
			url = PupperSource.fixLink(url)
			mo = imgurUrlPattern.search(url)

			imgurFilename = mo.group(2)
			if '?' in imgurFilename:
				imgurFilename = imgurFilename[:imgurFilename.find('?')]

			localFileName = "reddit_%s" % (submission.id)
			PupperSource.downloadImage(url, localFileName)
			
			if PupperSource.getFileSize(localFileName) > 5000000:
				os.remove(localFileName)
				continue
			else:
				usablePost = True;
				logging.info("Usable post found.")
				break
		else:
			continue
try:
	localFileName
except NameError:
	logging.info("Either all available posts have been sent, or no top posts meet criteria.")
	sys.exit()
else:
	if showTitle:
		pupTitle = PupperSource.getTitle()
	else:
		pupTitle = ""

	# Submission info block
	logging.info("Post Information")
	logging.info("---------------------")
	logging.info("Original title: " + title)
	logging.info("Sent title: " + pupTitle)
	logging.info("Subreddit: " + subredditTitle)
	logging.info("URL: " + url)
	logging.info("---------------------\n")

	if facebookPost or twitterPost:

		# Remove words from title
		tempTitle = title
		removeWords = ['[OC]', '[oc]']
		testWords = tempTitle.split()
		resultWords = [word for word in testWords if word.lower() not in removeWords]
		title = ' '.join(resultWords)

		# Remove excess punctuation 
		fbPostText = PupperSource.formatPost(title,name)
		tweetText = PupperSource.formatPost(title,0)
		
		logging.info("Attempting to send to social media...")

		# File operations

		# Post to Social Media if enabled
		if twitterPost:
			try:
				photo = open(str(localFileName),'rb')
				image_ids = twitter.upload_media(media = photo)
				twitter.update_status(status = pupTitle, media_ids = image_ids['media_id'])
			except TwythonError as e:
				logging.error("Twitter posting failed.")
				logging.error(e)
			else:
				logging.info("Twitter posting successful.\n")
				PupperSource.recordPost(postID)
		else:
			logging.info("Twitter posting disabled, skipping.")
		if facebookPost:
			try:
				logging.info("Attempting to post to Facebook...")
				graph = facebook.GraphAPI(access_token = fbToken)
				photo = open(str(localFileName),'rb')
				graph.put_photo(image=photo, message=fbPostText)
			except:
				logging.error("Facebook posting failed.")
			else:
				logging.info("Facebook posting successful.\n")
				# Log postID so that it cannot be reposted
				PupperSource.recordPost(postID)
		else:
			logging.info("Facebook posting disabled, skipping.")
		
		# Delete image
		try:
			os.remove(localFileName)
		except:
			logging.error("Could not delete: %s" % (localFileName))
		else:
			logging.info("Image %s deleted." % (localFileName))

		sys.exit()
	else:
		logging.warning("No social media enabled.")
		try:
			os.remove(localFileName)
		except:
			logging.error("Could not deleted: %s" % (localFileName))
		else:
			logging.info("Image %s deleted." % (localFileName))
		sys.exit()