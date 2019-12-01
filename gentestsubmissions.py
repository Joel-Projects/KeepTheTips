import praw, datetime, psycopg2, time
from BotUtils.CommonUtils import BotServices

dryrun = False

services = BotServices('personalBot')

reddit = services.reddit('Lil_SpazBot')

sub = reddit.subreddit('LifeProTips')
testsub = reddit.subreddit('LifeProBotTest')
for i, submission in enumerate(sub.new()):
    if i < 25:
        subm = testsub.submit(submission.title, url=submission.url)
        print(subm.id)
    else:
        exit()