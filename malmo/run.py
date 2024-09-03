#!/usr/bin/env python3
# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

# Import Python libraries
import csv, json, sys, math, operator
from swedish_sortition import Sortition
import pandas as pd
from questions import get_questions, check_duplicates
from answers import get_representative_answers, map_answer

# Filenames
def get_citeria_filename(assembly_name, size):
  return f'criteria-{assembly_name}-{size}.json'

def get_canidate_filename(assembly_name):
  return f'candidates-{assembly_name}.csv'

def get_pool_filename(cat_name):
  return f'cat-{cat_name}-pool.csv'

# Pool creation
def prepare_pool(assembly_name, input_filename, output_filename, 
                 incl_ids = [], excl_ids = [], check_dups=False):
  pool_fields = [
    'first_name','last_name','personnummer','age','age_group',
    'gender','address','phone_numbers','latitude','longitude',
    'geography','street','postcode','city','region','occupation',
    'housing_type','area_median_income','income_indicator',
    'education','climate_worry','is_confirmed'
  ]
  question_map = get_questions(assembly_name)
  
  with open(input_filename, newline='') as infile:
    with open(output_filename, "w", newline='') as outfile:
      poolreader = csv.reader(infile)
      poolwriter = csv.DictWriter(outfile, fieldnames=pool_fields)
      poolwriter.writeheader()
      num_pool_participants = 0
      for row in poolreader:
        map_row = {}
        map_row['is_confirmed'] = False
        row_valid = True
        if row[0] == '#':
          continue
        if check_dups:
          check_duplicates(row)
        for num,key in enumerate(question_map):
          mapping = question_map[key]
          val = row[num]
          #print(num, key, val, mapping, row)
          if mapping == None:
            continue
          elif isinstance(mapping, str):
            map_row[mapping] = val
          elif isinstance(mapping, int):
            ret = map_answer(mapping, map_row, val)
            if ret == "ok":
              pass
            elif ret == "skip":
              row_valid = False
              break
            elif ret == "error":
              error(f"Broken translation mapping for input row {row}")
          else:
            error(f"Broken mapping for input row {row}")
        if not row_valid:
          continue
        individual = (map_row['first_name'], map_row['last_name'], map_row['personnummer'])
        if incl_ids:
          if individual in incl_ids:
            map_row['is_confirmed'] = True
          else:
            continue
        if individual in excl_ids:
          continue
        num_pool_participants += 1
        poolwriter.writerow(map_row)
    print(f"Added {num_pool_participants} participants to {output_filename}")
    return num_pool_participants

def prepare_criteria(assembly_name, assembly_size):
  # Prepare criteria file
  # data from https://docs.google.com/spreadsheets/d/17o0X_hj38BVVE-OSz259AkoJoUjcoV8h/edit?gid=86822401#gid=86822401
  criteria_filename = get_citeria_filename(assembly_name, assembly_size)
  criteria = get_representative_answers(assembly_name)

  #print(f'Assembly size {assembly_size}:')
  for cat in criteria:
    vals = criteria[cat]["values"]
    value_sum = sum(vals.values())
    new_vals = {}
    for key in vals.keys():
      new_vals[key] = int(math.floor(vals[key] / value_sum * assembly_size))
    #print(f'Floor {cat} values {sum(new_vals.values())}: {new_vals}')
    while int(sum(new_vals.values())) != assembly_size:
      rel_diff = {key:(vals[key]/value_sum*assembly_size - new_vals[key]) for key in vals.keys()}
      best_fit_key = max(rel_diff, key=rel_diff.get)
      #print(f'Adjusted {best_fit_key}')
      new_vals[best_fit_key] += 1
    criteria[cat]["values"] = new_vals
    #print(f'Final {cat} values {sum(new_vals.values())}: {new_vals}')
  with open(criteria_filename, "w", newline='') as critfile:
    print(json.dumps(criteria), file=critfile)

  print(f"Created criteria file for {assembly_size} participants")

