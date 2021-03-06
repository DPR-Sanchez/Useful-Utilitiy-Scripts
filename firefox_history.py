import os
import re
import sqlite3

import pandas as pd
import requests

from datetime import datetime


def parse(history_row, lyrics_test, song_or_music_test, artist_album_or_genre_test):
    url, count, title, visit_date = history_row

    title = title.replace('- YouTube', '')

    if "YouTube" not in title:
        try:
            page_text = requests.get(url).text

            lyrics = lyrics_test.search(page_text)
            song_or_music = song_or_music_test.search(page_text)

            if lyrics or song_or_music:
                second_layer = lyrics == 1
                if not second_layer:
                    artist_album_or_genre = artist_album_or_genre_test.search(page_text)
                    second_layer = artist_album_or_genre is not None
                if second_layer:
                    try:
                        if visit_date < parse.min_date:
                            parse.min_date = visit_date
                        if visit_date > parse.max_date:
                            parse.max_date = visit_date
                    except Exception as e:
                        parse.min_date = visit_date
                        parse.max_date = visit_date

                    return [count, title.replace(',', ' '), url]

        except Exception as e:
            print(e)


def fetch_prior_list(file_name):
    df = pd.read_excel(file_name)
    second_column = (x.strip() for x in df.iloc[:, 1].values.tolist() if type(x) == str)
    return second_column


def fetch_YT(view_count_threshold, output_file_name):
    app_data = os.getenv('APPDATA')
    firefox_relative_path = r'\Mozilla\Firefox\Profiles'
    firefox_profile_folder = f'{app_data}{firefox_relative_path}'

    for file in os.listdir(firefox_profile_folder):
        if file.__contains__('.default-release'):
            data_path = f'{firefox_profile_folder}\\{file}'

    history_db = os.path.join(data_path, 'places.sqlite')
    c = sqlite3.connect(history_db)
    cursor = c.cursor()
    select_statement = 'SELECT moz_places.url, moz_places.visit_count, moz_places.title, moz_historyvisits.visit_date ' \
                       'FROM moz_places' \
                       ' LEFT JOIN moz_historyvisits' \
                       ' ON moz_places.id = moz_historyvisits.place_id ;'
    cursor.execute(select_statement)
    firefox_history = cursor.fetchall()

    youtube_test = re.compile('(?i)youtube.com')
    watch_test = re.compile('(?i)watch')

    firefox_filtered_history = (row for row in firefox_history
                                if youtube_test.search(row[0])
                                and watch_test.search(row[0])
                                and int(row[1]) >= view_count_threshold)

    firefox_filtered_history = sorted(firefox_filtered_history, reverse=True, key=lambda x: x[1])

    print('History count:', len(firefox_filtered_history))

    try:
        # Path should be the location that prior sheets generated by this script are kept
        prior_path = os.path.abspath(f'C:\\Users\\{os.getlogin()}\\Documents\\foxhistory\\prior')
        files = (entry.path for entry in os.scandir(prior_path) if entry.is_file())
    except Exception as e:
        print(e)

    prior_material = []
    for prior_list in files:
        prior_material.extend(fetch_prior_list(prior_list))

    material = {}

    # compiles regex used in parse() here to avoid compiling multiple times within the for loop
    lyrics_test = re.compile('(?i)Lyrics')
    song_or_music_test = re.compile('(?i)Song|Music')
    artist_album_or_genre_test = re.compile('(?i)Artist|Album|Genre')

    for elem in firefox_filtered_history:
        row = parse(elem, lyrics_test, song_or_music_test, artist_album_or_genre_test)
        if row is not None:
            if material.get(row[1], 0) != 0:
                material[row[1].strip()][0] += row[0]
            else:
                material[row[1].strip()] = [row[0], row[1].strip(), row[2]]

    print(f'material length pre pop: {len(material)}')
    for name in prior_material:
        if material.get(name, 0) != 0:
            material.pop(name)

    print(f'material length post pop: {len(material)}')

    material = sorted(list(material.values()), reverse=True, key=lambda x: x[0])

    print(f'\nfinal result count: {len(material)}\n')

    if len(material) > 0:
        content = []
        for elem in material:
            content.append((elem[0], elem[1], elem[2]))

        df = pd.DataFrame(content, columns=['Count', 'Title', 'URL'])

        print(parse.min_date / 1e6)
        min_date = str(datetime.fromtimestamp(parse.min_date / 1e6))[:10]
        max_date = str(datetime.fromtimestamp(parse.max_date / 1e6))[:10]
        print(min_date, max_date)
        current_path = os.path.abspath(f'C:\\Users\\{os.getlogin()}\\Documents\\foxhistory\\current')
        df.to_excel(f'{current_path}\\{output_file_name}_from_{min_date}_to_{max_date}.xlsx')


if __name__ == '__main__':
    try:
        view_count_threshold = 2
        location = 'home'
        year = '2020'
        document_title = f'YT_{view_count_threshold}plus_{location}_{year}'
        fetch_YT(view_count_threshold, document_title)
    except Exception as e:
        print(e)
