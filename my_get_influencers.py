import tweepy  # Twitter API helper package
from tweepy import OAuthHandler
import pprint # to print human readable dictionary
import json

from application.Connections import Connection

consumer_key = "utTM4qfuhmzeLUxRkBb1xb12P"  # API key
consumer_secret = "XteCQjAZCVAu7Tk5ftgcjv0jJlII2o7b8BqZc3sfEdwn1R6Ic7"  # API secret
access_token = "821415961467228161-iB85g0Lm8c4jLqIqxWcryWjE8nm6CPq"
access_secret = "BrNaqN0BP2K3rYzIurlaTIaJeOk4MBP6mzBtR73ay5ulU"

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)



# Fetches and saves the influencers of a specific topic to MongoDB
def get_influencers(topicID):
	with Connection.Instance().get_cursor() as cur:
		sql = (
			"SELECT topic_name, keywords "
			"FROM topics "
			"WHERE topic_id= " + str(topicID)
		)
		cur.execute(sql)
		topic = cur.fetchall()

		influencers=dict()
		key_field = 'id_str'
		keywords = topic[0][1]
		topic_name = topic[0][0]

		for keyword in keywords.split(','):
			print("Retrieving for keyword: " + str(keyword.strip()))

			for influencer in api.search_users(q=keyword.strip()): # !!!: retrieves 20 influencers per request (first page only)
				# get influencer from Twitter
				influencer_dict = influencer._json
				# check if he already exists in the database
				inf = Connection.Instance().influencerDB.all_influencers.find_one({ 'id_str': str(influencer_dict['id_str']) })
				# if he exists,
				if (inf!=None):  #update his topics list
					if(topicID not in inf['topics']):
						Connection.Instance().influencerDB.all_influencers.update(
   							{ 'id_str': inf['id_str'] },
   							{ '$addToSet':{'topics': topicID}} # add current topic to his topics list
						)

					pprint.pprint("influencer already in the list: " + inf['screen_name'])
				else: # if not, add him to the collection
					influencer_dict['topics']= [topicID]
					Connection.Instance().influencerDB['all_influencers'].insert_one(influencer_dict)

		print("Influencers of topic: " + topic_name + " found and inserted into database.")

# FETCH AND SAVE INFLUENCERS OF ALL TOPICS IN THE POSTGRE DATABASE
with Connection.Instance().get_cursor() as cur:
	sql = (
		"SELECT topic_id "
		"FROM topics "
	)
	cur.execute(sql)
	topics = cur.fetchall() # list of all topics

	for topic in topics:
		Connection.Instance().influencerDB[str(topic[0])].drop()
		get_influencers(topic[0]) # topic[0] is the topic id

	# GENERATE TOPIC-INFLUENCER COLLECTIONS
	count=1
	insertcount=1
	for influencer in Connection.Instance().influencerDB.all_influencers.find({}):
		print("influencer # "+ str(count) + " topics: " + str(influencer['topics']))
		count+=1
		for topicID in influencer['topics']:
			inf = Connection.Instance().influencerDB[str(topicID)].find_one({ 'id_str': str(influencer['id_str']) })
			if(inf==None):
				if ('topics' in influencer): del influencer['topics'] # get rid of topics list - we do not need it in topic-influencer collections
				Connection.Instance().influencerDB[str(topicID)].insert_one(influencer)
				print(insertcount)
				insertcount+=1