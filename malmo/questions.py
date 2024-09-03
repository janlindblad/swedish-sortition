def get_questions(assembly_name):
  if assembly_name in ['malmö24']:
    return {
      '#':None, #0
      'First name':'first_name', #1
      'Last name':'last_name', #2
      'Phone number':1, #3
      'Email':'address', #4
      "För att delta i rådslaget behöver du ha möjlighet att vara med vid fyra kvällsmöten och en rådslagshelg.":0,
      'Jag godkänner att mina personuppgifter samlas in av Klimatriksdagen för att användas inom ramen för klimatrådslaget.':None,
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
    return None

emails = set()
phone_nums = set()
fl_names = set()
def check_duplicates(assembly_name, entry):
  if assembly_name in ['malmö24']:
    messages = []
    email = entry[4]
    if email in emails:
      messages += [f"email {email}"]
    emails.add(email)
    phone_num = entry[3]
    if phone_num in phone_nums:
      messages += [f"phone number {phone_num}"]
    phone_nums.add(phone_num)
    fl_name = (entry[1], entry[2])
    if fl_name in fl_names:
      messages += [f"first+last name {fl_name}"]
    fl_names.add(fl_name)
    if messages:
      print(f"WARNING: Entry with duplicate {', '.join(messages)}")
  else:
    print(f"WARNING: No duplicates check for {assembly_name}")
