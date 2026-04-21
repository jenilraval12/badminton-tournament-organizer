import mysql.connector 
import pandas as pd
from tabulate import tabulate
from database.db_config import create_connection

def play_or_manage_matches(user_id):
    connection = create_connection()
    if not connection:
        print("Database connection failed.")
        return

    try:
        while True:
            # Step 1: Get Tournament, Category, and Mode
            tourney_id = input("Enter Tournament ID: ").strip()
            category_filter = input("Enter Category Name (e.g., 'Boys Singles'): ").strip()
            mode_filter = input("Enter Mode Name (e.g., 'Singles', 'Doubles', 'Mixed Doubles'): ").strip()

            while True:
                # Fetch matches for the specified filters
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT match_id, player1_name, player2_name, team_A_players, team_B_players,
                    category, mode, round_name, match_status, winner
                    FROM Tournament_Matches
                    WHERE user_id = %s AND tourney_id = %s AND category = %s AND mode = %s
                    """,
                    (user_id, tourney_id, category_filter, mode_filter)
                )
                matches = cursor.fetchall()

                if not matches:
                    print(f"No matches found for Tournament ID {tourney_id}, Category '{category_filter}', and Mode '{mode_filter}'.")
                    return

                # Convert match data to DataFrame
                matches_df = pd.DataFrame(matches, columns=[
                    "match_id", "player1_name", "player2_name", "team_A_players",
                    "team_B_players", "category", "mode", "round_name",
                    "match_status", "winner"
                ])

                # Display pending matches only
                pending_matches = matches_df[matches_df["match_status"] == "Pending"]
                if pending_matches.empty:
                    print(f"\nNo pending matches found for {category_filter} and {mode_filter}.")
                    break

                print("\n--- Pending Match Details ---")
                if mode_filter == "Singles":
                    print(tabulate(
                        pending_matches[["match_id", "player1_name", "player2_name", "round_name", "match_status"]],
                        headers=["Match ID", "Player 1", "Player 2", "Round", "Status"],
                        tablefmt="fancy_grid"
                    ))
                else:
                    pending_matches["team_A_players"] = pending_matches["team_A_players"].str.replace("&", "\n")
                    pending_matches["team_B_players"] = pending_matches["team_B_players"].str.replace("&", "\n")

                    print(tabulate(
                        pending_matches[["match_id", "team_A_players", "team_B_players", "round_name", "match_status", "winner"]],
                        headers=["Match ID", "Team A", "Team B", "Round", "Status", "Winner"],
                        tablefmt="fancy_grid"
                    ))

                # Ask user for the Match ID to score
                selected_match_id = int(input("\nEnter the Match ID to score: ").strip())
                selected_match = pending_matches[pending_matches['match_id'] == selected_match_id].iloc[0]

                # Initialize players or teams for scoring
                if mode_filter == "Singles":
                    player1 = selected_match['player1_name']
                    player2 = selected_match['player2_name']
                else:
                    player1 = selected_match['team_A_players'].replace("\n", " & ")
                    player2 = selected_match['team_B_players'].replace("\n", " & ")

                # Perform scoring
                score_match(connection, cursor, user_id, tourney_id, selected_match_id, player1, player2, category_filter, mode_filter)

                # Check for automatic round progression
                if check_and_progress_rounds(connection, cursor, user_id, tourney_id, category_filter, mode_filter):
                    print(f"\nRound progressed successfully for {category_filter} and {mode_filter}.")
                    break

                # Ask user for next action
                print("\nWhat would you like to do next?")
                print("1. Continue Matches")
                print("2. Change Category and Mode")
                print("3. Exit to Tournament Menu")

                user_choice = input("Enter your choice: ").strip()
                if user_choice == "1":
                    continue  # Stay in the current round and fetch matches again
                elif user_choice == "2":
                    break  # Exit to select a new category and mode
                elif user_choice == "3":
                    print("Returning to Tournament Menu...")
                    return
                else:
                    print("Invalid choice. Please try again.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()


def score_match(connection, cursor, user_id, tourney_id, match_id, player1, player2, category_filter, mode_filter):
    match_points = 21  # Points required to win a game
    player1_score, player2_score = 0, 0
    is_deuce = False
    advantage_player = None

    print(f"\nScoring for Match ID {match_id}: {player1} vs. {player2}")
    while True:
        try:
            scorer = int(input(f"Enter '1' for {player1}, '2' for {player2}: "))
            if scorer == 1:
                player1_score += 1
            elif scorer == 2:
                player2_score += 1
            else:
                print("Invalid input. Try again.")
                continue

            print(f"Score: {player1} {player1_score} : {player2_score} {player2}")

            # Deuce and Advantage Logic
            if player1_score >= match_points - 1 and player2_score >= match_points - 1:
                if player1_score == player2_score:
                    if not is_deuce or advantage_player:
                        print("\nDeuce! A player must now win by 2 points.")
                        is_deuce = True
                        advantage_player = None
                elif abs(player1_score - player2_score) == 1:
                    new_advantage_player = player1 if player1_score > player2_score else player2
                    if advantage_player != new_advantage_player:
                        advantage_player = new_advantage_player
                        print(f"\nAdvantage {advantage_player}!")

            # Check for winner
            if (is_deuce and abs(player1_score - player2_score) >= 2) or (
                not is_deuce and max(player1_score, player2_score) >= match_points
            ):
                winner = player1 if player1_score > player2_score else player2
                print(f"\n🎉 {winner} wins the match! Final Score: {player1} {player1_score} : {player2_score} {player2}")

                
                cursor.execute(
                    """
                    UPDATE Tournament_Matches
                    SET match_status = 'Completed', winner = %s, 
                        plr1_score_game1 = %s, plr2_score_game1 = %s
                    WHERE match_id = %s
                    """,
                    (winner, player1_score, player2_score, match_id)
                )
                connection.commit()
                break
        except ValueError:
            print("Invalid input. Try again.")

    # Check for automatic round progression
    check_and_progress_rounds(connection, cursor, user_id, tourney_id, category_filter, mode_filter)


def check_and_progress_rounds(connection, cursor, user_id, tourney_id, category_filter, mode_filter):
    # Check if there are any pending matches in the current round
    cursor.execute(
        """
        SELECT round_name, COUNT(*) FROM Tournament_Matches
        WHERE tourney_id = %s AND category = %s AND mode = %s AND match_status = 'Pending'
        GROUP BY round_name
        """,
        (tourney_id, category_filter, mode_filter)
    )
    pending_matches = cursor.fetchall()

    if not pending_matches:
        # No pending matches, proceed to the next round
        progress_to_next_round(connection, user_id, tourney_id, category_filter, mode_filter)
        return True
    return False


def progress_to_next_round(connection, user_id, tourney_id, category_filter, mode_filter):
    try:
        cursor = connection.cursor()

        # Step 1: Determine the current round
        cursor.execute(
            """
            SELECT DISTINCT round_name
            FROM Tournament_Matches
            WHERE tourney_id = %s AND category = %s AND mode = %s
            ORDER BY FIELD(round_name, 'Knockout', 'Quarterfinal', 'Semifinal', 'Final')
            """,
            (tourney_id, category_filter, mode_filter)
        )
        current_round_result = cursor.fetchall()

        if not current_round_result:
            print(f"No matches found for the tournament in {category_filter} and {mode_filter}.")
            return

        current_round = current_round_result[-1][0]  # Get the latest round
        print(f"Current round is: {current_round}")

        # Step 2: Check if there are any pending matches in the current round
        cursor.execute(
            """
            SELECT COUNT(*) FROM Tournament_Matches
            WHERE tourney_id = %s AND category = %s AND mode = %s AND round_name = %s AND match_status = 'Pending'
            """,
            (tourney_id, category_filter, mode_filter, current_round)
        )
        pending_matches = cursor.fetchone()[0]

        if pending_matches > 0:
            print(f"There are still {pending_matches} pending matches in the {current_round} round.")
            return

        # Step 3: Determine the next round
        next_round = {
            "Knockout": "Quarterfinal",
            "Quarterfinal": "Semifinal",
            "Semifinal": "Final",
        }.get(current_round, None)

        if not next_round:
            print(f"The tournament for {category_filter} and {mode_filter} has concluded.")
            return

        # Step 4: Check if the next round is already created
        cursor.execute(
            """
            SELECT COUNT(*) FROM Tournament_Matches
            WHERE tourney_id = %s AND category = %s AND mode = %s AND round_name = %s
            """,
            (tourney_id, category_filter, mode_filter, next_round)
        )
        next_round_exists = cursor.fetchone()[0]

        if next_round_exists > 0:
            print(f"The {next_round} round has already been created for {category_filter} and {mode_filter}.")
            return

        # Step 5: Fetch winners from the current round
        cursor.execute(
            """
            SELECT winner FROM Tournament_Matches
            WHERE tourney_id = %s AND category = %s AND mode = %s AND round_name = %s AND match_status = 'Completed'
            """,
            (tourney_id, category_filter, mode_filter, current_round)
        )
        winners = [row[0] for row in cursor.fetchall()]

        if not winners:
            print(f"No winners found in the {current_round} round for {category_filter} and {mode_filter}.")
            return

        # Step 6: Create matches for the next round
        for i in range(0, len(winners), 2):
            if mode_filter == 'Singles':
                if i + 1 < len(winners):
                    cursor.execute(
                        """
                        INSERT INTO Tournament_Matches (
                            user_id, tourney_id, player1_name, player2_name,
                            category, mode, round_name, match_status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (user_id, tourney_id, winners[i], winners[i + 1],
                        category_filter, mode_filter, next_round, "Pending")
                    )
            elif mode_filter == 'Doubles' or mode_filter == 'Mixed Doubles':
                if i + 1 < len(winners):
                    # Assuming each winner is a team of players in Doubles/Mixed Doubles mode
                    team_a = winners[i].split('&')  # Assuming winners are stored as comma-separated player names
                    team_b = winners[i + 1].split('&') if i + 1 < len(winners) else []

                    cursor.execute(
                        """
                        INSERT INTO Tournament_Matches (
                            user_id, tourney_id, team_a_players, team_b_players,
                            category, mode, round_name, match_status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (user_id, tourney_id, '& '.join(team_a), '& '.join(team_b),
                        category_filter, mode_filter, next_round, "Pending")
                    )
        connection.commit()
        print(f"{next_round} matches created successfully for {category_filter} and {mode_filter}.")

    except mysql.connector.Error as e:
        print(f"Database error during round progression: {e}")
        connection.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
        connection.rollback()