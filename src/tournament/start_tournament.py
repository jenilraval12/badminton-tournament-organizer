import pandas as pd
import random
from database.db_config import create_connection


def start_tournament(user_id):
    connection = create_connection()
    if not connection:
        print("Database connection failed.")
        return

    try:
        # Step 1: Collect Tournament Details
        tourney_name = input("Enter Tournament Name: ").strip()
        no_of_categories = int(input("Enter Number of Categories: ").strip())
        categories = input("Enter Category Names (comma-separated): ").strip()
        knockout_point = int(input("Enter Points for Knockout Round: ").strip())
        quarter_point = int(input("Enter Points for Quarterfinal Round: ").strip())
        semi_final_point = int(input("Enter Points for Semifinal Round: ").strip())
        final_point = int(input("Enter Points for Final Round: ").strip())

        # Insert tournament details into the database
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO Tournament (
                user_id, tourney_name, no_of_categories, name_of_categories,
                knockout_point, quarter_point, semi_final_point, final_point, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, tourney_name, no_of_categories, categories,
             knockout_point, quarter_point, semi_final_point, final_point, "Ongoing")
        )
        connection.commit()

        # Get the generated Tournament ID
        tourney_id = cursor.lastrowid
        print(f"Tournament '{tourney_name}' created successfully with ID {tourney_id}.")

        # Step 2: Read Player Details from CSV
        csv_path = input("Enter the path to the CSV file containing player details: ").strip()
        players_df = pd.read_csv(csv_path)

        # Replace NaN values with None (MySQL NULL equivalent)
        players_df = players_df.where(pd.notnull(players_df), None)

        # Insert player details into the database
        for _, row in players_df.iterrows():
            cursor.execute(
                """
                INSERT INTO Tournament_Players (
                    user_id, tourney_id, player_name, player1_name, player2_name,
                    mobile_number, category, mode
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, tourney_id, row.get('Player Name'), row.get('Player 1 Name'),
                 row.get('Player 2 Name'), row.get('Mobile Number'),
                 row.get('Category'), row.get('Mode'))
            )

        connection.commit()
        print("Players added successfully.")

        # Step 3: Generate Knockout Matches
        print("Creating knockout matches...")
        cursor.execute(
            """
            SELECT player_name, player1_name, player2_name, category, mode
            FROM Tournament_Players
            WHERE tourney_id = %s AND user_id = %s
            """,
            (tourney_id, user_id)
        )
        players = cursor.fetchall()

        # Organize players by category and mode
        categories = {}
        for player in players:
            category, mode = player[3], player[4]
            categories.setdefault((category, mode), []).append(player)

        # Create matches for each category and mode
        for (category, mode), player_list in categories.items():
            random.shuffle(player_list)

            matches = []
            for i in range(0, len(player_list), 2):
                if i + 1 < len(player_list):
                    # Pair two players/teams for a match
                    player1, player2 = player_list[i], player_list[i + 1]
                    matches.append((player1, player2))
                else:
                    # Handle BYE if odd number of players/teams
                    player1 = player_list[i]
                    matches.append((player1, None))  # None represents a BYE

            # Insert matches into the database
            for match in matches:
                if mode == "Singles":
                    player1_name, player2_name = match[0][0], match[1][0] if match[1] else None
                    cursor.execute(
                        """
                        INSERT INTO Tournament_Matches (
                            user_id, tourney_id, player1_name, player2_name,
                            category, mode, round_name, Match_Status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (user_id, tourney_id, player1_name, player2_name,
                         category, mode, "Knockout", "Pending")
                    )
                elif mode in ["Doubles", "Mixed Doubles"]:
                    team_a = f"{match[0][1]} & {match[0][2]}"
                    team_b = f"{match[1][1]} & {match[1][2]}" if match[1] else None
                    cursor.execute(
                        """
                        INSERT INTO Tournament_Matches (
                            user_id, tourney_id, team_A_players, team_B_players,
                            category, mode, round_name, Match_Status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (user_id, tourney_id, team_a, team_b,
                         category, mode, "Knockout", "Pending")
                    )

        connection.commit()
        print("Knockout matches created successfully.")
        return tourney_id

    except Exception as e:
        print(f"Error during tournament creation: {e}")
    finally:
        connection.close()
