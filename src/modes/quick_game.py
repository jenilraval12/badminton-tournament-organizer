import matplotlib.pyplot as plt
from database.db_config import create_connection

def quick_game(user_id):
    connection = create_connection()
    if not connection:
        print("Database connection failed.")
        return

    try:
        cursor = connection.cursor()

        # Get player names
        player1 = input("Enter Player 1 Name: ").strip()
        player2 = input("Enter Player 2 Name: ").strip()

        # Ask for match points
        while True:
            try:
                match_points = int(input("Enter the points to win the match (e.g., 21): ").strip())
                if 1 <= match_points <= 21:
                    break
                else:
                    print("Match points must be between 1 and 21. Try again.")
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 21.")

        print(f"\nMatch set to {match_points} points! Enter scores as follows:")
        print(f"Enter '1' for {player1}, '2' for {player2}.\n")

        # Insert initial game record
        cursor.execute(
            "INSERT INTO quick_game (user_id, player1_name, player2_name, player1_score, player2_score, winner) VALUES (%s, %s, %s, 0, 0, NULL)",
            (user_id, player1, player2)
        )
        connection.commit()
        game_id = cursor.lastrowid

        player1_score = 0
        player2_score = 0
        is_deuce = False
        advantage_player = None

        while True:
            print(f"Score: {player1} {player1_score} : {player2} {player2_score}")

            # Deuce and advantage logic
            if player1_score >= match_points - 1 and player2_score >= match_points - 1:
                if player1_score == player2_score:
                    if not is_deuce or advantage_player:
                        print("\nDeuce! A player must now win by 2 points.")
                        is_deuce = True
                        advantage_player = None  # Clear advantage
                elif abs(player1_score - player2_score) == 1:
                    new_advantage_player = player1 if player1_score > player2_score else player2
                    if advantage_player != new_advantage_player:
                        advantage_player = new_advantage_player
                        print(f"\nAdvantage {advantage_player}!")

            # Input score
            while True:
                scorer = input(f"Enter '1' for {player1}, '2' for {player2}: ").strip()
                if scorer == "1":
                    player1_score += 1
                    break
                elif scorer == "2":
                    player2_score += 1
                    break
                else:
                    print("Invalid input. Try again.")

            # Check for winner
            if (player1_score >= match_points or player2_score >= match_points) and abs(player1_score - player2_score) >= 2:
                break

        # Determine winner
        winner = player1 if player1_score > player2_score else player2
        print(f"\n🎉 {winner} wins! Final Score: {player1} {player1_score} : {player2} {player2_score}\n")

        # Update game record
        cursor.execute(
            "UPDATE quick_game SET player1_score = %s, player2_score = %s, winner = %s WHERE game_id = %s",
            (player1_score, player2_score, winner, game_id)
        )
        connection.commit()

        # Post-match options
        while True:
            print("What would you like to do next?")
            print("1. See match recap")
            print("2. View scores as a bar graph")
            print("3. Return to game modes menu")
            choice = input("Enter your choice (1/2/3): ").strip()

            if choice == "1":
                print(f"\n--- Match Recap ---")
                print(f"Game ID: {game_id}")
                print(f"Player 1: {player1} | Score: {player1_score}")
                print(f"Player 2: {player2} | Score: {player2_score}")
                print(f"Winner: {winner}\n")
            elif choice == "2":
                # Display horizontal bar graph of scores with labels
                players = [player1, player2]
                scores = [player1_score, player2_score]

                plt.barh(players, scores, color=['blue', 'green'])
                for index, score in enumerate(scores):
                    plt.text(score + 0.5, index, str(score), va='center')  # Add labels to the bars

                plt.title("Match Scores")
                plt.xlabel("Scores")
                plt.ylabel("Players")
                plt.grid(axis='x', linestyle='--', alpha=0.7)
                plt.show()
            elif choice == "3":
                break
            else:
                print("Invalid choice. Try again.")


    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()
