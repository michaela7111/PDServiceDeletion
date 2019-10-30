import sys
import traceback
import requests
import json
from datetime import datetime

# Update to match your chosen parameters
TEAM_IDS = []
TIME_ZONE = 'UTC'
SORT_BY = 'name'
QUERY = ''
INCLUDE = []

# Other variables needed for script
dash = '-' * 62
service_ids = []

def preamble():
    print("\n\nThis script will delete services in PagerDuty which have not had recent incident activity.  You will enter your PagerDuty API KEY and the amount of time without any recent activity for your list of services.  You will then confirm that you want to delete those services and the script will execute that action.\n\n")

def pd_info():
    global API_KEY
    API_KEY = raw_input("Enter the API KEY for your PagerDuty account: ")    

    url = 'https://api.pagerduty.com/services'
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': 'Token token={token}'.format(token=API_KEY)
    }
    payload = {
        'team_ids[]': TEAM_IDS,
        'time_zone': TIME_ZONE,
        'sort_by': SORT_BY,
        'query': QUERY,
        'include[]': INCLUDE
    }
    
    r = requests.get(url, headers=headers, params=payload)
    
    # Watch for valid API KEY entries
    try:
        data = r.json()
    except Exception as error:
        print("Not a valid PagerDuty API KEY - try again.\n")
        return pd_info()

    items = data['services']
    return items

def list_services(items):
    # Print the header for the list
    print(dash)
    print('{:>10s}{:>49s}'.format('-- Service --','-- Last Incident --'))
    print(dash)

    # Iterate over list to display list of current services
    for item in items:
        name = item['name']
	last_incident = item['last_incident_timestamp']
	print('{:<42s}{:>14s}'.format(str(name),str(last_incident)))

    return items

def output_format(items):
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    try:
        user_input = raw_input("\nEnter the number of months to go back (3, 6, 9 or 12): ")
        val = int(user_input)
        while val != 3 and val != 6 and val != 9 and val != 12:
            val = input("Entry must be (3, 6, 9 or 12). Enter the number of months to go back: ")
    except ValueError:
        print("The value entered is not an integer -- please try again.")
        return output_format(items)
    except NameError:
        print("The value entered is not an integer -- please try again.")
        return output_format(items)       

    print("Services with last incident more than " + str(val) + " months ago are listed below.")

    # Print header for the list
    print(dash)
    print('{:>10s}{:>49s}'.format('-- Service --','-- Last Incident --'))
    print(dash)
    
    # Iterate over list to display services that match criteria
    for item in items:
        name = item['name']
        last_incident = item['last_incident_timestamp']
            
        if last_incident in (None, ''):
            # 4-digit arbitrary value that won't evaluate to 0 in below calculations
            year_last_incident = 1000
        else:
            year_last_incident = int(last_incident[:4])
            month_last_incident = int(last_incident[5:7])
            day_last_incident = int(last_incident[8:10])

            if(int(year) - year_last_incident == 0):
                if((int(month) - month_last_incident == int(val)) and (int(day) - day_last_incident >= 0)):
                    print('{:<42s}{:>14s}'.format(str(name),str(last_incident)))
                    service_ids.append(item['id'])
                if(int(month) - month_last_incident > int(val)):
                    print('{:<42s}{:>14s}'.format(str(name),str(last_incident)))
                    service_ids.append(item['id'])

            if(int(year) - year_last_incident == 1):
                if((int(month) - month_last_incident + 12 == int(val)) and (int(day) - day_last_incident >= 0)):
                    print('{:<42s}{:>14s}'.format(str(name),str(last_incident)))
                    service_ids.append(item['id'])
                if(int(month) - month_last_incident + 12 > int(val)):
                    print('{:<42s}{:>14s}'.format(str(name),str(last_incident)))
                    service_ids.append(item['id'])

            if(int(year) - year_last_incident >= 2):
                print('{:<42s}{:>14s}'.format(str(name),str(last_incident)))
                service_ids.append(item['id'])
    
    if not service_ids:
        print("No Services match criteria - script will now exit.\n")
        sys.exit()

    return val

def service_deletion(val,items):
    print("\nThe above listed Services are eligible for deletion as their last incident is " + str(val) + " or more months ago.")
    check = str(raw_input("Do you want to delete these Services? (Y/N): ")).lower().strip()
    
    try:
        if check[0] == 'y':
            for i in service_ids:
                url = 'https://api.pagerduty.com/services/{id}'.format(id=i)
                headers = {
                    'Accept': 'applications/vnd.pagerduty+json;version=2',
                    'Authorization': 'Token token={token}'.format(token=API_KEY)
                }
                r = requests.delete(url,headers=headers)
            
            print("\nServices have been deleted -- updated list is below")
            return items
        elif check[0] == 'n':
            print("\nServices have not been deleted -- script exiting.\n")
            sys.exit()
        else:
            print("***** Invalid input - please try again.")
            return service_deletion(val,items)
    except Exception as error:
        print("***** Invalid input - please try again.")
        return service_deletion(val,items)

def updated_list():
    url = 'https://api.pagerduty.com/services'
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': 'Token token={token}'.format(token=API_KEY)
    }
    payload = {
        'team_ids[]': TEAM_IDS,
        'time_zone': TIME_ZONE,
        'sort_by': SORT_BY,
        'query': QUERY,
        'include[]': INCLUDE
    }
    r = requests.get(url, headers=headers, params=payload)
    data = r.json()
    updated_items = data['services']

    print(dash)
    print('{:>10s}{:>49s}'.format('-- Service --','-- Last Incident --'))
    print(dash)

    for item in updated_items:
        name = item['name']
        last_incident = item['last_incident_timestamp']
        print('{:<42s}{:>14s}'.format(str(name),str(last_incident)))

if __name__ == '__main__':
    preamble()
    items = list_services(pd_info())
    service_deletion(output_format(items),items)
    updated_list()
