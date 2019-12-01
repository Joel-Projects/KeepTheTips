import praw, datetime, time, prawcore, sqlalchemy, sys
from multiprocessing import Process
from parameters import *
from math import floor
from models import Submission
# from praw.models.util import BoundedSet
debug = sys.platform == 'darwin'
if debug:
    import logging

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger('prawcore')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

dryrun = False

def submissionStream(botName, subreddit, redditKwargs):
    from BotUtils import BotServices
    services = BotServices(botName)
    log = services.logger()
    session = services.sqlalc()
    reddit = praw.Reddit(**redditKwargs)
    sub = reddit.subreddit(subreddit)
    stream = sub.new
    log.info('Submission Stream: Starting Submission Loop...')
    log.info('Submission Stream: Starting Submission Stream...')
    while True:
        alreadyProcessed = [i[0] for i in session.query(Submission.id).all()]
        try:
            for submission in stream():
                if submission:
                    try:
                        if getattr(submission.author, 'name', None) and not submission.removed and not submission.is_self and not submission.archived:
                            data = {
                                'id': submission.id,
                                'author': submission.author.name,
                                'submitted_timestamp': datetime.datetime.fromtimestamp(time.time()),
                                'submitted': time.time()
                            }
                            log.debug(data)
                            # if not submission.id in alreadyProcessed:
                            dbSubmission = Submission(**data)
                            session.add(dbSubmission)
                            session.commit()
                            log.info(f'Submission Stream: {submission.id} by u/{submission.author} submitted at {time.strftime("%b %d, %Y %I:%M:%S %p %Z", time.localtime(submission.created_utc))}')
                            if not dryrun:
                                reply = submission.reply(submissionComment)
                                reply.mod.distinguish(sticky=True)
                                reply.mod.lock()
                                dbSubmission.commentid = reply.id
                                session.commit()
                                alreadyProcessed.append(submission.id)
                    except sqlalchemy.exc.IntegrityError:
                        session.rollback()
                        pass
        except praw.exceptions.APIException as error:
            log.exception(error)
            log.info('Submission Stream: API Exception occured for 120 seconds...')
            time.sleep(120)
        except Exception as error:
            log.exception(error)
            log.info('Submission Stream: Sleeping for 120 seconds...')
            time.sleep(120)
        # time.sleep(1)

def commentChecker(botName, subreddit, redditKwargs):
    from BotUtils.CommonUtils import BotServices
    services = BotServices(botName)
    session = services.sqlalc()
    reddit = praw.Reddit(**redditKwargs)
    log = services.logger()
    log.info('Comment Checker: Starting Comment Checker...')
    log.info('Comment Checker: Checking comments...')
    i = time.time()
    while True:
        try:
            if (time.time() - i) >= 60:
                log.info('Comment Checker: Checking comments...')
                i = time.time()
            commentMaxAge = time.time() - commentAgeMax
            commentMinAge = time.time() - gracePeriod
            comments = session.query(Submission).filter(Submission.commentid.isnot(None), Submission.comment_removed == False, Submission.submission_removed == False, Submission.safe == False).all()
            for result in comments:
                commentid = result.commentid
                comment = reddit.comment(commentid)
                try:
                    comment._fetch()
                    if not comment.submission.removed:
                        if commentMinAge>comment.created_utc>commentMaxAge:
                            commentRemovalScore = floor(1.6**((((time.time() - comment.created_utc)/60)/60) - 1) - 20)+(comment.submission.score*submissionScoreRatio)
                            if comment.score < commentRemovalScore:
                                log.info(f'Comment Checker: Removal Score: {commentRemovalScore}, Actual Score: {comment.score} for {comment.id}')
                                comment.submission.mod.remove()
                                result.removed_timestamp = datetime.datetime.utcnow()
                                author = getattr(comment.submission.author, 'name', None)
                                if not author:
                                    comment.submission.author = result.author
                                    result.submission_removed = True
                                    log.info(f'Comment Checker: Marked submission {comment.submission.id} as removed, submission was deleted by u/{comment.submission.author}')
                                log.info(f'Comment Checker: Removed submission {comment.submission.id}')
                        else:
                            if comment.created_utc < commentMaxAge:
                                result.safe = True
                                log.info(f'Comment Checker: {comment.submission.id} marked as safe')
                            else:
                                continue
                    else:
                        if not comment.submission.banned_by == 'keepthetips':
                            result.submission_removed = True
                            log.info(f'Comment Checker: Marked submission {comment.submission.id} as removed. Post was removed by u/{comment.submission.banned_by}.')
                    session.commit()
                except prawcore.NotFound:
                    pass
                except Exception as error:
                    log.exception(error)
        except Exception as error:
            log.exception(error)
            log.info('Comment Checker: Sleeping for 120 seconds...')
            time.sleep(120)
        # time.sleep(1)

if __name__ == '__main__':
    from BotUtils.CommonUtils import BotServices
    botName = 'KeepTheTips'
    if sys.platform == 'darwin':
        from multiprocessing import set_start_method
        set_start_method('spawn')
    services = BotServices(botName)
    funcs = [submissionStream, commentChecker]
    redditApps = ['KeepTheTips_SubmissionStream', 'KeepTheTips_CommentChecker']
    redditKwargs = [BotServices(app).reddit(botname=app, redditUsername='keepthetips').config._settings for app in redditApps]
    processes = [Process(target=func, kwargs={'botName': botName, 'subreddit': 'LifeProTips', 'redditKwargs': redditKwargs[i]}) for i, func in enumerate(funcs)]
    # processes = [Process(target=func, kwargs={'botName': botName, 'subreddit': 'RoastMe', 'redditKwargs': redditKwargs}) for func in funcs]
    for process in processes:
        process.start()
    for process in processes:
        process.join()