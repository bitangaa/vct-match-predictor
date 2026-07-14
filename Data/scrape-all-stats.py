import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import urllib.parse

def get_all_match_links(team_matches_url):
    try:
        response = requests.get(team_matches_url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {team_matches_url}: {e}")
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    match_links = []
    for a in soup.find_all('a', class_='wf-card'):
        href = a.get('href')
        date_div = a.find('div', class_='m-item-date')
        match_date = None
        if date_div:
            date_inner = date_div.find('div')
            if date_inner:
                match_date = date_inner.text.strip()
        if href and 'vs' in href and '?' not in href:
            match_links.append({'url': 'https://www.vlr.gg' + href, 'date': match_date})
    return match_links

def load_scraped_match_ids(filepath):
    try:
        with open(filepath, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_scraped_match_id(filepath, match_id):
    with open(filepath, 'a') as f:
        f.write(match_id + '\n')

def fetch_team_stats(soup, match_url, match_date, patch, team1, team2, team1_won, team2_won, series_score):
    team_stats = []
    for map_game in soup.find_all('div', class_='vm-stats-game'):
        map_game_id = map_game.get('data-game-id')
        map_url = f"{match_url}?game={map_game_id}" if map_game_id else None

        map_game_header = map_game.find('div', class_='vm-stats-game-header')
        if not map_game_header:
            continue

        team_blocks = map_game_header.find_all('div', class_='team')
        if len(team_blocks) < 2:
            continue

        team1_score_div = team_blocks[0].find('div', class_='score')
        team1_map_score = int(team1_score_div.text.strip()) if team1_score_div else None

        team2_score_div = team_blocks[1].find('div', class_='score')
        team2_map_score = int(team2_score_div.text.strip()) if team2_score_div else None

        rounds_played = None
        won_map_team = [None, None]
        if team1_map_score is not None and team2_map_score is not None:
            rounds_played = team1_map_score + team2_map_score
            won_map_team[0] = team1_map_score > team2_map_score
            won_map_team[1] = team2_map_score > team1_map_score

        map_div = map_game_header.find('div', class_='map')
        map_name = None
        if map_div:
            name_div = map_div.find('div', style=lambda v: v and 'font-weight: 700' in v and 'font-size: 20px' in v)
            if name_div:
                first_span = name_div.find('span')
                if first_span and first_span.contents:
                    map_name = first_span.contents[0].strip()

        stat_tables = map_game.find_all('table')
        for team_idx, table in enumerate(stat_tables[:2]):
            team = team1 if team_idx == 0 else team2
            opponent = team2 if team_idx == 0 else team1
            won_series = team1_won if team_idx == 0 else team2_won
            won_map = won_map_team[team_idx]

            team_kills = 0
            team_deaths = 0
            team_assists = 0
            team_first_kills = 0
            team_first_deaths = 0
            player_count = 0
            agents = []

            acs_list = []
            acs_attack_list = []
            acs_defense_list = []
            kast_list = []

            for row in table.find_all('tr'):
                if row.find('th'):
                    continue

                # Agent extraction
                agent_td = row.find('td', class_='mod-agents')
                agent = ""
                if agent_td:
                    img = agent_td.find('img')
                    if img and img.has_attr('alt'):
                        agent = img['alt'].strip().lower()
                agents.append(agent)

                # Kills
                kills_td = row.find('td', class_='mod-stat mod-vlr-kills')
                kills_span = kills_td.find('span', class_='side mod-side mod-both') if kills_td else None
                kills = int(kills_span.text.strip()) if kills_span and kills_span.text.strip().isdigit() else 0

                # Deaths
                deaths_td = row.find('td', class_='mod-stat mod-vlr-deaths')
                deaths_span = deaths_td.find('span', class_='side mod-both') if deaths_td else None
                deaths = int(deaths_span.text.strip()) if deaths_span and deaths_span.text.strip().isdigit() else 0

                # Assists
                assists_td = row.find('td', class_='mod-stat mod-vlr-assists')
                assists_span = assists_td.find('span', class_='side mod-both') if assists_td else None
                assists = int(assists_span.text.strip()) if assists_span and assists_span.text.strip().isdigit() else 0

                # ACS (overall, attack, defense)
                acs = acs_attack = acs_defense = 0
                mod_stat_tds = row.find_all('td', class_='mod-stat')
                if len(mod_stat_tds) > 1:
                    acs_td = mod_stat_tds[1]  # Second mod-stat is ACS
                    acs_span = acs_td.find('span', class_='side mod-side mod-both')
                    if acs_span and acs_span.text.strip().replace('.', '', 1).isdigit():
                        acs = float(acs_span.text.strip())
                    acs_t_span = acs_td.find('span', class_='side mod-side mod-t')
                    if acs_t_span and acs_t_span.text.strip().replace('.', '', 1).isdigit():
                        acs_attack = float(acs_t_span.text.strip())
                    acs_ct_span = acs_td.find('span', class_='side mod-side mod-ct')
                    if acs_ct_span and acs_ct_span.text.strip().replace('.', '', 1).isdigit():
                        acs_defense = float(acs_ct_span.text.strip())
                acs_list.append(acs)
                acs_attack_list.append(acs_attack)
                acs_defense_list.append(acs_defense)

                # KAST and Headshot %
                kast = None
                headshot_pct = None
                percent_found = 0
                for td in row.find_all('td', class_='mod-stat'):
                    span = td.find('span', class_='side mod-both')
                    if span and '%' in span.text:
                        try:
                            val = float(span.text.strip().replace('%', ''))
                        except Exception:
                            continue
                        if percent_found == 0:
                            kast = val
                        elif percent_found == 1:
                            headshot_pct = val
                            break  # Found both, stop searching
                        percent_found += 1

                # First Kills
                fk_td = row.find('td', class_='mod-stat mod-fb')
                fk_span = fk_td.find('span', class_='side mod-both') if fk_td else None
                fk = int(fk_span.text.strip()) if fk_span and fk_span.text.strip().isdigit() else 0

                # First Deaths
                fd_td = row.find('td', class_='mod-stat mod-fd')
                fd_span = fd_td.find('span', class_='side mod-both') if fd_td else None
                fd = int(fd_span.text.strip()) if fd_span and fd_span.text.strip().isdigit() else 0

                team_kills += kills
                team_deaths += deaths
                team_assists += assists
                team_first_kills += fk
                team_first_deaths += fd
                player_count += 1

            # After the player loop, calculate averages:
            avg_acs = sum(acs_list) / len(acs_list) if acs_list else 0
            avg_acs_attack = sum(acs_attack_list) / len(acs_attack_list) if acs_attack_list else 0
            avg_acs_defense = sum(acs_defense_list) / len(acs_defense_list) if acs_defense_list else 0
            avg_kast = sum(kast_list) / len(kast_list) if kast_list else 0

            if player_count > 0:
                rounds_won = team1_map_score if team_idx == 0 else team2_map_score
                agents = agents[:5] + [""] * (5 - len(agents))
                team_stats.append({
                    'patch': patch,
                    'date': match_date,
                    'map': map_name,
                    'team': team,
                    'opponent': opponent,
                    'won_map': won_map,
                    'won_series': won_series,
                    'series_score': series_score,
                    'rounds_played': rounds_played,
                    'rounds_won': rounds_won,
                    'total_kills': team_kills,
                    'total_deaths': team_deaths,
                    'total_assists': team_assists,
                    'avg_acs': avg_acs,
                    'avg_acs_attack': avg_acs_attack,
                    'avg_acs_defense': avg_acs_defense,
                    'avg_kast': avg_kast,
                    'total_first_kills': team_first_kills,
                    'total_first_deaths': team_first_deaths,
                    'agent1': agents[0],
                    'agent2': agents[1],
                    'agent3': agents[2],
                    'agent4': agents[3],
                    'agent5': agents[4],
                    'map_url': map_url,
                })
    return team_stats

def fetch_player_stats(soup, match_url, match_date, patch, team1, team2, team1_won, team2_won, series_score):
    player_stats = []
    for map_game in soup.find_all('div', class_='vm-stats-game'):
        map_game_id = map_game.get('data-game-id')
        map_url = f"{match_url}?game={map_game_id}" if map_game_id else None

        map_game_header = map_game.find('div', class_='vm-stats-game-header')
        if not map_game_header:
            continue

        team_blocks = map_game_header.find_all('div', class_='team')
        if len(team_blocks) < 2:
            continue

        map_div = map_game_header.find('div', class_='map')
        map_name = None
        if map_div:
            name_div = map_div.find('div', style=lambda v: v and 'font-weight: 700' in v and 'font-size: 20px' in v)
            if name_div:
                first_span = name_div.find('span')
                if first_span and first_span.contents:
                    map_name = first_span.contents[0].strip()

        stat_tables = map_game.find_all('table')
        for team_idx, table in enumerate(stat_tables[:2]):
            team = team1 if team_idx == 0 else team2
            opponent = team2 if team_idx == 0 else team1
            won_series = team1_won if team_idx == 0 else team2_won

            for row in table.find_all('tr'):
                if row.find('th'):
                    continue

                # Player display name
                player_td = row.find('td', class_='mod-player')
                player_name = ""
                if player_td:
                    div_name = player_td.find('div', class_='text-of')
                    if div_name:
                        player_name = div_name.text.strip()
                    else:
                        player_name = player_td.get_text(strip=True)

                # Agent extraction
                agent_td = row.find('td', class_='mod-agents')
                agent = ""
                if agent_td:
                    img = agent_td.find('img')
                    if img and img.has_attr('alt'):
                        agent = img['alt'].strip().capitalize()

                # Kills
                kills_td = row.find('td', class_='mod-stat mod-vlr-kills')
                kills_span = kills_td.find('span', class_='side mod-side mod-both') if kills_td else None
                kills = int(kills_span.text.strip()) if kills_span and kills_span.text.strip().isdigit() else 0

                # Deaths
                deaths_td = row.find('td', class_='mod-stat mod-vlr-deaths')
                deaths_span = deaths_td.find('span', class_='side mod-both') if deaths_td else None
                deaths = int(deaths_span.text.strip()) if deaths_span and deaths_span.text.strip().isdigit() else 0

                # Assists
                assists_td = row.find('td', class_='mod-stat mod-vlr-assists')
                assists_span = assists_td.find('span', class_='side mod-both') if assists_td else None
                assists = int(assists_span.text.strip()) if assists_span and assists_span.text.strip().isdigit() else 0

                # ACS (overall, attack, defense)
                acs = acs_attack = acs_defense = 0
                mod_stat_tds = row.find_all('td', class_='mod-stat')
                if len(mod_stat_tds) > 1:
                    acs_td = mod_stat_tds[1]  # Second mod-stat is ACS
                    acs_span = acs_td.find('span', class_='side mod-side mod-both')
                    if acs_span and acs_span.text.strip().replace('.', '', 1).isdigit():
                        acs = float(acs_span.text.strip())
                    acs_t_span = acs_td.find('span', class_='side mod-side mod-t')
                    if acs_t_span and acs_t_span.text.strip().replace('.', '', 1).isdigit():
                        acs_attack = float(acs_t_span.text.strip())
                    acs_ct_span = acs_td.find('span', class_='side mod-side mod-ct')
                    if acs_ct_span and acs_ct_span.text.strip().replace('.', '', 1).isdigit():
                        acs_defense = float(acs_ct_span.text.strip())

                # KAST and Headshot %
                kast = None
                headshot_pct = None
                percent_found = 0
                for td in row.find_all('td', class_='mod-stat'):
                    span = td.find('span', class_='side mod-both')
                    if span and '%' in span.text:
                        try:
                            val = float(span.text.strip().replace('%', ''))
                        except Exception:
                            continue
                        if percent_found == 0:
                            kast = val
                        elif percent_found == 1:
                            headshot_pct = val
                            break  # Found both, stop searching
                        percent_found += 1

                # First Kills
                fk_td = row.find('td', class_='mod-stat mod-fb')
                fk_span = fk_td.find('span', class_='side mod-both') if fk_td else None
                fk = int(fk_span.text.strip()) if fk_span and fk_span.text.strip().isdigit() else 0

                # First Deaths
                fd_td = row.find('td', class_='mod-stat mod-fd')
                fd_span = fd_td.find('span', class_='side mod-both') if fd_td else None
                fd = int(fd_span.text.strip()) if fd_span and fd_span.text.strip().isdigit() else 0

                player_stats.append({
                    'patch': patch,
                    'date': match_date,
                    'name': player_name,
                    'map': map_name,
                    'team': team,
                    'opponent': opponent,
                    'agent': agent,
                    'kills': kills,
                    'deaths': deaths,
                    'assists': assists,
                    'acs': acs,
                    'acs_attack': acs_attack,
                    'acs_defense': acs_defense,
                    'kast': kast,
                    'first_kills': fk,
                    'first_deaths': fd,
                    'headshot_pct': headshot_pct,
                    'map_url': map_url,
                })
    return player_stats

def load_team_match_urls(filepath):
    try:
        with open(filepath, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        if not urls:
            print(f"No team match URLs found in {filepath}")
        return urls
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return []

if __name__ == "__main__":
    team_match_pages_file = "Data/Dictionaries//team_match_pages.txt"
    team_match_urls = load_team_match_urls(team_match_pages_file)

    scraped_ids_file = "Data/old_match_ids.txt"
    scraped_match_ids = load_scraped_match_ids(scraped_ids_file)

    team_stats_csv = "Data/team_stats3.csv"
    player_stats_csv = "Data/player_stats3.csv"

    if not team_match_urls:
        print("No team match URLs to process. Exiting.")
    else:
        for team_matches_url in team_match_urls:
            print(f"Processing team match page: {team_matches_url}")
            match_links = get_all_match_links(team_matches_url)
            if not match_links:
                print(f"No matches found for {team_matches_url}")
                continue
            for match in match_links:
                match_url = match['url']
                match_date = match['date']
                parsed = urllib.parse.urlparse(match_url)
                match_id = parsed.path.split('/')[1] if len(parsed.path.split('/')) > 1 else None
                if not match_id:
                    print(f"Could not extract match ID from {match_url}")
                    continue
                if match_id in scraped_match_ids:
                    print(f"Skipping already scraped match: {match_url}")
                    continue

                try:
                    response = requests.get(match_url)
                    response.raise_for_status()
                except Exception as e:
                    print(f"Failed to fetch {match_url}: {e}")
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')

                patch = None
                col_mod3 = soup.find('div', class_='col mod-3')
                if col_mod3:
                    patch_div = col_mod3.find('div', style=lambda v: v and 'font-style: italic' in v)
                    if patch_div and 'Patch' in patch_div.text:
                        patch = patch_div.text.strip()

                team_names = [div.text.strip() for div in soup.find_all('div', class_='team-name')]
                if len(team_names) < 2:
                    team_names = [div.text.strip() for div in soup.find_all('div', class_='wf-title-med')]
                team1, team2 = team_names[:2] if len(team_names) >= 2 else ("Unknown", "Unknown")

                score_winner = soup.find('span', class_='match-header-vs-score-winner')
                score_loser = soup.find('span', class_='match-header-vs-score-loser')
                series_score = ""
                team1_score = team2_score = None
                team1_won = team2_won = None
                if score_winner and score_loser:
                    team1_score = int(score_winner.text.strip())
                    team2_score = int(score_loser.text.strip())
                    series_score = f"{team1_score}:{team2_score}"
                    team1_won = team1_score > team2_score
                    team2_won = team2_score > team1_score

                # --- TEAM STATS ---
                team_stats = fetch_team_stats(
                    soup, match_url, match_date, patch, team1, team2, team1_won, team2_won, series_score
                )
                if team_stats:
                    file_exists = os.path.isfile(team_stats_csv)
                    pd.DataFrame(team_stats).to_csv(team_stats_csv, mode='a', header=not file_exists, index=False)
                    print(f"Appended {len(team_stats)} team stats from {match_url}")
                else:
                    print(f"No team stats found for {match_url}")

                # --- PLAYER STATS ---
                player_stats = fetch_player_stats(
                    soup, match_url, match_date, patch, team1, team2, team1_won, team2_won, series_score
                )
                if player_stats:
                    player_exists = os.path.isfile(player_stats_csv)
                    pd.DataFrame(player_stats).to_csv(player_stats_csv, mode='a', header=not player_exists, index=False)
                    print(f"Appended {len(player_stats)} player stats from {match_url}")
                else:
                    print(f"No player stats found for {match_url}")

                save_scraped_match_id(scraped_ids_file, match_id)