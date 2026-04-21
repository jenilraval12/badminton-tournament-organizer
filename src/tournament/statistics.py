import mysql.connector
import pandas as pd 
import matplotlib.pyplot as plt
from mysql.connector import Error
from tabulate import tabulate 
from collections import Counter
from database.db_config import create_connection
    
def view_tournament_details(user_id):
    # Establish the database connection
    connection = create_connection()
    if not connection:
        print("Database connection failed.")
        return

    try:
        # Create a cursor to fetch data
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                tourney_id AS `Tournament ID`, 
                tourney_name AS `Tournament Name`, 
                name_of_categories AS `Categories`, 
                status AS `Status`, 
                created_at AS `Created At`
            FROM 
                tournament 
            WHERE 
                user_id = %s;
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()

        if not results:
            print("No tournament details found for the user.")
            return

        # Convert results to a DataFrame
        df = pd.DataFrame(results)

        # Format the 'Categories' column to handle missing or invalid data
        df['Categories'] = df['Categories'].apply(
            lambda categories: "\n".join(str(categories).split(',')) if categories and isinstance(categories, str) else "No categories"
        )

        # Display the formatted table
        print("\n--- Tournament Details ---")
        print(tabulate(df, headers='keys', tablefmt="fancy_grid"))

    except Exception as e:
        print(f"Error fetching tournament details: {e}")
    finally:
        # Close the database connection
        connection.close()

def view_tournament_players_details(user_id):
    # Fetching user input for tournament selection
    connection = create_connection()
    if not connection:
        return
    
    try:
        # Fetching user input for tournament selection
        tourney_input = input("Enter the tournament ID or name: ").strip()
        category_filter = input("Do you want to filter by category? (Yes/No): ").strip().lower()
        selected_category = None
        if category_filter == "yes":
            selected_category = input("Enter the category name: ").strip()
        
        mode_filter = input("Do you want to filter by mode? (Yes/No): ").strip().lower()
        selected_mode = None
        if mode_filter == "yes":
            selected_mode = input("Enter the mode (Singles/Doubles): ").strip()

        # Building the base SQL query
        query = """
            SELECT ID, tourney_id, player_name, player1_name, player2_name, mobile_number, category, mode
            FROM tournament_players
            WHERE (user_id = %s AND tourney_id = %s OR %s IN (SELECT tourney_name FROM tournament WHERE tourney_id = tournament_players.tourney_id))
        """

        # Adding filters dynamically
        params = [user_id,tourney_input, tourney_input]  # Base parameters
        if selected_category:
            query += " AND category = %s"
            params.append(selected_category)
        if selected_mode:
            query += " AND mode = %s"
            params.append(selected_mode)

        # Executing the query
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()

        # If no results, notify the user
        if not results:
            print("No players found for the selected criteria.")
            return

        # Displaying results in a formatted table
        print("--- Tournament Players Details ---")
        headers = ["ID", "Tournament ID", "Player Name", "Player1 Name", "Player2 Name", "Mobile Number", "Category", "Mode"]
        print(tabulate(results, headers=headers, tablefmt="fancy_grid"))        
    
    except Error as e:
        print("Error occurred while accessing the database:", e)
    finally:
        # Closing the connection
        if connection.is_connected():
            connection.close()

