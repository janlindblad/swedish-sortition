# Klimatriksdagen sortition process
# Based on https://github.com/digidemlab/swedish-sortition
# Adapted by Jan Lindblad <jan.lindblad@protonmail.com>

import sys, logging
logger = logging.getLogger("swedish_sortition")

def get_questions(assembly_name):
  if assembly_name in ['boras24.0','boras24.1']:
    return {
      '#':None,
      'First name':'first_name',
      'Last name':'last_name',
      'Phone number':1,
      'Email':'address',
      "För att delta i rådslaget behöver du ha möjlighet att vara med vid fyra kvällsmöten och en rådslagshelg.":0,
      'Jag godkänner att mina personuppgifter samlas in av Klimatriksdagen för att användas inom ramen för klimatrådslaget.':0,
      'Hur många år är du?':'age_group',
      'Vilket kön identifierar du dig med?':'gender',
      'Vilken stadsdel bor du i?':2,
      'Vad är din högsta utbildning?':'education',
      'Vilket slags sysselsättning har du (mest)?':'occupation',
      'Hur orolig är du för klimatförändringar?':'climate_worry',
      'utm_source':None,
      'Response Type':None,
      'Start Date (UTC)':None,
      'Stage Date (UTC)':None,
      'Submit Date (UTC)':None,
      'Network ID':None,
      'Tags':None,
    }
  else:
    logger.error(f"No known questions for assembly named {assembly_name}")
    sys.exit(9)

emails = set()
phone_nums = set()
fl_names = set()
def check_duplicates(assembly_name, entry):
  if assembly_name in ['boras24.0','boras24.1']:
    messages = []
    email = entry['Email']
    if email in emails:
      messages += [f"email {email}"]
    emails.add(email)
    phone_num = entry['Phone number']
    if phone_num in phone_nums:
      messages += [f"phone number {phone_num}"]
    phone_nums.add(phone_num)
    fl_name = (entry['First name'], entry['Last name'])
    if fl_name in fl_names:
      messages += [f"first+last name {fl_name}"]
    fl_names.add(fl_name)
    if messages:
      logger.warning(f"WARNING: Entry with duplicate {', '.join(messages)}")
  else:
    logger.warning(f"WARNING: No duplicates check for {assembly_name}")
