from auth.signin import sign_in
from auth.signup import sign_up
from modes.quick_game import quick_game
from modes.quick_match import quick_match
from tournament.start_tournament import start_tournament
from tournament.continue_tournament import play_or_manage_matches
from tournament.statistics import view_tournament_details, view_tournament_match_details, view_tournament_players_details
from tournament.statistics import plot_matches_won, plot_match_completion_status


def main():
    while True:
        print("\n--- Badminton Tourney Organizer ---")
        print("1. Sign-Up")
        print("2. Sign-In")
        print("3. Exit")

        option = input("Choose an option: ").strip()

        if option == "1":
            sign_up()
        elif option == "2":
            user_id = sign_in()
            if user_id:
                while True:
                    print("\n--- Game Modes ---")
                    print("1. Quick Game")
                    print("2. Quick Match")
                    print("3. Tournament Mode")
                    print("4. Log Out")

                    mode = input("Choose an option: ").strip()
                    if mode == "1":
                        quick_game(user_id)
                    elif mode == "2":
                        quick_match(user_id)
                    elif mode == "3":
                        tournament_menu(user_id)
                    elif mode == "4":
                        confirm = input("Are you sure you want to log out? (Yes/No): ").strip().lower()
                        if confirm == 'yes':
                            break
                    else:
                        print("Invalid option. Please try again.")
            else:
                print("Returning to main menu...")
        elif option == "3":
            confirm = input("Are you sure you want to exit? (Yes/No): ").strip().lower()
            if confirm == 'yes':
                print("Goodbye!")
                break
        else:
            print("Invalid option. Try again.")

def tournament_menu(user_id):
    while True:
        print("\n--- Tournament Menu ---")
        print("1. Start Tournament")
        print("2. Continue Tournament")
        print("3. View Statistics (CLI)")
        print("4. Statistics (GUI)")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print("Starting tournament...")
            start_tournament(user_id)
        elif choice == "2":
            print("Continuing tournament...")
            play_or_manage_matches(user_id)
        elif choice == "3":
            print("\n--- View Statistics (CLI) ---")
            print("1. View Tournament Details")
            print("2. View Tournament Player Details")
            print("3. View Tournament Matches Details")
            cli_choice = input("Enter your choice: ").strip()
            if cli_choice == "1":
                view_tournament_details(user_id)
            elif cli_choice == "2":
                view_tournament_players_details(user_id)
            elif cli_choice == '3':
                view_tournament_match_details(user_id)                
            else:
                print("Invalid choice. Try again.")
        elif choice == "4":
            print("\n--- Statistics (GUI) ---")
            print("1. Wins by Player/Team")
            print("2. Match Status Distribution")
            gui_choice = input("Enter your choice: ").strip()

            if gui_choice == "1":
                tourney_id = input("Enter Tournament ID: ").strip()
                category = input("Enter Category: ").strip()
                mode = input("Enter Mode (Singles/Doubles): ").strip()
                plot_matches_won(tourney_id, category, mode, user_id)
            
            elif gui_choice == "2":
                tourney_id = input("Enter Tournament ID: ").strip()
                category = input("Enter Category: ").strip()
                mode = input("Enter Mode (Singles/Doubles): ").strip()
                plot_match_completion_status(tourney_id, category, mode, user_id)
 
            else:
                print("Invalid choice. Try again.")
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
