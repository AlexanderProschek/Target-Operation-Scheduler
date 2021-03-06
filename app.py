#!python

# Import the required packages
try:
    import requests
    import time
    import requests
    import sys
    from dotenv import load_dotenv
    import os
except:
    print('Error importing the neccessary packages\n> Have you run ./setup?')
    exit()

load_dotenv()

# Metadata configuration
progress_width = 40
run_start = time.time()
apikey = os.getenv('DARKSKYKEY')
# Maximum API calls for Darksky
# 1000 for the free plan
maxAPICalls = 1000

# Open the input file
try:
    file = open('./input.csv', 'r')
except:
    print('Error opening input file.\n> Make sure the input.csv is in the home folder!')
    exit()

# Check if user has inputed the API key for Darksky
if not apikey or apikey == '':
     print('Could not find DARKSKYKEY.\n> Change the .env-default file to .env and go to darksky.com/dev to get an API key and put it in the .env file')
     exit()

# Initialize the data storage
data = []
textInput = file.read().split('\r\n')

# Read and parse all the lines of input.csv
for line in textInput:
    dataPoint = {}
    elements = line.split(',')
    dataPoint['start_time'] = time.strptime(
        elements[0], '%d %b %Y %H:%M:%S.%f')
    dataPoint['end_time'] = time.strptime(elements[1], '%d %b %Y %H:%M:%S.%f')
    dataPoint['lat'] = float(elements[2])
    dataPoint['long'] = float(elements[3])
    data.append(dataPoint)

# Array sorting function


def timeSort(e):
    return int(time.mktime(e['start_time']))


# Sort the data by start_time
data.sort(key=timeSort)

# setup progress bar
sys.stdout.write("[%s]" % (" " * progress_width))
sys.stdout.flush()
# return to start of line, after '['
sys.stdout.write("\b" * (progress_width+1))

# API calls made
calls = 0
# Pull down all the weather data
for index, point in enumerate(data):
    lat = point['lat']
    long = point['long']
    urlTime = int(time.mktime(point['start_time']))
    url = 'https://api.darksky.net/forecast/{apikey}/{lat},{long},{time}?units=si'.format(apikey=apikey, lat=lat, long=long, time=urlTime)
    r = requests.get(url)
    json = r.json()
    cloudCover = json['currently']['cloudCover']
    data[index]['cc'] = cloudCover

    # Update the API calls made
    calls = r.headers['x-forecast-api-calls']

    # Update the progress bar
    dash = "-" * ((index+1)/len(data)) * progress_width
    space = " " * ((len(data)-index-1)/len(data)) * progress_width
    sys.stdout.write(dash + space)
    sys.stdout.flush()

sys.stdout.write("]\n")  # this ends the progress bar

# Filter the target passes by cloud cover
data = [e for e in data if e['cc'] < float(
    os.getenv('CLOUD_COVERAGE_THRESHOLD'))]

# Open a filestream for output.csv
outFile = open('output.csv', 'w')
outFile.write('Event Time (UTC),Duration of Mode (s),Active mode'+'\n')

# Write every line of the target evluation to the output.csv file
for index, point in enumerate(data):
    start = int(time.mktime(point['start_time']))
    end = int(time.mktime(point['end_time']))
    outStr = '{s},{t}, Scan - Prep'.format(s=start-int(os.getenv('SCAN_PREP_TIME')), t=os.getenv('SCAN_PREP_TIME'))
    outFile.write(outStr+'\n')

    outStr = '{s},{t},Scan - Spectra Gathering'.format(s=start, t=end-start)
    outFile.write(outStr+'\n')

    outStr = '{s},{t},Scan - Data Finalization'.format(s=end, t=os.getenv('SCAN_FINALIZATION_TIME'))
    outFile.write(outStr+'\n')
    try:
        start = int(time.mktime(data[index+1]['start_time']))
        outStr = '{s},{t},Cruise - Idle'.format(s=end+int(os.getenv('SCAN_FINALIZATION_TIME')), t=start-end-int(os.getenv('SCAN_FINALIZATION_TIME')))
        outFile.write(outStr+'\n')
    except:
        outStr = '{s},{t},Cruise - Idle'.format(s=end+int(os.getenv('SCAN_FINALIZATION_TIME')), t=os.getenv('FINAL_CURISE_TIME'))
        outFile.write(outStr+'\n')

        outStr = '{s},0,END'.format(s=end+int(os.getenv('SCAN_FINALIZATION_TIME'))+int(os.getenv('FINAL_CURISE_TIME')))
        outFile.write(outStr+'\n')

# Finish statement
print('Execution finished in {time} seconds'.format(time=time.time()-run_start))
print('Used {a}/{b} API calls for today'.format(a=calls, b=maxAPICalls))