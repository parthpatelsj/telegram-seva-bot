import pandas as pd
import json

def standardize_breakouts():
    # Read both files
    ebreakouts = pd.read_csv('ebreakouts.csv')
    ibreakouts = pd.read_csv('ibreakouts.csv')
    
    # Function to standardize a row
    def standardize_row(row, is_ibky=False):
        if is_ibky:
            return {
                'First Name': str(row['First Name']),
                'Last Name': str(row['Last Name']),
                'Center': str(row['Center']),
                'Primary Seva': str(row['Primary Seva']),
                'Type': 'iBKY',
                'Breakout1_Session': str(row['Breakout #1 10:30am-12pm']),
                'Breakout1_Room': str(row['Breakout Room 1']),
                'Breakout1_Time': '10:30am-12pm',
                'Breakout2_Session': str(row['Breakout #2 6pm-7:30pm']),
                'Breakout2_Room': str(row['Breakout Room 2']),
                'Breakout2_Time': '6:00-7:30pm',
                'Breakout3_Session': '',
                'Breakout3_Room': '',
                'Breakout3_Time': '8:45-9:45pm',
                'Center_Planning_Session': str(row['Center Analysis 4:30-6pm']),
                'Center_Planning_Room': '',
                'Center_Planning_Time': '4:30-6:00pm',
                'Ghoshti_Session': str(row['Goshti 3:15-4pm']),
                'Ghoshti_Room': '',
                'Ghoshti_Time': '3:15-4:00pm'
            }
        else:
            # Handle the specific column names for ebreakouts
            return {
                'First Name': str(row['First Name']),
                'Last Name': str(row['Last Name']),
                'Center': str(row['Center']),
                'Primary Seva': str(row['Primary Seva']),
                'Type': 'eBKY',
                'Breakout1_Session': str(row['Breakout #1 (10:30 - 12:00)']),
                'Breakout1_Room': str(row['Room Number']),
                'Breakout1_Time': '10:30am-12pm',
                'Breakout2_Session': str(row['Breakout #2 (6:00 - 7:30)']),
                'Breakout2_Room': str(row['Room Number.1'] if 'Room Number.1' in row else row['Room Number']),
                'Breakout2_Time': '6:00-7:30pm',
                'Breakout3_Session': str(row['Breakout #3 (8:45 - 9:45)']),
                'Breakout3_Room': str(row['Room Number.2'] if 'Room Number.2' in row else ''),
                'Breakout3_Time': '8:45-9:45pm',
                'Center_Planning_Session': str(row['Center Planning (4:30 - 6:00)']),
                'Center_Planning_Room': str(row['Room Number.3'] if 'Room Number.3' in row else ''),
                'Center_Planning_Time': '4:30-6:00pm',
                'Ghoshti_Session': str(row['Ghosthi Group (3:15 - 4:00)']),
                'Ghoshti_Room': str(row['Room Number.4'] if 'Room Number.4' in row else ''),
                'Ghoshti_Time': '3:15-4:00pm'
            }

    # Process each file
    print("Processing ebreakouts...")
    e_rows = [standardize_row(row) for _, row in ebreakouts.iterrows()]
    print(f"Processed {len(e_rows)} ebreakout rows")

    print("Processing ibreakouts...")
    i_rows = [standardize_row(row, True) for _, row in ibreakouts.iterrows()]
    print(f"Processed {len(i_rows)} ibreakout rows")
    
    # Combine and create DataFrame
    combined_df = pd.DataFrame(e_rows + i_rows)
    
    # Create a lookup index
    combined_df['lookup_key'] = combined_df.apply(
        lambda x: f"{x['First Name']}|{x['Last Name']}|{x['Center']}|{x['Primary Seva']}", 
        axis=1
    )
    
    # Save to CSV
    combined_df.to_csv('combined_breakouts.csv', index=False)
    print(f"Saved combined CSV with {len(combined_df)} total rows")
    
    # Save as JSON for faster lookups
    lookup_dict = combined_df.set_index('lookup_key').to_dict(orient='index')
    with open('breakouts_lookup.json', 'w') as f:
        json.dump(lookup_dict, f, indent=2)
    print("Saved JSON lookup file")

    # Print a few sample entries to verify
    print("\nSample entries from combined data:")
    print("\neBKY sample (Ravin Maru):")
    ravin = combined_df[
        (combined_df['First Name'] == 'Ravin') & 
        (combined_df['Last Name'] == 'Maru')
    ].to_dict('records')[0]
    print(json.dumps(ravin, indent=2))

    print("\niBKY sample (Mukti Patel):")
    ashka = combined_df[
        (combined_df['First Name'] == 'Mukti') & 
        (combined_df['Last Name'] == 'Patel')
    ].to_dict('records')[0]
    print(json.dumps(ashka, indent=2))

    return combined_df

if __name__ == "__main__":
    standardize_breakouts()