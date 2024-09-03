# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

def get_representative_answers(assembly_name):
  if assembly_name in ['malmö24']:
    return {
      "gender": {
        "values": { "Man": 48.36, "Kvinna": 49.14, "Annat": 2.50 },
        "weight": 1
      },
      "age_group": {
        "values": { "16-19 år": 14992, "20-29 år": 52838, "30-39 år": 65033, "40-49 år": 49114,
                    "50-64 år": 57089, "65- år": 55022 },
        "weight": 1
      },
      "education": {
        "values": {
          "Högskola mer än 3 år": 31.07,
          "Högskola": 16.78,
          "Gymnasium": 32.30,
          "Grundskola": 19.85
        },
        "weight": 1
      },
      "geography": {
        "values": {
          "RFH": 23206+46274+42979, # 'Rosengård', 'Fosie', 'Hyllie'
          "SIK": 35857+16575, # 'Södra Innerstaden', 'Kirseberg'
          "OVIC": 14418+35616+60589, # 'Oxie', 'Västra Innerstaden', 'Centrum'
          "HLB": 42979+60537 # 'Husie', 'Limhamn-Bunkeflo'
        },
        "weight": 1
      },
      "occupation": {
        "values": {
          "Går i skola / trainee / arbetsträning": 15.54,
          "Arbete i kommun / region / stat": 16.80,
          "Arbete i företag / näringsliv": 36.94,
          "Annat arbete / ideell organisation": 4.21,
          "Pensionär": 18.41,
          "Arbestslös / Annat": 8.09, # sic! Felstavat i formuläret
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
    return None
def map_answer(mapping, map_row, val):
  if mapping == 0: # Can attend?
    if not val.startswith("Ja"):
      return "skip"
    return "ok"
  elif mapping == 1: # Phone number used as id number
    map_row['personnummer'] = val.replace("'", "")
    return "ok"
  elif mapping == 2: # District
    if val in ['Rosengård', 'Fosie', 'Hyllie']:
      map_row['geography'] = 'RFH'
    elif val in ['Södra innerstaden', 'Kirseberg']:
      map_row['geography'] = 'SIK'
    elif val in ['Oxie', 'Västra innerstaden', 'Centrum']:
      map_row['geography'] = 'OVIC'
    elif val in ['Husie', 'Limhamn - Bunkeflo']:
      map_row['geography'] = 'HLB'
    else:
      print(f"ERROR: unknown district for input row {row}")
      return "error"
    return "ok"
  return "error"