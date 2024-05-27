from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os

app = Flask(__name__)

# Mapping of name variations to standardized names
name_mapping = {
    'Narine': 'Sunil Narine',
    'S Narine': 'Sunil Narine',
    'Russell': 'Andre Russell',
    'A Russell': 'Andre Russell',
    'Kohli': 'Virat Kohli'
    # Add more mappings as needed
}

DEFAULT_FRIEND = 'Unknown Friend'

# Load data from JSON files
def load_data(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return default

# Save data to JSON files
def save_data(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file)

friend_assignment = load_data('friend_assignments.json', {})
name_mapping.update(load_data('name_mappings.json', {}))
processed_urls = load_data('processed_urls.json', [])

def standardize_name(name):
    return name_mapping.get(name, name)

def scrape_batting_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    batting_table = soup.find_all('div', class_='cb-col cb-col-100 cb-scrd-itms')
    batting_data = []
    for row in batting_table:
        player_name = row.find('a').text.strip() if row.find('a') else ''
        runs = row.find_all('div', class_='cb-col cb-col-8 text-right text-bold')[0].text.strip() if row.find_all('div', class_='cb-col cb-col-8 text-right text-bold') else '0'
        if player_name:
            player_name = standardize_name(player_name)
            batting_data.append({
                'player_name': player_name,
                'runs': int(runs)
            })
    return batting_data

def scrape_bowling_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    bowling_table = soup.find_all('div', class_='cb-col cb-col-100 cb-scrd-itms')
    bowling_data = []
    for row in bowling_table:
        columns = row.find_all('div')
        if len(columns) > 5:
            player_name = standardize_name(columns[0].text.strip())
            wickets = int(columns[5].text.strip())
            bowling_data.append({
                'player_name': player_name,
                'wickets': wickets
            })
    return bowling_data

def standardize_dataframe(df):
    df['player_name'] = df['player_name'].apply(standardize_name)
    return df

def consolidate_duplicates(df):
    df = df.groupby(['player_name', 'friend_name'], as_index=False).agg({
        'runs': 'sum',
        'wickets': 'sum',
        'points': 'sum'
    })
    df['points'] = df['runs'] + 25 * df['wickets']
    return df

def update_excel_sheet():
    try:
        df = pd.read_excel('player_stats.xlsx')
    except FileNotFoundError:
        df = pd.DataFrame(columns=['player_name', 'runs', 'wickets', 'points', 'friend_name'])

    df = standardize_dataframe(df)
    for player_name, friend_name in friend_assignment.items():
        player_name = standardize_name(player_name)
        if player_name in df['player_name'].values:
            df.loc[df['player_name'] == player_name, 'friend_name'] = friend_name
        else:
            new_row = pd.DataFrame([{
                'player_name': player_name,
                'runs': 0,
                'wickets': 0,
                'points': 0,
                'friend_name': friend_name
            }])
            df = pd.concat([df, new_row], ignore_index=True)
    
    df = consolidate_duplicates(df)
    df.to_excel('player_stats.xlsx', index=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_player', methods=['POST'])
def add_player():
    player_name = request.form['player_name']
    friend_name = request.form['friend_name']
    if player_name and friend_name:
        player_name = standardize_name(player_name)
        friend_assignment[player_name] = friend_name
        save_data(friend_assignment, 'friend_assignments.json')
        update_excel_sheet()
        return redirect(url_for('index'))
    return "Error: Both fields are required"

@app.route('/add_mapping', methods=['POST'])
def add_mapping():
    short_name = request.form['short_name']
    full_name = request.form['full_name']
    if short_name and full_name:
        name_mapping[short_name] = full_name
        save_data(name_mapping, 'name_mappings.json')
        update_excel_sheet()
        return redirect(url_for('index'))
    return "Error: Both fields are required"

@app.route('/update_points', methods=['POST'])
def update_points():
    url = request.form['url']
    if url:
        if url in processed_urls:
            return "Error: This URL has already been processed."
        batting_data = scrape_batting_data(url)
        bowling_data = scrape_bowling_data(url)
        try:
            df = pd.read_excel('player_stats.xlsx')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['player_name', 'runs', 'wickets', 'points', 'friend_name'])
        
        for player in batting_data:
            friend_name = friend_assignment.get(player['player_name'], DEFAULT_FRIEND)
            player['player_name'] = standardize_name(player['player_name'])
            if player['player_name'] in df['player_name'].values:
                df.loc[df['player_name'] == player['player_name'], 'runs'] += player['runs']
            else:
                new_row = pd.DataFrame([{
                    'player_name': player['player_name'],
                    'runs': player['runs'],
                    'wickets': 0,
                    'points': 0,
                    'friend_name': friend_name
                }])
                df = pd.concat([df, new_row], ignore_index=True)
        
        for player in bowling_data:
            friend_name = friend_assignment.get(player['player_name'], DEFAULT_FRIEND)
            player['player_name'] = standardize_name(player['player_name'])
            if player['player_name'] in df['player_name'].values:
                df.loc[df['player_name'] == player['player_name'], 'wickets'] += player['wickets']
            else:
                new_row = pd.DataFrame([{
                    'player_name': player['player_name'],
                    'runs': 0,
                    'wickets': player['wickets'],
                    'points': 0,
                    'friend_name': friend_name
                }])
                df = pd.concat([df, new_row], ignore_index=True)
        
        df['points'] = df['runs'] + 25 * df['wickets']
        df = standardize_dataframe(df)
        df = consolidate_duplicates(df)
        df.to_excel('player_stats.xlsx', index=False)
        
        processed_urls.append(url)
        save_data(processed_urls, 'processed_urls.json')
        return redirect(url_for('index'))
    return "Error: URL is required"

@app.route('/get_scores', methods=['GET'])
def get_scores():
    try:
        df = pd.read_excel('player_stats.xlsx')
        df = standardize_dataframe(df)
        df = consolidate_duplicates(df)
        friend_points = df.groupby('friend_name')['points'].sum().reset_index()
        return jsonify({'data': df.to_dict(orient='records'), 'friend_points': friend_points.to_dict(orient='records')})
    except FileNotFoundError:
        return jsonify({'data': [], 'friend_points': []})

if __name__ == '__main__':
    app.run(debug=True)