def run_selection(assembly_name, assembly_size, draw_iterations, result_file_stem):
  print(f'Running {draw_iterations} random participant draws')

  # Load pools of candidates in Cat A and B
  # These files can be generated test data or real candidate lists
  print("Reading pool files for Cat A and B")
  pool_a = pd.read_csv(get_pool_filename('a'))
  pool_b = pd.read_csv(get_pool_filename('b'))

  # Pick Cat A participants (which must be equal to all candidates)
  already_confirmed_participants = pd.DataFrame(pool_a)
  print(f"A: Already confirmed participants: {already_confirmed_participants.is_confirmed.count()[True][0]}")

  # Split Cat B candidates into already confirmed participants and candidates.
  # The first time we run this, there will be no confirmed participants,
  # But if we need to run this again later because we need to add more
  # candidates, the previously confirmed candidates will be marked as confirmed

  try:
    cat_b_candidates, cat_b_participants = [part[1] for part in pool_b.groupby('is_confirmed')]
    already_confirmed_participants = pd.concat([already_confirmed_participants, cat_b_participants])
    print("Some Cat B candidates already confirmed")
  except:
    # No confirmed candidates, so all of pool B are just candidates
    cat_b_candidates = [part[1] for part in pool_b.groupby('is_confirmed')][0]
    print("No Cat B candidates already confirmed")

  #print(f"Pool B\n{pool_b}")
  #print(f"Candidates B\n{cat_b_candidates}")
  print(f"AB: Already confirmed participants: {already_confirmed_participants.shape[0]}")

  # Load file with local population profile, to match in coming draws
  # Note: The numbers in this file need to match the total 
  #       number of participants
  criteria_filename = get_citeria_filename(assembly_name, assembly_size)
  print(f"Reading criteria file {criteria_filename}")
  with open(criteria_filename) as f:
      criteria = json.load(f)

  print("\nStarting selection process")
  print(f"{already_confirmed_participants.shape[0]} participants already confirmed")
  print(f"{assembly_size} participants to be selected")
  sortition = Sortition(criteria, assembly_size)
  sortition.generate_samples(draw_iterations, result_file_stem, cat_b_candidates, already_confirmed_participants)

def error(msg):
  print(f"ERROR: {msg}")
  sys.exit(1)

def main():
  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("-n", type="str", dest="assembly_name",
                    help="name of the event")
  parser.add_option("-a", type="str", dest="cat_a_ids",
                    action="append",
                    help="Cat A participant ids fname:lname:phone")
  parser.add_option("-s", type="int", dest="assembly_size",
                    help="desired number of participants")
  parser.add_option("-r", type="str", dest="result_file_stem",
                    default="particpant",
                    help="name stem of the result files")
  parser.add_option("-i", type="int", dest="draw_iterations",
                    default=0,
                    help="number of random draws")
  (options, args) = parser.parse_args()

  if not options.assembly_name:
    error("Need to specify an assembly event name, -n")

  if not options.assembly_size:
    error("Need to specify an assembly size, -s")

  # Create or check pools
  if not options.cat_a_ids:
    # Check if a cat_a_pool file already exists
    pool_a = pd.DataFrame(pd.read_csv(get_pool_filename('a')))
    cat_a_size = pool_a.shape[0] # Number of participants
    pool_b = pd.DataFrame(pd.read_csv(get_pool_filename('b')))
    cat_b_size = pool_b.shape[0] # Number of participants
    print(f'Using existing pools with participants')
    print(f'+ {get_pool_filename("a")} with {cat_a_size} participants')
    print(f'+ {get_pool_filename("b")} with {cat_b_size} participants')
  else:
    cat_a_size = len(options.cat_a_ids)
    cat_a_participant_ids = [tuple(id.split(':')) for id in options.cat_a_ids]
    input_filename = get_canidate_filename(options.assembly_name)
    cat_a_filename = get_pool_filename('a')
    cat_a_size = prepare_pool(options.assembly_name, input_filename, cat_a_filename, incl_ids=cat_a_participant_ids, check_dups=True)
    print(f'Created new pool {get_pool_filename("a")} with {cat_a_size} participants')

    cat_b_filename = get_pool_filename('b')
    cat_b_size = prepare_pool(options.assembly_name, input_filename, cat_b_filename, excl_ids=cat_a_participant_ids)
    print(f'Created new pool {get_pool_filename("b")} with {cat_b_size} participants')

  if options.assembly_size > cat_a_size + cat_b_size:
    error("Assembly size is larger than the number of participants")

  # Prepare criteria file
  prepare_criteria(options.assembly_name, options.assembly_size)

  # Run the main sortition
  if options.draw_iterations:
    run_selection(options.assembly_name, options.assembly_size, options.draw_iterations, options.result_file_stem)

main()
