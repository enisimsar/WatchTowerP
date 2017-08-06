from newspaper import Article
from application.Connections import Connection
from application.ThreadPool import ThreadPool
import application.utils.location.get_locations as get_location
import application.utils.dateExtractor as dateExtractor
from requests import head
from time import gmtime, strftime, time, sleep
from urllib.parse import urlparse
from tldextract import extract
import timeout_decorator
from re import search, IGNORECASE
import sys, time
from tldextract import extract
from rq import Queue
from redis import Redis
import json

def get_next_links_sequence():
    cursor = Connection.Instance().newsPoolDB["counters"].find_and_modify(
            query= { '_id': "link_id" },
            update= { '$inc': { 'seq': 1 } },
            new= True,
            upsert= True
    )
    return cursor['seq']

def unshorten_url(url):
    return head(url, allow_redirects=True).url

def linkParser(link):
    parsed_uri = urlparse(link)
    source = '{uri.netloc}'.format(uri=parsed_uri)
    domain = extract(link).domain
    article = Article(link)
    article.build()
    image = article.top_image
    keywords = article.keywords
    description = article.summary
    title = article.title

    try:
        published_at = dateExtractor.extractArticlePublishedDate(link)
    except Exception as e:
        published_at = None
        print(e)
        print("\n\n\n")
        pass

    try:
        language = article.meta_lang
    except:
        language = None
        pass

    try:
        author = article.authors
    except:
        author = None
        pass

    places = get_location.get_place_context(text=description)

    location = {
        "countries": places.countries,
        "country_mentions" : places.country_mentions,
        "cities" : places.cities,
        "city_mentions" : places.city_mentions
    }

    if image != "" and description != "" and title != "":
        dic = {'url': link, 'im':image, 'title': title, 'domain': domain,\
        'description': description, 'keywords': keywords, 'source': source,\
        'published_at': published_at, 'language': language, 'location': location,\
        'author': author}
        print('done')
        return dic

def calculateLinks(data):
    alertid = data['alertid']
    tweet = data['tweet']
    print("processing...")
    alertid = int(alertid)
    Connection.Instance().db[str(alertid)].find_one_and_update({'id_str':tweet['id_str'], 'isprocessed': {'$exists': True}, 'isprocessed': False}, {'$set': {'isprocessed': True}})
    try:
        lang = None
        location = None

        try:
            lang = tweet['user']['lang']
            location = tweet['user']['location']
        except:
            pass

        tweet_tuple = {'user_id': tweet['user']['id_str'], 'tweet_id': tweet['id_str'],\
         'timestamp_ms': int(tweet['timestamp_ms']), 'language': lang, 'location': location}
        for link in tweet['entities']['urls']:
            link = link['expanded_url']
            if link == None:
                continue
            try:
                link = unshorten_url(link)
                if len(list(Connection.Instance().newsPoolDB[str(alertid)].find({'url':link}))) != 0:
                    print("found in db")
                    Connection.Instance().newsPoolDB[str(alertid)].find_one_and_update({'url': link}, {'$push': {'mentions': tweet_tuple}})
                    continue
                dic = linkParser(link)
                if dic != None:
                    if len(list(Connection.Instance().newsPoolDB[str(alertid)].find({'domain':dic['domain'], 'title':dic['title']}))) != 0:
                        Connection.Instance().newsPoolDB[str(alertid)]\
                        .find_one_and_update(\
                        {'source':dic['source'], 'title':dic['title']}, \
                        {'$push': {'mentions': tweet_tuple}, '$set': {'published_at': dic['published_at'], 'language': dic['language'], 'author': dic['author']}})
                    else:
                        dic['link_id'] = get_next_links_sequence()
                        dic['mentions']=[tweet_tuple]
                        dic['forbidden']=False
                        dic['bookmark']=False
                        dic['bookmark_date']=None
                        Connection.Instance().newsPoolDB[str(alertid)].insert_one(dic)
            except Exception as e:
                print(link)
                print(e)
                pass
    except Exception as e:
        print(e)
        pass

def createParameters(alertid, tweets):
    return [[alertid,tweet] for tweet in tweets]


if __name__ == '__main__':
    d = linkParser("https://semiengineering.com/iot-myth-busting/")
    print(d['published_at'])
