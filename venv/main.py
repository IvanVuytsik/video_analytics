from googleapiclient.discovery import build
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pprint import pprint

#Google YouTube Data API documentation:
# https://developers.google.com/youtube/v3

api_key = None #add your unique YouTube Key
#channel_id = 'UCpVhp2_0xzV7BrLHzprIcbg'
channel_ids = ['UClu56Ik6ewp3JRBXDhyTFoQ',
              'UCvU7fItEZq-WzOXm41P0AXg',
              'UCGTi2CzrMIO7jR-ZjeN4WSQ',
              'UCW5AiPkbW1uas4AVh2RgO-Q',
              'UCpVhp2_0xzV7BrLHzprIcbg']

youtube = build('youtube', 'v3', developerKey=api_key)

def get_channel_stats(youtube, channel_ids):
    all_data = []
    request = youtube.channels().list(part='snippet, contentDetails, statistics',
                                      id=','.join(channel_ids))
    response = request.execute()
    #https://jsonformatter.curiousconcept.com/#
    for i in range(len(response['items'])):
        data = dict(Channel_name=response['items'][i]['snippet']['title'],
                    Subscribers=response['items'][i]['statistics']['subscriberCount'],
                    Views=response['items'][i]['statistics']['viewCount'],
                    Total_videos=response['items'][i]['statistics']['videoCount'],
                    Playlist_id=response['items'][i]['contentDetails']['relatedPlaylists']['uploads'],
                    )

        all_data.append(data)

    return all_data


channel_statistics = get_channel_stats(youtube, channel_ids)

#chane data type from object
channel_data = pd.DataFrame(channel_statistics)
channel_data['Subscribers'] = pd.to_numeric(channel_data['Subscribers'])
channel_data['Views'] = pd.to_numeric(channel_data['Views'])
channel_data['Total_videos'] = pd.to_numeric(channel_data['Total_videos'])

sns.set(rc={'figure.figsize':(10,8)})
# ax = sns.barplot(x='Channel_name', y='Subscribers', data=channel_data)
# print(channel_data.dtypes)
# print(channel_data)

playlist_id = channel_data.loc[channel_data['Channel_name']=='Guitars & Dragons', 'Playlist_id'].iloc[0]
#print(playlist_id)


#---------------------------------------------------
def get_vid_ids(youtube, playlist_id):
    #https://developers.google.com/youtube/v3/docs/playlists
    request = youtube.playlistItems().list(part='contentDetails',
                                           playlistId=playlist_id,
                                           maxResults=5)
    response = request.execute()

    video_ids = []
    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    more_pages = True

    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(part='contentDetails',
                                                   playlistId=playlist_id,
                                                   maxResults=10,
                                                   pageToken = next_page_token)
            response = request.execute()
            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')

    # print(video_ids)
    # print(len(video_ids))

    return (video_ids)

video_ids = get_vid_ids(youtube, playlist_id)
#---------------------------------------------------
def get_vid_details(youtube, video_ids):
    all_video_stats = []

    for i in range(0, len(video_ids), 50): #50 at a time
        request = youtube.videos().list(part='snippet,statistics',
                                        id=','.join(video_ids[i:i+50])) # limit by youtube / list to str
        response = request.execute()

        for vid in response['items']:
            video_stats = dict(Title=vid['snippet']['title'],
                               PublishedDate=vid['snippet']['publishedAt'],
                               Views=vid['statistics']['viewCount'],
                               Likes=vid['statistics']['likeCount'],
                               Comments=vid['statistics']['commentCount'])
            all_video_stats.append(video_stats)

    #pprint(all_video_stats)
    return all_video_stats

video_details = get_vid_details(youtube, video_ids)
#-------------------------------------------------
video_data = pd.DataFrame(video_details)
video_data['PublishedDate'] = pd.to_datetime(video_data['PublishedDate']).dt.date
video_data['Views'] = pd.to_numeric(video_data['Views'])
video_data['Likes'] = pd.to_numeric(video_data['Likes'])
video_data['Comments'] = pd.to_numeric(video_data['Comments'])

top_10 = video_data.sort_values(by="Views", ascending=False).head(10)
#print(top_10)

# ax1 = sns.barplot(x="Views", y='Title', data=top_10)


#------------------------------
video_data['Month'] = pd.to_datetime(video_data['PublishedDate']).dt.strftime('%b')
videos_per_month = video_data.groupby('Month', as_index=False).size()


sort_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
videos_per_month.index = pd.CategoricalIndex(videos_per_month['Month'],categories=sort_order, ordered=True)
videos_per_month = videos_per_month.sort_index()
# pprint(videos_per_month)

ax2 = sns.barplot(x="Month", y='size', data=videos_per_month)
plt.show()

video_data.to_csv('.\Video_Details(Guitars & Dragons).csv')