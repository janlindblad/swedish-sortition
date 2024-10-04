# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

import sys, logging
logger = logging.getLogger("swedish_sortition")

def get_representative_answers(assembly_name):
  if assembly_name in ['boras24.0','boras24.1', 'boras24.2']:
    return {
      "gender": {
        "values": { "Man": 48.92, "Kvinna": 48.58, "Annat": 2.50 },
        "weight": 1
      },
      "age_group": {
        "values": { "16-19 år": 5487, "20-29 år": 14728, "30-39 år": 16190, "40-49 år": 13959,
                    "50-64 år": 20405, "65- år": 22366 },
        "weight": 1
      },
      "education": {
        "values": {
          "Högskola mer än 3 år": 20.64,
          "Högskola": 15.42,
          "Gymnasium": 45.12,
          "Grundskola": 18.82
        },
        "weight": 1
      },
      "geography": {
        "values": {
          "VDFS": 6512+11270+10579+9593, # Viskafors, Dalsjöfors, Fristad, Sandhult
          "GNS": 12532+13278+9803, # Göta, Norrby, Sjöbo
          "BCT": 12466+16171+12108, # Brämhult, Centrum, Trandared
        },
        "weight": 1
      },
      "occupation": {
        "values": {
          "Går i skola / trainee / arbetsträning": 12.83,
          "Arbete i kommun / region / stat": 17.28,
          "Arbete i företag / näringsliv": 39.00,
          "Annat arbete / ideell organisation": 1.17+0.17,
          "Pensionär": 23.29,
          "Arbestslös / Annat": 6.26, # sic! Felstavat i formuläret
        },
        "weight": 1
      },
      "climate_worry": {
        "values": {
          "Mycket orolig.": 50,
          "Ganska orolig.": 35,
          "Inte särskilt orolig.": 13,
          "Inte alls orolig.": 2
        },
        "weight": 1
      }
    }
  else:
    logger.error(f"No known criteria for assembly named {assembly_name}")
    sys.exit(9)

def map_answer(assembly_name, mapping, map_row, val):
  if assembly_name in ['boras24.0', 'boras24.1','boras24.2']:
    if mapping == 0: # Can attend? # Approves conditions?
      if not val or not val.startswith("Ja"):
        logger.info(f"Candidate {map_row['first_name']} {map_row['last_name']} has declined to particpate")
        return "skip"
      return "ok"
    elif mapping == 1: # Phone number used as id number
      map_row['personnummer'] = val.replace("'", "").replace("+","")
      return "ok"
    elif mapping == 2: # District
      if val in ['Viskafors', 'Dalsjöfors', 'Fristad', 'Sandhult']:
        map_row['geography'] = 'VDFS'
      elif val in ['Göta', 'Norrby', 'Sjöbo']:
        map_row['geography'] = 'GNS'
      elif val in ['Brämhult', 'Centrum', 'Trandared']:
        map_row['geography'] = 'BCT'
      else:
        logger.error(f"ERROR: unknown district for input row {map_row}")
        sys.exit(9)
      return "ok"
    logger.error(f"Broken translation mapping for input row {map_row}")
    sys.exit(9)
  logger.error(f"No known answers for assembly named {assembly_name}")
  sys.exit(9)
