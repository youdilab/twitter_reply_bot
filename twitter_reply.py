#Tweepy is the Python library used for accessing Twitter API
import tweepy
import config as config
import json
import re

#Parameter used to set how many tweets mentioning the bot name are fetched in a single iteration
#Minimum=> 1, Maximum 20
TWEETS_PER_CALL = config.TWEETS_PER_CALL

#File where the id of the last looked up mentioned tweet is stored.
METADATA_FILE_PATH = config.METADATA_FILE_PATH

#Value to be used as id of the last looked up mentioned tweet in case unable to read metadata file
LOWER_LIMIT_TWEET = config.LOWER_LIMIT_TWEET

#Regular expression to see if the bot is tagged properly.
TAG_REGEX = config.TAG_REGEX

#Twitter API Credentials are stored in the config file.
#API_KEY = '<api_key>'
#SECRET_KEY = '<secret_key>'
#BEARER_TOKEN = '<bearer_token>'
#ACCESS_TOKEN = '<access_token>'
#SECRET_TOKEN = '<secret_token>'

#App Level
client = tweepy.Client(bearer_token=config.BEARER_TOKEN)

#User Level
auth = tweepy.OAuthHandler(config.API_KEY, config.SECRET_KEY)
auth.set_access_token(config.ACCESS_TOKEN, config.SECRET_TOKEN)
api = tweepy.API(auth)

#Function to read saved id of the last tweet the bot was mentioned in
def read_last_mention_id(file_path):
    try:
        f = open(file_path, "r")
        file_content = f.read()
        data = json.loads(file_content)
        lower_limit_id = data["last_max_tweet_id"]
        f.close()
    except:
        lower_limit_id = LOWER_LIMIT_TWEET
    
    return lower_limit_id

#Function to update saved id of the last tweet the bot was mentioned in
def update_latest_mention_id(file_path,max_limit_id):
    
    #Empty dictionary to hold data
    data={}
    
    try:
        f = open(file_path, "w")
        data["last_max_tweet_id"] = max_limit_id
        json.dump(data, f)
        f.close()
        return True
    except:
        return False

#Function to tweet the reply
def tweet_reply(mention_user, mention_id_str, reply_text):
    try:
        api.update_status(status = '@'+mention_user+' '+reply_text, in_reply_to_status_id = mention_id_str)
        return True
    except Exception as exception:
        print('Error occurred '+str(exception.__class__.__name__))
        return False

#Function to check for mentions and reply to them
def reply_to_mentions():
    #Initialization of loop parameters
    upper_limit_id = None
    lower_limit_id = read_last_mention_id(METADATA_FILE_PATH)
    mention_ids = []

    while (True):
        mentions = api.mentions_timeline(count = TWEETS_PER_CALL,since_id = lower_limit_id, max_id = upper_limit_id,trim_user=False)
        
        #Exit the loop if there are no mentions
        if (len(mentions)<1):
            print('No further mentioned tweets found.')
            break
        
        #Reply to each individual mention
        for mention in mentions:
            mention_ids.append(mention.id)

            #Check if the mention is posted by the bot itself
            if(mention.user.id==BOT_TWITTER_ID):
                print('Avoding responding to bot\'s own tweet')
                continue
            
            #Check if the bot has been tagged properly
            if(not re.search(config.TAG_REGEX, mention.text)):
                print('Filtering out untagged tweets.')
                continue

            #Print currently iterating tweet content just to monitor.
            print(mention.id)#Tweet Id
            print(mention.text)#Tweet Text
            print(mention.created_at)#Tweet Created Date


            #If the bot name is mentioned in a reply tweet
            if(mention.in_reply_to_status_id):
                original = api.lookup_statuses(id=[mention.in_reply_to_status_id])
                price_get_date = original[0].created_at
            #If the bot name is mentioned in an original tweet
            else:
                price_get_date = mention.created_at

            #Fetch the appropriate response
            #reply_to_mention = get_reply_format(price_get_date)
            reply_to_mention = 'Temporary Response'+str(mention.created_at)#debug

            #Tweet the reply
            tweet_reply(mention_user, mention_id_str, reply_text)

            #Update the latest tweet id to be considered
            upper_limit_id = min(mention_ids)-1

        #Update the upper tweet id limit at the end of API call invokation
        if (len(mention_ids)<1):
            max_limit_id = lower_limit_id
        else:
            max_limit_id = max(mention_ids)+1

        update_latest_mention_id(METADATA_FILE_PATH,max_limit_id)

#Main entry point
reply_to_mentions()