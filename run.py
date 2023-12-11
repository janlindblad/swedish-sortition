# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

# Set number of participants in each participant category
AMOUNT_CAT_A_PARTICIPANTS = 5
AMOUNT_CAT_B_PARTICIPANTS = 10
AMOUNT_CAT_C_PARTICIPANTS = 25
AMOUNT_CAT_C_RESERVE_PARTICIPANTS = 10

# If SIMULATION is True, we will generate fake candidate lists
# as part of the run
SIMULATION = True

# Import Python libraries
from services.fake_data_generator import get_random_people, confirm_certain
import services.writer as writer
import json
from swedish_sortition import Sortition
import pandas as pd

if SIMULATION:
    # Set number of simulated candidates to create
    AMOUNT_CAT_B_CANDIDATES = 36
    AMOUNT_CAT_C_CANDIDATES = 110

    # Create a file with all Cat A candidates
    print("Generating simulated Cat A Pool")
    cat_a_pool = get_random_people(AMOUNT_CAT_A_PARTICIPANTS)
    # Mark all candidates as confirmed participants
    cat_a_pool = confirm_certain(cat_a_pool, AMOUNT_CAT_A_PARTICIPANTS)
    writer.write_csv(cat_a_pool, 'cat_a_pool.csv')

    # Create a file with all Cat B candidates
    print("Generating simulated Cat B Pool")
    cat_b_pool = get_random_people(AMOUNT_CAT_B_CANDIDATES)
    # Randomly mark some candidates as confirmed participants
    # This decides which Cat B candidates will participate
    cat_b_pool = confirm_certain(cat_b_pool, AMOUNT_CAT_B_PARTICIPANTS)
    writer.write_csv(cat_b_pool, 'cat_b_pool.csv')

    # Create a file with all Cat C candidates,
    # but do not mark any candidates as confirmed participants yet
    print("Generating simulated Cat C Pool")
    cat_c_pool = get_random_people(AMOUNT_CAT_C_CANDIDATES)
    # Add is_confirmed column, but don't makr any as confirmed
    cat_c_pool = confirm_certain(cat_c_pool, 0)
    writer.write_csv(cat_c_pool, 'cat_c_pool.csv')

    # Special code for Candidate simulation ends here

# Load pools of candidates in Cat A, B and C
# These files can be generated test data or real candidate lists
print("Reading pool files for Cat A, B and C")
pool_a = pd.read_csv('cat_a_pool.csv')
pool_b = pd.read_csv('cat_b_pool.csv')
pool_c = pd.read_csv('cat_c_pool.csv')

# Pick Cat A participants (which must be equal to all candidates)
already_confirmed_participants = pd.DataFrame(pool_a)
print(f"A: Already confirmed participants: {already_confirmed_participants.is_confirmed.count()[True][0]}")

# Pick Cat B participants (which are already marked as confirmed)
cat_b_waitinglist, cat_b_participants = [part[1] for part in pool_b.groupby('is_confirmed')]
if cat_b_participants.last_name.count() != AMOUNT_CAT_B_PARTICIPANTS:
    raise Exception(f"Wrong number of Category B participants: {cat_b_participants.last_name.count()} (actual) != {AMOUNT_CAT_B_PARTICIPANTS} (desired)")
already_confirmed_participants = pd.concat([already_confirmed_participants, cat_b_participants])
print(f"B: Already confirmed participants: {already_confirmed_participants.is_confirmed.count()[True][0]}")

# Split Cat C candidates into already confirmed participants and candidates.
# The first time we run this, there will be no confirmed participants,
# But if we need to run this again later because we need to add more
# candidates, the previously confirmed candidates will be marked as confirmed

#print(f"Pool B\n{pool_b}")
#print(f"Participants B\n{cat_b_participants}")
#print(f"Waitinglist B\n{cat_b_waitinglist}")

try:
    cat_c_candidates, cat_c_participants = [part[1] for part in pool_c.groupby('is_confirmed')]
    already_confirmed_participants = pd.concat([already_confirmed_participants, cat_c_participants])
    print("Some Cat C candidates already confirmed")
except:
    # No confirmed candidates, so all of pool C are just candidates
    cat_c_candidates = [part[1] for part in pool_c.groupby('is_confirmed')][0]
    print("No Cat C candidates already confirmed")

#print(f"Pool C\n{pool_c}")
#print(f"Candidates C\n{cat_c_candidates}")
print(f"C: Already confirmed participants: {already_confirmed_participants.shape[0]}")

# Load file with local population profile, to match in coming draws
# Note: The numbers in this file need to match the total 
#       number of participants
print("Reading criteria file")
with open('criteria.json') as f:
    criteria = json.load(f)

print("\nStarting selection process")
total_number_of_participants = AMOUNT_CAT_A_PARTICIPANTS + AMOUNT_CAT_B_PARTICIPANTS + AMOUNT_CAT_C_PARTICIPANTS
print(f"{already_confirmed_participants.shape[0]} participants already confirmed")
print(f"{total_number_of_participants} participants to be selected")
sortition = Sortition(criteria, total_number_of_participants)
#print(f"Cat C candidates\n{cat_c_candidates}")
sortition.generate_samples(10000, 'participants', cat_c_candidates, already_confirmed_participants)

