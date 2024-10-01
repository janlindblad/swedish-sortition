#!/usr/bin/env python3
# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

# Import Python libraries
import json, sys, math, logging
from swedish_sortition import Sortition
import pandas as pd
from pool import prepare_pool
from answers import get_representative_answers
logger = logging.getLogger("swedish_sortition")

# Filenames
def get_citeria_filename(assembly_name, size):
  return f'criteria-{assembly_name}-{size}.json'

def get_pool_filename(assembly_name, confirmed=False):
  confirmed='-confirmed' if confirmed else ''
  return f'pool-{assembly_name}{confirmed}.csv'

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

  logger.info(f"Created criteria file for {assembly_size} participants")

def run_selection(assembly_name, assembly_size, draw_iterations, result_file_stem):
  logger.info(f'Running {draw_iterations} random participant draws')

  # Load pools of candidates
  logger.info("Reading pool file")
  pool = pd.read_csv(get_pool_filename(assembly_name))

  # Split candidates into already confirmed participants and candidates.
  
  try:
    pool_candidates, pool_participants = [part[1] for part in pool.groupby('is_confirmed')]
    logger.info("Some candidates already confirmed")
  except:
    # No confirmed candidates
    pool_candidates = [part[1] for part in pool.groupby('is_confirmed')][0]
    pool_participants = []
    logger.info("No candidates already confirmed")

  #print(f"Pool\n{pool}")
  #print(f"Candidates\n{pool_candidates}")
  logger.info(f"Already confirmed participants: {pool_participants.shape[0]}")

  # Load file with local population profile, to match in coming draws
  # Note: The numbers in this file need to match the total 
  #       number of participants
  criteria_filename = get_citeria_filename(assembly_name, assembly_size)
  logger.info(f"Reading criteria file {criteria_filename}")
  with open(criteria_filename) as f:
      criteria = json.load(f)

  logger.info(f"{pool_participants.shape[0]} participants already confirmed")
  logger.info(f"{assembly_size} participants to be selected")
  sortition = Sortition(criteria, assembly_size)
  sortition.generate_samples(draw_iterations, result_file_stem, pool_candidates, pool_participants)

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
                   (pool.personnummer==row.personnummer) #& 
                   #(pool.address==row.address)
                   ), all_confirmed, inplace=True)
      pool_confirmed_post = pool.is_confirmed.value_counts().get(True,0)
      if pool_confirmed_post - pool_confirmed_pre != 1:
        logger.warning(f'{row.first_name}, {row.last_name}, {row.personnummer}, {row.address} matched {pool_confirmed_post - pool_confirmed_pre} candidates')
    pool_size = pool.shape[0]
    pool_confirmed = pool.is_confirmed.value_counts()[True]
    pool.to_csv(outfile, index=False)
    logger.info(f'Wrote confirmed pool file {target_pool_filename} with {pool_confirmed}/{pool_size} confirmed candidates')

def main():
  logging.basicConfig(level=logging.INFO)
  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("-n", type="str", dest="assembly_name",
                    help="name of the event")
  parser.add_option("-p", type="str", dest="initial_pool_filename",
                    help="pool filename")
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
    logger.error("Need to specify an assembly event name, -n")
    sys.exit(9)

  if options.initial_pool_filename:
    # Create candidate pool file
    logger.info(f'Creating new pool file')
    pool_filename = get_pool_filename(options.assembly_name)
    pool_size = prepare_pool(options.assembly_name, options.initial_pool_filename, pool_filename, check_dups=True)
    logger.info(f"Placed {pool_size} participants into {pool_filename}")

  # Check if pool file already exists and and makes sense
  pool = pd.DataFrame(pd.read_csv(get_pool_filename(options.assembly_name)))
  pool_size = pool.shape[0] # Number of candidates
  logger.info(f'Using candidate pool {get_pool_filename(options.assembly_name)} with {pool_size} candidates')
  if options.assembly_size and options.assembly_size > pool_size:
    logger.error("Assembly size is larger than the number of candidates")
    sys.exit(9)

  # Prepare criteria file
  if options.assembly_size:
    logger.info(f'Creating new criteria file')
    prepare_criteria(options.assembly_name, options.assembly_size)

  # Run the main sortition
  if options.draw_iterations:
    logger.info(f'Starting sortition')
    run_selection(options.assembly_name, options.assembly_size, options.draw_iterations, options.result_file_stem)
    logger.info(f'Sortition completed')
    logger.info(f'Sortition result in files {options.result_file_stem}*.xlsx')

  # Generate a confirmed participant pool file
  if options.participant_file:
    logger.info(f'Generating confirmed participants pool file')
    generate_confirmed_pool_file(options.participant_file, get_pool_filename(options.assembly_name))

main()