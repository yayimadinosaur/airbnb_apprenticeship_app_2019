#!/usr/bin/python3

import requests
import time
import sys
import signal
import multiprocessing
from threading import Lock

transactions = 0
success = 0
fail = 0
total_data = 0
total_time = 0
longest_transaction = 0
shortest_transaction = 0
concurrent_cpu = 0
lock = Lock()
site = ""
num_of_atks = 0

#parses site that isn't blank and has https://www. or http://www. and ends with .com
def parse_site(text):
    if text == '':
        print("site cannot be blank, please try again")
        return 0
    if text.endswith(".com") == False:
        print("invalid url, this program only takes .com urls")
        return 0
    if text.startswith("http://www.") == False and text.startswith("https://www.") == False:
        print("invalid url, missing https://www. or http://www.")
        return 0
    return 1

#requests the url to siege, # of attacks, sets default attack to 1 if negative
def request_get():
    site_check = 0
    global site, num_of_atks
    while site_check == 0:
        site = input("url to siege?\n")
        if parse_site(site) == 1:
            site_check = 1
    num_of_atks = input("num of times to run test?\n")
    num_of_atks = int(num_of_atks)
    if num_of_atks <= 1:
        print("minimum tests = 1, setting to default")
        num_of_atks = 1
    #start_request(num_of_atks, site)

#locked variables so they dont error during concurrency, releases after variables are updated
#because of locking, it is hard to show proof that this program is indeed concurrent
#requests the site, fails only >= 500 because of status code descriptions
#200 or lower than 500 is success

def start_request(num, site):
    while num > 0:
        lock.acquire()
        global transactions, success, fail, total_time, total_data, shortest_transaction, longest_transaction
        r = requests.get(site, allow_redirects=False)
        elapsed_time = r.elapsed.total_seconds()
        print("%s   %f secs:    %i bytes ==> GET    /" % (r.status_code, elapsed_time, len(r.content)))
        if r.status_code == 200:
            success += 1
        else:
            if r.status_code >= 500:
                fail += 1
            else:
                success += 1
        num -= 1
        transactions += 1
        if shortest_transaction == 0:
            shortest_transaction = elapsed_time
        elif shortest_transaction > elapsed_time:
            shortest_transaction = elapsed_time
        if longest_transaction == 0:
            longest_transaction = elapsed_time
        elif longest_transaction < elapsed_time:
            longest_transaction = elapsed_time
        total_time += elapsed_time
        total_data += len(r.content)
        lock.release()
    print('')

#prints summary of data
def summary():
    global concurrent_cpu
    avail_percentage = success / (success + fail)
    print("Transactions:                %i hits" % transactions) 
    print("Availability:                %f %%" % (avail_percentage * 100))
    print("Elapsed time:                %f secs" % total_time)
    print("Data transferred:            %f MB" % (total_data / 1000000))
    print("Response time:               %f secs" % (total_time / transactions))
    print("Transaction rate:            %f trans/sec" % (transactions / total_time))
    print("Throughput:                  %f MB/sec" % ((total_data / 1000000) / total_time))
    print("Concurrency:                 %i" % concurrent_cpu)
    print("Successful transactions:     %i" % success)
    print("Failed transactions:         %i" % fail)
    print("Longest Transaction:         %f" % longest_transaction)
    print("Shortest Transaction:        %f" % shortest_transaction)
    print("")

#does a GET request, up to 4 concurrent threads, handles keyboard interrupt properly
def main():
    global concurrent_cpu
    process_check = 0
    max_cpu = multiprocessing.cpu_count()
    print("there are %i CPUs on this machne" % max_cpu)
    while process_check == 0:
        num_processes = input("concurrent tasks wanted?\n")
        if num_processes.isdigit() == False:
            print("invalid number, cpu ranges 1 - %i on this machine" % max_cpu)
            continue
        num_processes = int(num_processes)
        if 1 < num_processes > max_cpu:
            print("invalid number, cpu ranges 1 - %i on this machine" % max_cpu)
        else:
            concurrent_cpu = num_processes
            process_check = 1
    try:
        request_get()
        print("con = %i" % concurrent_cpu)
        print("** CATTLE BRUISER OPERATIONAL 1.0.0")
        print("** Preparing %i concurrent users for battle." % concurrent_cpu)
        count = 0
        procs = []
        for i in range(concurrent_cpu):
            procs.append(multiprocessing.Process(target = start_request(num_of_atks, site)))
        for p in procs:
            p.start()
        #request_get()
        summary()
    except KeyboardInterrupt:
        #cleanly end multithreading (but breaks when keyboardinterrupt
        #leaving comment here for future debug if needed
        #for p in procs:
        #    p.join()
        print("\nKeyboardInterrupted by User, lifting server siege")
        print("MOOOOOOO")
        summary()

if __name__ == "__main__":
    main()
