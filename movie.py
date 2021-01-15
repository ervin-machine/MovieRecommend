import tweepy
import pandas as pd
import os
from flask import Flask, render_template, request
from ibm_watson import PersonalityInsightsV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import sys
import logging

app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
# Creds for Personality Insights
# 1 Twitter Person insight
apikey = '5YJ2mr2pIG4-GwDsPlgFm-hA9zSLYiArXhcLVfKTi2kI'
url = 'https://api.us-south.personality-insights.watson.cloud.ibm.com/instances/464d9d72-e60e-4206-af88-a14403acaa4a'



# Authenticate to Twitter
auth = tweepy.OAuthHandler("dRhbHdiqmAdiYv3beQQIkrvJa",
    "d4UDwWsmZbNFCr8ZyJMBBDZB2wEpMvzRSyO3Qr11g3GsS4QvPy")
auth.set_access_token("23929565-SkWIfSILv0bfgG7xxHvKzvswST1EEYl47A6GrCRc0",
    "Efp3iKHQJxSDXDxVRJISrGO9paR0XfDSv66L5fLBjqlfw")

# Instantiate API
api = tweepy.API(auth, wait_on_rate_limit=True)



@app.route('/', methods = ['GET', 'POST'])
def result():
   if request.method == 'GET':
       return render_template('twitter.html')

   if request.method == 'POST':

      handle = request.form['name']
      print(handle)
      res = api.user_timeline(screen_name=handle, count=200)
      tweets = [[tweet.text] for tweet in res]
      text = ''.join(str(tweet) for tweet in tweets)

      authenticator = IAMAuthenticator(apikey)
      personality_insights = PersonalityInsightsV3(
              version='2017-10-13',
              authenticator=authenticator
      )
      personality_insights.set_service_url(url)


      profile = personality_insights.profile(text, accept='application/json').get_result()
      givPersonality = []
      for personality in profile['personality']:
          givPersonality.append(personality['percentile']*5)

      user = np.array(givPersonality)
      user = np.round(user, 2)

      #-----------------END OF TWITTER PERSON INSIGHT


      #-----------------GENRES 5-FIVE
      df1 = pd.read_csv("data.csv")
      #-----------------END OF GENRES


      #-----------------Personal Score Calculation
      Ope = df1["ope"] - user[0]
      Con = df1["con"] - user[1]
      Ext = df1["ext"] - user[2]
      Agr = df1["agr"] - user[3]
      Neu = df1["neu"] - user[4]

      Personalscore = Ope + Con + Ext + Agr + Neu
      Moviescore = df1["ope"] + df1["con"] + df1["ext"] + df1["agr"] + df1["neu"]
      ms = Moviescore.mean()
      ps = Personalscore.mean()

      #-----------------END OF PERSONAL SCORE


      #-----------------MOVIE DATASET


      df = pd.read_csv("moviedata.csv")
      df['ps'] = ps


      C = df['ps'].mean()

      #genre = input("Input a genre: ")

      m = df['vote_average'].quantile(0.90)


      q_movies = df.copy().loc[df['vote_average'] >= m]
      def weighted_rating(x, m=m, C=C):
          v = x['vote_average']
          R = x['ps']

          return (v/(v+m) * R) + (m/(m+v) * C)

      q_movies['score'] = q_movies.apply(weighted_rating, axis=1)
      q_movies = q_movies.sort_values('score', ascending=True)

      #Print the top 15 movies
      print(q_movies[['title']].head(20))
      movies = np.array(q_movies[['title', 'poster_path']].head(20))
      #movies1 = np.array(q_movies.loc[q_movies['genres'] == data1][['title', 'genres']].head(20))
      #stocklist = list(movies.flatten())
      #print(movies)
      return render_template("result.html",movies=movies, result = handle, personality = user)






if __name__ == '__main__':
    app.debug = True
    app.run()
