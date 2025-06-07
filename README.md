# YouTube VC Lead Generator

This repository contains an automated system for generating daily lists of YouTube channels related to venture capital, angel investing, and startup content.

It uses the YouTube Data API along with GitHub Actions to fetch, deduplicate, and store a set number of unique leads each day. The system is designed to consistently provide new and actionable data without repeating previously collected channels.



# Overview

- Scrapes up to 200 relevant YouTube channels each day
- Maintains a persistent history (`history.csv`) to avoid duplicates across runs
- Outputs a fresh daily lead file (`vc_leads_YYYY-MM-DD.csv`)
- Uses a diverse pool of startup- and VC-related search terms
- Automatically runs every day using GitHub Actions
- Tracks and uploads both daily and cumulative results



# Repository Structure



# How It Works

1. A large pool of search queries is shuffled each run to increase lead diversity.
2. The script uses the YouTube Data API to search for channels based on these terms.
3. It filters out any channels already listed in `history.csv`.
4. Up to 200 unique leads are saved to a daily CSV file.
5. All new leads are appended to `history.csv` to avoid duplication on future runs.
6. Both the daily output and updated history file are uploaded as workflow artifacts.



# Setup Instructions

1. Fork this repository or clone it into your own project.
2. Create a new GitHub Actions secret:
   - Name: `YOUTUBE_API_KEY`
   - Value: Your YouTube Data API v3 key
3. Ensure that `history.csv` exists in the root of your repository with the following header row:
