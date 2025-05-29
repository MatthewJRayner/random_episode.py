# AUTHOR : MATTHEW RAYNER | "WHICH EPISODE SHOULD WE WATCH"

# LIBRARIES
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import random
import pandas as pd
import requests
import os

# CONFIG

CONFIG = {
    "file_path": "episodes.xlsx",
    "excel_sheet": "Sheet1",
    "tvmaze_base_url": "https://api.tvmaze.com",
    "max_attempts": 3 # Not currently in use
}

# CONSTANTS
file_path = CONFIG["file_path"]
if not os.path.exists(file_path): # Check for file path location and created one if needed
    pd.DataFrame(columns=["Title", "Seasons", "Eps Compressed"]).to_excel(CONFIG["file_path"], sheet_name=CONFIG["excel_sheet"], index=False)

# FUNCTIONS
def load_database():
    # Loads data from excel database
    try:
        return pd.read_excel(CONFIG["file_path"])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load database: {e}")
        return pd.DataFrame(columns=["Title", "Seasons", "Eps Compressed"])

def get_tvmaze_data(search):
    # Fetches title, total amount of seasons, and year of selected tv show
    try:
        url = f"{CONFIG['tvmaze_base_url']}/search/shows?q={search}"
        search_response = requests.get(url).json()
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Network error: {e}")
        return {}
    if not search_response:
        messagebox.showerror("Error", "No series found! Please try another name")
        return {}
    
    for result in search_response:
        name = result["show"]["name"]
        premiered = result["show"].get("premiered", "Unknown")
        ended = result["show"].get("ended", "None")
        if premiered and ended:
            confirm = messagebox.askyesno("Confirm", f"Is {name} ({premiered.split('-')[0]} - {ended.split('-')[0]}) the correct series?")
        else:
            confirm = messagebox.askyesno("Cofirm", f"Is {name} ({premiered.split('-')[0]} - Ongoing) the correct series?")
        if confirm:
            show_id = result["show"]["id"]
            details_url = f"{CONFIG['tvmaze_base_url']}/shows/{show_id}/seasons"
            details_response = requests.get(details_url).json()
            return {i + 1: details_response[i]["episodeOrder"] for i in range(len(details_response))}
    return {}

def extract_episode_data(series):
    # Converts the 'Eps Compressed' sections to usable episode per season data
    episodes = load_database()
    series_row = episodes[episodes["Title"] == series]
    if series_row.empty: return {}
    eps_per_season = list(map(int, series_row["Eps Compressed"].values[0].split()))
    episode_dict = {season + 1: eps_per_season[season] for season in range(len(eps_per_season))}
    return episode_dict

def randomizer(episode_dict):
    # Picks a random key and then a random number from a list of 1 - the value of that key
    if not episode_dict:
        return None, None
    chosen_season = random.choice(list(episode_dict.keys()))
    chosen_episode = random.randint(1, episode_dict[chosen_season] )
    return chosen_season, chosen_episode

def pick_random_episode():
    # Main function for the picking of a random episode
    series = series_var.get()
    episodes = load_database()
    if series not in list(episodes["Title"]):
        messagebox.showerror("Error", "Invalid Selection!")
        return
    episode_dict = extract_episode_data(series)
    if not episode_dict:
        messagebox.showerror("Error", "No episode data found for this series.")
        return
    chosen_season, chosen_episode = randomizer(episode_dict)
    result_label.config(text=f"Random Episode: Season {chosen_season} Episode {chosen_episode}")
    
def pick_random_series():
    # Selects a random series from the database
    series_list = list(load_database()["Title"])
    if not series_list:
        result_label.config(text="No series found.")
        return
    random_series = random.choice(series_list)
    series_var.set(random_series)
    
