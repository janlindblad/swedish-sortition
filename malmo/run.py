#!/usr/bin/env python3
# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

# Import Python libraries
import csv, json, sys, math
from swedish_sortition import Sortition
import pandas as pd
from questions import get_questions, check_duplicates
from answers import get_representative_answers, map_answer

# Filenames
def get_citeria_filename(assembly_name, size):
  return f'criteria-{assembly_name}-{size}.json'

def get_canidates_filename(assembly_name):
  return f'candidates-{assembly_name}.csv'

def get_pool_filename(assembly_name, cat_name, confirmed=False):
  confirmed='-confirmed' if confirmed else ''
  return f'cat-{assembly_name}-pool-{cat_name}{confirmed}.csv'

# Pool creation
def get_pool_fields():
  return [
    'first_name','last_name','personnummer','age','age_group',
    'gender','address','phone_numbers','latitude','longitude',
    'geography','street','postcode','city','region','occupation',
    'housing_type','area_median_income','income_indicator',
    'education','climate_worry','is_confirmed'
  ]

def prepare_pool(assembly_name, input_filename, output_filename, 
                 incl_ids = [], excl_ids = [], check_dups=False):
  question_map = get_questions(assembly_name)
  with open(input_filename, newline='') as infile:
    with open(output_filename, "w", newline='') as outfile:
      poolreader = csv.reader(infile)
      poolwriter = csv.DictWriter(outfile, fieldnames=get_pool_fields())
      poolwriter.writeheader()
      num_pool_participants = 0
      for row in poolreader:
        map_row = {}
        map_row['is_confirmed'] = False
        row_valid = True
        if row[0] == '#':
          continue
        if check_dups:
          check_duplicates(assembly_name, row)
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
              report_error(f"Broken translation mapping for input row {row}")
          else:
            report_error(f"Broken mapping for input row {row}")
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
    report_info(f"Added {num_pool_participants} participants to {output_filename}")
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

  report_info(f"Created criteria file for {assembly_size} participants")

def run_selection(assembly_name, assembly_size, draw_iterations, result_file_stem):
  report_info(f'Running {draw_iterations} random participant draws')

  # Load pools of candidates in Cat A and B
  # These files can be generated test data or real candidate lists
  report_info("Reading pool files for Cat A and B")
  pool_a = pd.read_csv(get_pool_filename(assembly_name, 'a'))
  pool_b = pd.read_csv(get_pool_filename(assembly_name, 'b'))

  # Pick Cat A participants (which must be equal to all candidates)
  already_confirmed_participants = pd.DataFrame(pool_a)
  report_info(f"A: Already confirmed participants: {already_confirmed_participants.is_confirmed.count()[True][0]}")

  # Split Cat B candidates into already confirmed participants and candidates.
  # The first time we run this, there will be no confirmed participants,
  # But if we need to run this again later because we need to add more
  # candidates, the previously confirmed candidates will be marked as confirmed

  try:
    cat_b_candidates, cat_b_participants = [part[1] for part in pool_b.groupby('is_confirmed')]
    already_confirmed_participants = pd.concat([already_confirmed_participants, cat_b_participants])
    report_info("Some Cat B candidates already confirmed")
  except:
    # No confirmed candidates, so all of pool B are just candidates
    cat_b_candidates = [part[1] for part in pool_b.groupby('is_confirmed')][0]
    report_info("No Cat B candidates already confirmed")

  #print(f"Pool B\n{pool_b}")
  #print(f"Candidates B\n{cat_b_candidates}")
  report_info(f"AB: Already confirmed participants: {already_confirmed_participants.shape[0]}")

  # Load file with local population profile, to match in coming draws
  # Note: The numbers in this file need to match the total 
  #       number of participants
  criteria_filename = get_citeria_filename(assembly_name, assembly_size)
  report_info(f"Reading criteria file {criteria_filename}")
  with open(criteria_filename) as f:
      criteria = json.load(f)

  report_info(f"{already_confirmed_participants.shape[0]} participants already confirmed")
  report_info(f"{assembly_size} participants to be selected")
  sortition = Sortition(criteria, assembly_size)
  sortition.generate_samples(draw_iterations, result_file_stem, cat_b_candidates, already_confirmed_participants)