def view_tournament_match_details(user_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    if not connection:
        return

    try:
        # Fetching user input for tournament selection
        tourney_input = input("Enter the tournament ID or name: ").strip()
        category_filter = input("Do you want to filter by category? (Yes/No): ").strip().lower()
        selected_categories = None
        if category_filter == "yes":
            # Accepting multiple categories separated by commas
            selected_categories = [category.strip() for category in input("Enter the category names (comma-separated): ").split(",")]

        mode_filter = input("Do you want to filter by mode? (Yes/No): ").strip().lower()
        selected_mode = None
        if mode_filter == "yes":
            selected_mode = input("Enter the mode (Singles/Doubles): ").strip()

        # Main query
        query = f"""
        SELECT match_id, player1_name, player2_name, team_A_players, team_B_players,
               round_name, category, mode, match_status, winner
        FROM tournament_matches
        WHERE (user_id = %s AND tourney_id = %s OR %s IN (SELECT tourney_name FROM tournament WHERE tourney_id = tournament_matches.tourney_id))
        """
        # Adding filters dynamically
        params = [user_id, tourney_input, tourney_input]  # Base parameters
        if selected_categories:
            query += " AND category IN (%s)" % ",".join(["%s"] * len(selected_categories))  # Using IN clause for multiple categories
            params.extend(selected_categories)
        if selected_mode:
            query += " AND mode = %s"
            params.append(selected_mode)

        # Executing the query
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        if not rows:
            print("No match records found for the given filters.")
            return

        # Format table data
        table_data = []
        for row in rows:
            # Determine which columns to display based on the mode
            if row["mode"].lower() == "singles":
                table_data.append([
                    row["match_id"],
                    row["player1_name"],
                    row["player2_name"],
                    row["round_name"],
                    row["category"],
                    row["mode"],
                    row["match_status"],
                    row["winner"] if row["winner"] else "N/A"  # Check for None
                ])
            else:  # Doubles or Mixed Doubles
                team_a_players = "\n".join(row["team_A_players"].split("&"))
                team_b_players = "\n".join(row["team_B_players"].split("&"))
                
                # Check if winner is None, then handle accordingly
                winner = "\n".join(row["winner"].split("&")) if row["winner"] else "N/A"
                
                table_data.append([
                    row["match_id"],
                    team_a_players,
                    team_b_players,
                    row["round_name"],
                    row["category"],
                    row["mode"],
                    row["match_status"],
                    winner
                ])

        # Define headers based on mode
        headers_singles = [
            "Match ID", "Player 1", "Player 2", "Round Name",
            "Category", "Mode", "Match Status", "Winner"
        ]
        headers_doubles = [
            "Match ID", "Team A Players", "Team B Players", "Round Name",
            "Category", "Mode", "Match Status", "Winner"
        ]

        # Display table
        if rows[0]["mode"].lower() == "singles":
            print("\n--- Tournament Matches Details ---")
            print(tabulate(table_data, headers=headers_singles, tablefmt="fancy_grid"))
        else:
            print("\n--- Tournament Matches Details ---")
            print(tabulate(table_data, headers=headers_doubles, tablefmt="fancy_grid"))

    except mysql.connector.Error as e:
        print("Error occurred while accessing the database:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def plot_matches_won(tourney_id, category, mode, user_id, cursor):
    connection = create_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        
        # Query to fetch match winners
        query = """
        SELECT winner
        FROM tournament_matches
        WHERE user_id = %s AND tourney_id = %s AND LOWER(category) = %s AND mode = %s AND winner IS NOT NULL
        """
        cursor.execute(query, (tourney_id, category, mode, user_id))
        rows = cursor.fetchall()
        print(rows)
        print(user_id)

        if not rows:
            print("No match records found for the given filters.")
            return

        # Count the number of wins for each player or team
        winners = [row['winner'] for row in rows]
        winner_counts = Counter(winners)

        # Prepare data for plotting
        players_or_teams = list(winner_counts.keys())
        matches_won = list(winner_counts.values())

        # Plot horizontal bar chart
        plt.figure(figsize=(10, 6))
        plt.barh(players_or_teams, matches_won, color="skyblue")
        plt.xlabel("Number of Matches Won")
        plt.ylabel("Player/Team")
        plt.title(f"Matches Won in {category} ({mode})")
        plt.legend()
        plt.tight_layout()
        plt.show()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        connection.close()

def plot_match_completion_status(tourney_id, category, mode, user_id):
    # Establish database connection
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    if not connection:
        print("Database connection failed!")
        return

    try:
        # Query to count Completed and Pending matches
        query = f"""
        SELECT Match_Status, COUNT(*) as count
        FROM tournament_matches
        WHERE user_id = %s AND tourney_id = %s AND category = %s AND mode = %s
        GROUP BY Match_Status
        """
        cursor.execute(query, (user_id, tourney_id, category, mode))
        rows = cursor.fetchall()

        # Organize data for the pie chart
        status_counts = {row["Match_Status"]: row["count"] for row in rows}
        completed_count = status_counts.get("Completed", 0)
        pending_count = status_counts.get("Pending", 0)

        # Pie chart data
        labels = ["Completed", "Pending"]
        sizes = [completed_count, pending_count]
        colors = ["#4CAF50", "#FF7043"]  # Green for completed, orange for pending
        explode = (0.1, 0)  # Slightly separate Completed

        # Plot the pie chart
        plt.figure(figsize=(8, 6))
        plt.pie(
            sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors, explode=explode
        )
        plt.title(
            f"Match Completion Status\n(Category: {category}, Mode: {mode})",
            fontsize=14,
        )
        plt.axis("equal")  # Equal aspect ratio for a perfect circle
        plt.show()

    except mysql.connector.Error as e:
        print("Error while fetching match status:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