def add_to_database(series_name, episode_dict):
    # Adds the selection to the database to be used for the randomization
    episodes = load_database()
    if series_name in list(episodes["Title"]):
        messagebox.showerror("Error", "Series already exists in database")
        return
    new_row = pd.DataFrame([{
        "Title": series_name.title(),
        "Seasons": len(episode_dict),
        "Eps Compressed": " ".join(map(str, episode_dict.values()))
    }])
    pd.concat([episodes, new_row], ignore_index=True).to_excel(CONFIG["file_path"], sheet_name=CONFIG["excel_sheet"], index=False)
    refresh_dropdown()
    
def search_online():
    # Lets the user search for their series from the TVMaze API and checks for amount of episodes per season
    search_term = simpledialog.askstring("Search", "Enter series name:")
    if not search_term:
        return
    episode_dict = get_tvmaze_data(search_term)
    if episode_dict:
        add_to_database(search_term, episode_dict)
    
def manual_entry():
    # Allows the user to manually enter their own data about a series if the API doesn't work
    series_name = simpledialog.askstring("Manual Entry", "Enter series name:")
    if not series_name:
        return
    try:
        season_count = int(simpledialog.askstring("Manuel Entry", "Enter number of seasons"))
        if season_count <= 0:
            raise ValueError
        episode_dict = {}
        for i in range(season_count):
            eps = int(simpledialog.askstring("Manual Entry", f"Episodes in Seasons {i+1}:"))
            if eps <= 0:
                raise ValueError
            episode_dict[i+1] = eps
        add_to_database(series_name, episode_dict)
    except ValueError:
        messagebox.showerror("Error", "Invalid input.")

def refresh_dropdown():
    # Refreshes the dropdown
    series_list = list(load_database()["Title"].sort_values(ascending=True))
    series_dropdown["values"] = series_list
    if series_list:
        series_var.set(series_list[0])
    else:
        series_var.set("")

# MAIN
if __name__ == "__main__":
    
    # MAIN WINDOW
    root = tk.Tk()
    root.title("Which Episode Should We Watch?")
    root.geometry("400x325")
    root.resizable(width=False, height=False)
    root.configure(bg="#1e1e1e")
    
    # STYLING
    FONT_TITLE = ("Arial", 12, "bold")
    FONT_BUTTON = ("Arial", 10)
    BG_COLOUR = "#1e1e1e"
    FG_COLOUR = "#f8f8f8"
    BTN_COLOUR = "#1b3b6f"
    BTN_HOVER = "#162c52"
    ENTRY_BG = "#2c2c2c"
    ENTRY_FG = "black"
    
    # TITLE LABEL
    tk.Label(
        root, 
        text="Select a Series", 
        font=FONT_TITLE, 
        fg=FG_COLOUR, 
        bg=BG_COLOUR).pack(pady=10)
    
    # DROPDOWN MENU
    series_var = tk.StringVar(root)
    series_dropdown = ttk.Combobox(
        root, 
        textvariable=series_var, 
        state="readonly",
        background=ENTRY_BG, 
        foreground=ENTRY_FG)
    series_dropdown.pack(pady=5, padx=20, fill="x")
    
    # RESULTS DISPLAY
    result_label = tk.Label(
        root, 
        text="",
        font=FONT_BUTTON, 
        fg=FG_COLOUR, 
        bg=BG_COLOUR)
    result_label.pack(pady=10)
    
    # BUTTON STYLE FUNCTION
    def create_button(parent, text, command):
        btn = tk.Button(
            parent, 
            text=text, 
            command=command, 
            font=FONT_BUTTON, 
            bg=BTN_COLOUR, 
            fg="white", 
            padx=10, 
            pady=5, 
            relief="flat")
        btn.pack(pady=5, fill="x", padx=20)
        
        def on_enter(e): btn.config(bg=BTN_HOVER)
        def on_leave(e): btn.config(bg=BTN_COLOUR)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    # BUTTONS
    create_button(root, "Pick Random Episode", pick_random_episode)
    create_button(root, "Pick Random Series", pick_random_series)
    create_button(root, "Search Online", search_online)
    create_button(root, "Manual Entry", manual_entry)
    
    refresh_dropdown()
    root.mainloop()
