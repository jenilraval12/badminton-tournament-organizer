import matplotlib.pyplot as plt
from database.db_config import create_connection

def quick_match(user_id):
    connection = create_connection()
    if not connection:
        print("Database connection failed.")
        return

    try:
        cursor = connection.cursor()

        # Get player names and match points
        print("\n--- Quick Match (Best-of-3 Games) ---")
        player1 = input("Enter Player 1 Name: ").strip()
        player2 = input("Enter Player 2 Name: ").strip()

        while True:
            try:
                match_points = int(input("Enter the points to win each game (e.g., 21, max 21): "))
                if 1 <= match_points <= 21:
                    break
                else:
                    print("Points must be between 1 and 21. Try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        print(f"\nMatch set to {match_points} points!\n")

        # Initialize match data
        game_scores = {
            "game1": {player1: 0, player2: 0},
            "game2": {player1: 0, player2: 0},
            "game3": {player1: 0, player2: 0},
        }
        game_winners = []
        overall_winner = None

        for game_number in range(1, 4):
            print(f"\n--- Game {game_number} ---")
            player1_score = 0
            player2_score = 0
            is_deuce = False
            advantage_player = None

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

                    if (is_deuce and abs(player1_score - player2_score) >= 2) or (not is_deuce and max(player1_score, player2_score) >= match_points):
                        winner = player1 if player1_score > player2_score else player2
                        print(f"\n🎉 {winner} wins Game {game_number}! Final Score: {player1} {player1_score} : {player2_score} {player2}")
                        game_scores[f"game{game_number}"] = {player1: player1_score, player2: player2_score}
                        game_winners.append(winner)
                        break

                except ValueError:
                    print("Invalid input. Try again.")

            # Save game data after each game
            cursor.execute(
                f"""
                INSERT INTO quick_match (
                    user_id, player1_name, player2_name, 
                    plr1_score_game1, plr2_score_game1, 
                    plr1_score_game2, plr2_score_game2, 
                    plr1_score_game3, plr2_score_game3, 
                    game_winner, match_winner
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id, player1, player2,
                    game_scores['game1'][player1], game_scores['game1'][player2],
                    game_scores['game2'][player1] if game_number >= 2 else None,
                    game_scores['game2'][player2] if game_number >= 2 else None,
                    game_scores['game3'][player1] if game_number == 3 else None,
                    game_scores['game3'][player2] if game_number == 3 else None,
                    ','.join(game_winners),
                    None  # Match winner will be determined at the end
                )
            )
            connection.commit()

            # Determine if the match is won
            if game_winners.count(player1) == 2:
                overall_winner = player1
                print(f"\n🎉 {player1} wins the match with 2 games!")
                break
            elif game_winners.count(player2) == 2:
                overall_winner = player2
                print(f"\n🎉 {player2} wins the match with 2 games!")
                break

                    # Prompt user to view recap or proceed
            while True:
                print("\nOptions:")
                print("1. View match recap in text format.")
                print("2. View match recap as a bar graph.")
                print("3. Proceed to the next game.")
                
                recap_option = input("\nChoose an option (1/2/3): ").strip()
                
                if recap_option == "1":
                    print("\nMatch Recap So Far:")
                    for i in range(1, game_number + 1):
                        print(f"Game {i}: {player1} {game_scores[f'game{i}'][player1]} : {game_scores[f'game{i}'][player2]} {player2} - Winner: {game_winners[i-1]}")
                elif recap_option == "2":
                    
                    # Display horizontal bar graph for the current game
                    print(f"\nDisplaying scores for Game {game_number} as a horizontal bar graph...")
                    scores = [game_scores[f'game{game_number}'][player1], game_scores[f'game{game_number}'][player2]]
                    players = [player1, player2]

                    plt.barh(players, scores, color=['blue', 'green'])
                    for index, score in enumerate(scores):
                        plt.text(score + 0.5, index, str(score), va='center')

                    plt.title(f"Scores - Game {game_number}")
                    plt.xlabel("Scores")
                    plt.ylabel("Players")
                    plt.grid(axis='x', linestyle='--', alpha=0.7)
                    plt.legend()
                    plt.show()
                    
                elif recap_option == "3":
                    print("\nMoving to the next game...")
                    break
                else:
                    print("Invalid input. Please try again.")        
        
        # Display final horizontal bar graph for all games
        game_labels = ["Game 1", "Game 2", "Game 3"]
        player1_scores = [game_scores[f"game{i}"][player1] for i in range(1, 4)]
        player2_scores = [game_scores[f"game{i}"][player2] for i in range(1, 4)]

        y_pos = range(len(game_labels))

        plt.barh(y_pos, player1_scores, height=0.4, color='blue', label=player1, align='center')
        plt.barh([p + 0.4 for p in y_pos], player2_scores, height=0.4, color='green', label=player2, align='center')

        for i, (p1_score, p2_score) in enumerate(zip(player1_scores, player2_scores)):
            plt.text(p1_score + 0.5, i, str(p1_score), va='center')
            plt.text(p2_score + 0.5, i + 0.4, str(p2_score), va='center')

        plt.title("Scores Across All Games")
        plt.ylabel("Games")
        plt.xlabel("Scores")
        plt.yticks([p + 0.2 for p in y_pos], game_labels)
        plt.legend()
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.show()

        # Update match winner in the database
        cursor.execute(
            "UPDATE quick_match SET match_winner = %s WHERE user_id = %s AND match_winner IS NULL",
            (overall_winner, user_id)
        )
        connection.commit()

        # Display final recap
        print("\n--- Final Match Recap ---")
        for i, winner in enumerate(game_winners, 1):
            print(f"Game {i}: {player1} {game_scores[f'game{i}'][player1]} : {game_scores[f'game{i}'][player2]} {player2} - Winner: {winner}")
        print(f"\n🎉 Overall Match Winner: {overall_winner}!")

    finally:
        # Close the connection
        cursor.close()
        connection.close()
