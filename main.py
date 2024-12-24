
import os
import googleapiclient.discovery
import pandas as pd
from pytube import YouTube
from googleapiclient.errors import HttpError

# Step 1: Setup YouTube API
API_KEY = "Enter api Key"  # Replace with your YouTube API Key

# Initialize the YouTube API client
def get_youtube_client():
    return googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

# Step 2: Fetch Videos for a Genre(releted to category)
def fetch_videos(genre, max_results=500):
    youtube = get_youtube_client()
    video_list = []
    next_page_token = None

    while len(video_list) < max_results:
        try:
            request = youtube.search().list(
                part="id,snippet",
                type="video",
                q=genre,
                maxResults=min(max_results - len(video_list), 50),
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get("items", []):
                video_list.append({
                    "Video ID": item["id"]["videoId"],
                    "Title": item["snippet"]["title"],
                    "Description": item["snippet"].get("description", ""),
                    "Channel Title": item["snippet"].get("channelTitle", ""),
                    "Published At": item["snippet"].get("publishedAt", ""),
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            print(f"An error occurred: {e}")
            break

    return video_list

# Step 3: Fetch Additional Video Details
def fetch_video_details(video_ids):
    youtube = get_youtube_client()
    details = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids[i:i+50])
        )
        response = request.execute()

        for item in response.get("items", []):
            details.append({
                "Video ID": item["id"],
                "Tags": item["snippet"].get("tags", []),
                "Category": item["snippet"].get("categoryId", ""),
                "Duration": item["contentDetails"].get("duration", ""),
                "View Count": item["statistics"].get("viewCount", 0),
                "Comment Count": item["statistics"].get("commentCount", 0),
                "Captions Available": "true" if "caption" in item["contentDetails"] else "false"
            })
    return details

# Step 4: Download Captions
def download_captions(video_id):
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        captions = yt.captions.get_by_language_code('')
        if captions:
            return captions.generate_srt_captions()
        else:
            return ""
    except Exception as e:
        print(f"Error fetching captions for {video_id}: {e}")
        return ""

# Step 5: Combine Data and Save to CSV
def save_to_csv(data, filename="youtube_data.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

# Main Execution
def main():
    genre = input("Enter the genre to search for: ")
    print("Fetching video data...")
    videos = fetch_videos(genre)

    video_ids = [video["Video ID"] for video in videos]
    print("Fetching additional video details...")
    details = fetch_video_details(video_ids)

    # Merge video data with details
    for video in videos:
        for detail in details:
            if video["Video ID"] == detail["Video ID"]:
                video.update(detail)
                video["Caption Text"] = download_captions(video["Video ID"]) if detail["Captions Available"] == "true" else ""

    print("Saving data to CSV...")
    save_to_csv(videos)
    print("Data saved successfully!")

if __name__ == "__main__":
    main()