def generate_confirmed_pool_file(xlsx_filename, source_pool_filename,
                                 target_pool_filename=None):
  if not target_pool_filename:
    target_pool_filename = source_pool_filename.replace(".csv", "-confirmed.csv")
  with open(target_pool_filename, "w", newline='') as outfile:
    sortition_result = pd.read_excel(xlsx_filename)
    pool = pd.read_csv(source_pool_filename)
    all_confirmed = pool.copy()
    all_confirmed.is_confirmed = True
    for index, row in sortition_result.iterrows():
      # Update pool so that is_confirmed == True on entries that match
      # none of the conditions
      if row.is_confirmed:
        # Already confirmed, no need to do anything
        continue
      pool_confirmed_pre = pool.is_confirmed.value_counts().get(True,0)
      pool.where(~((pool.first_name==row.first_name) & 
                   (pool.last_name==row.last_name) & 
                   (pool.personnummer==row.personnummer) & 
                   (pool.address==row.address)), all_confirmed, inplace=True)
      pool_confirmed_post = pool.is_confirmed.value_counts().get(True,0)
      if pool_confirmed_post - pool_confirmed_pre != 1:
        report_warning(f'{row.first_name}, {row.last_name}, {row.personnummer}, {row.address} matched {pool_confirmed_post - pool_confirmed_pre} candidates')
    pool_size = pool.shape[0]
    pool_confirmed = pool.is_confirmed.value_counts()[True]
    pool.to_csv(outfile, index=False)
    report_info(f'Wrote confirmed pool file {target_pool_filename} with {pool_confirmed}/{pool_size} confirmed candidates')

def report_error(msg):
  print(f"ERROR: {msg}")
  sys.exit(1)

def report_warning(msg):
  print(f"WARNING: {msg}")

def report_progress(msg):
  print(f">>> {msg}")

def report_info(msg):
  print(f"{msg}")

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
                    default="participant",
                    help="name stem of the result files")
  parser.add_option("-i", type="int", dest="draw_iterations",
                    default=0,
                    help="number of random draws")
  parser.add_option("-c", type="str", dest="participant_file",
                    help="Generate confirmed candidate file from participant file")
  (options, args) = parser.parse_args()

  if not options.assembly_name:
    report_error("Need to specify an assembly event name, -n")

  if options.cat_a_ids:
    # Create pools, parse pool A participant id:s
    report_progress(f'Creating new pools')
    input_filename = get_canidates_filename(options.assembly_name)

    cat_a_size = len(options.cat_a_ids)
    cat_a_participant_ids = []
    if options.cat_a_ids != ["none"]:
      cat_a_participant_ids = [tuple(id.split(':')) for id in options.cat_a_ids]

    # Create pool A
    cat_a_filename = get_pool_filename(options.assembly_name, 'a')
    cat_a_size = prepare_pool(options.assembly_name, input_filename, cat_a_filename, incl_ids=cat_a_participant_ids, check_dups=True)
    report_info(f'Created new pool {cat_a_filename} with {cat_a_size} participants')

    # Create pool B
    cat_b_filename = get_pool_filename(options.assembly_name, 'b')
    cat_b_size = prepare_pool(options.assembly_name, input_filename, cat_b_filename, excl_ids=cat_a_participant_ids)
    report_info(f'Created new pool {cat_a_filename} with {cat_b_size} participants')

  # Check if pool files already exist and and make sense
  pool_a = pd.DataFrame(pd.read_csv(get_pool_filename(options.assembly_name, 'a')))
  cat_a_size = pool_a.shape[0] # Number of candidates
  pool_b = pd.DataFrame(pd.read_csv(get_pool_filename(options.assembly_name, 'b')))
  cat_b_size = pool_b.shape[0] # Number of candidates
  report_info(f'Using candidate pools:')
  report_info(f'+ {get_pool_filename(options.assembly_name, "a")} with {cat_a_size} candidates')
  report_info(f'+ {get_pool_filename(options.assembly_name, "b")} with {cat_b_size} candidates')
  if options.assembly_size and options.assembly_size > cat_a_size + cat_b_size:
    report_error("Assembly size is larger than the number of candidates")

  # Prepare criteria file
  if options.assembly_size:
    report_progress(f'Creating new criteria file')
    prepare_criteria(options.assembly_name, options.assembly_size)

  # Run the main sortition
  if options.draw_iterations:
    report_progress(f'Starting sortition')
    run_selection(options.assembly_name, options.assembly_size, options.draw_iterations, options.result_file_stem)
    report_progress(f'Sortition completed')
    report_info(f'Sortition result in files {options.result_file_stem}*.xlsx')

  # Generate a confirmed participant pool file
  if options.participant_file:
    report_progress(f'Generating confirmed participants pool file')
    generate_confirmed_pool_file(options.participant_file, get_pool_filename(options.assembly_name, "b"))

main()