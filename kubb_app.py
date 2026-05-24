# --- SETUP ---
if df.empty or "Team A" not in df.columns:
    st.header("Tournament Setup (1 Court)")
    team_input = st.text_area("Enter Team Names (one per line):")
    
    if st.button("🚀 Launch Tournament"):
        teams = [t.strip() for t in team_input.split('\n') if t.strip()]
        if len(teams) < 4:
            st.error("Enter at least 4 teams.")
        else:
            t_list = list(teams)
            # Ensure even number of teams for the math to work
            if len(t_list) % 2 != 0: 
                t_list.append("BYE")
            
            n = len(t_list)
            all_matches = []
            
            # Generate 3 Rounds of play
            for r in range(3):
                for i in range(n // 2):
                    team_a = t_list[i]
                    team_b = t_list[n - 1 - i]
                    
                    # Only add the match if it's not against a "BYE"
                    if team_a != "BYE" and team_b != "BYE":
                        all_matches.append({
                            "Game": len(all_matches) + 1,
                            "Team A": team_a,
                            "Team B": team_b,
                            "Winner": "None"
                        })
                
                # The "Circle" Rotation: Keep first team fixed, rotate others
                t_list = [t_list[0]] + [t_list[-1]] + t_list[1:-1]
            
            # Convert to DataFrame and sync
            master_df = pd.DataFrame(all_matches).astype(str)
            update_sheet(master_df)
            st.rerun()
