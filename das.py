import os
import json
import mimetypes
import shutil
from datetime import datetime
from tqdm import tqdm
from requests_html import HTMLSession


def get_videos():
    session = HTMLSession()

    r = session.get("https://www.destroyallsoftware.com/screencasts/catalog")

    seasons = 0
    episodes = 0

    if not os.path.exists("videos"):
        os.mkdir("videos")

    for season in r.html.find(".season"):
        seasons += 1
        name = season.find(".season_title a", first=True).attrs["name"]
        description = season.find(".description p", first=True)
        description = description.text if description else ""

        season_directory = "videos/{}/".format("-".join(name.split(" "))).lower()

        if not os.path.exists(season_directory):
            os.mkdir(season_directory)

        for episode in season.find(".episode"):
            start = datetime.now()
            episodes += 1
            a = episode.find("a", first=True)
            detail_link = "https://www.destroyallsoftware.com{}".format(a.attrs["href"])

            row = a.find(".row", first=True)

            number = row.find(".number", first=True).text
            title = row.find(".title", first=True).text
            subtitle = row.find(".subtitle", first=True).text
            duration = row.find(".duration", first=True).text
            print("Starting: {} - {} - {}".format(number, title, subtitle))

            filename = title.replace(" ", "-").replace("/", "-").lower()
            file_path = os.path.join(season_directory, filename)

            meta_file = "{}.json".format(file_path)

            if os.path.exists(meta_file):
                print("Found {} skipping....".format(file_path))
                continue

            detail = session.get(detail_link)
            detail.html.render()

            video_link = detail.html.find(".container video source", first=True).attrs["src"]
            video_link = "https://www.destroyallsoftware.com{}".format(video_link)

            fr = session.get(video_link, stream=True)

            total_length = fr.headers["Content-Length"]

            mime = fr.headers["Content-Type"]
            local_filename = "{}{}".format(file_path, mimetypes.guess_extension(mime))

            part_filename = "{}.part".format(local_filename)

            chunk_size = 1024 * 256

            total_size_mb = int(total_length) / (1024 * 1024)

            pbar = tqdm(total=total_size_mb)

            with open(part_filename, 'wb') as f:
                for chunk in fr.iter_content(chunk_size=chunk_size):
                    if chunk:
                        pbar.update(0.25)
                        f.write(chunk)

            print("Moving part file..")
            shutil.move(part_filename, local_filename)

            data = {
                "season": {"name": name, "description": description},
                "episode": {"number": number, "title": title, "subtitle": subtitle, "duration": duration},
                "file_path": file_path,
                "video_link": video_link,
                "local_filename": local_filename,
                "download_started": start.isoformat(),
                "download_finished": datetime.now().isoformat(),
            }

            with open(meta_file, "w") as jfi:
                jfi.write(json.dumps(data))

    print("Found {} seasons and {} episodes".format(seasons, episodes))


if __name__ == "__main__":
    get_videos()
