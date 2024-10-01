# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

import sys, csv, logging, warnings
import pandas as pd
from questions import get_questions, check_duplicates
from answers import get_representative_answers, map_answer
logger = logging.getLogger("swedish_sortition")

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
  with open(output_filename, "w", newline='') as outfile:
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      poolreader = pd.read_excel(input_filename)
    poolwriter = csv.DictWriter(outfile, fieldnames=get_pool_fields())
    poolwriter.writeheader()
    num_pool_participants = 0
    for rownum, row in poolreader.iterrows():
      map_row = {}
      map_row['is_confirmed'] = False
      row_valid = True
      if check_dups:
        check_duplicates(assembly_name, row)
      for num,key in enumerate(question_map):
        mapping = question_map[key]
        val = list(row)[num]
        if mapping == None:
          continue
        elif isinstance(mapping, str):
          map_row[mapping] = val
        elif isinstance(mapping, int):
          ret = map_answer(assembly_name, mapping, map_row, val)
          if ret == "ok":
            pass
          elif ret == "skip":
            row_valid = False
            break
          elif ret == "error":
            logger.error(f"Broken translation mapping for input row {row}")
            sys.exit(9)
        else:
          logger.error(f"Broken mapping for input row {row}")
          sys.exit(9)
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
  return num_pool_participants
