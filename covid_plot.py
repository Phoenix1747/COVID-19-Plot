#!/usr/bin/env python3
import csv
from git import Repo, exc
import matplotlib.pyplot as plt
from argparse import ArgumentParser

git_dir = "COVID-19"
path = "csse_covid_19_data/csse_covid_19_time_series/"
filename1 = "time_series_covid19_"
filename2 = "_global.csv"

modes = {"total":"number of cases","delta":"number of new cases","growth":"growth rate"}

#global vars
data = {}
header = []

# PARSE USER INPUT
def parse_user():
        parser = ArgumentParser(description="Plot the latest COVID-19 data based on country and province/state.")

        parser.add_argument("-np", "--no-plot", action='store_true', help="do not plot the data")
        parser.add_argument("-l", "--log", action='store_true', help="plot logarithmic axis")
        parser.add_argument("-f", "--file", help="print data to this file")
        parser.add_argument("-c", "--country", required=True, action="append", help="specify country as in data. If you provide multiple country flags this will go into comparison mode.")
        parser.add_argument("-p", "--province", default="", help="specify province in the chosen country")
        parser.add_argument("-cy", "--category", default="confirmed", help="specify a category [confirmed, deaths, recovered]")
        parser.add_argument("-m", "--mode", default="total", help="specify what to plot [total, delta, growth]")

        return parser.parse_args()

# INIT ALL AROUND THE DATA REPO GIT AND ALL
def init_repo():
        repo = Repo(".")

        try:
                submodule = Repo(git_dir)
                current = submodule.head.commit
                print("Looking for updates...")

                try:
                        submodule.remotes.origin.pull() ##Update Submodules
                except exc.GitCommandError as err:
                        if "resolve" in err.stderr.lower():
                                print("No internet connection, skipping check.")
                                return
                        else:
                                print(err)
                
                if current != submodule.head.commit:
                        print("Updated data submodule.")
                else:
                        print("Data is up-to-date.")
        except:
                print("No data found. Initializing...")
                repo.submodule_update()
                print("Successfully initialized submodule.")

# GET ALL THE DATA FROM GIT REPO
def get_data(category, country, province):
        global data
        global header

        file = git_dir + "/" + path + filename1 + category + filename2
        print("Preparing data...")
        with open(file) as ofile:
                csv_reader = csv.reader(ofile, delimiter=",")
                line_count = 0
                for row in csv_reader:
                        if line_count == 0:
                                header = row
                        else:
                                for c in country:
                                        if c in data:
                                                data_buffer = data[c]
                                        else:        
                                                data_buffer = []
                                        
                                        if c.lower() == row[1].lower():
                                                if province == "":
                                                        if len(data_buffer) == 0:
                                                                data_buffer = row
                                                                data_buffer[0] = ""
                                                        else:
                                                                i = 4
                                                                while i < len(row):
                                                                        data_buffer[i] = int(data_buffer[i]) + int(row[i])
                                                                        i += 1
                                                elif province.lower() in row[0].lower():
                                                        data_buffer = row

                                                data[c.lower()] = data_buffer

                        line_count += 1
        
        if len(data) > 0:
                print("Done grabbing data.")
        else:
                print("Country and/or province not available!")
                quit()

# COMPUTE DAY TO DAY DELTA
def get_delta():
        delta = {}

        for key in data:
                delta[key] = [] #List with all the changes
                n = 0 #starts really at 3, the first four entries are region, country, lat/longitude; the fith one is just the start, no delta
                while n < len(data[key]):
                        if n < 4:
                                delta[key] += [""]
                        elif n == 4:
                                delta[key] += [0]
                        else:
                                dN = int(data[key][n]) - int(data[key][n-1])
                                delta[key] += [dN]
                        n += 1
        return delta

# COMPUTE GROWTH RATE
def get_growth():
        delta = get_delta()
        growth = {}

        for key in data:
                growth[key] = []
                n = 0
                while n < len(data[key]):
                        if n < 4:
                                growth[key] += [""]
                        elif delta[key][n-1] == 0 or delta[key][n-1] == "":
                                growth[key] += [0]
                        else:
                                exp = int(delta[key][n]) / int(delta[key][n-1])
                                growth[key] += [exp]
                        n += 1
        return growth

# PRINT ALL (NEW) DATA TO CSV FILE
def print_file(filepath):
        print("Preparing file...")
        
        delta = get_delta()
        growth = get_growth()

        save_file = filepath

        with open(save_file, "w", newline="") as sfile:
                writer = csv.writer(sfile)
                writer.writerow(header)
                for key in data:
                        writer.writerow(data[key])
                        writer.writerow(delta[key])
                        writer.writerow(growth[key])
        print(f"Successfully wrote data to {save_file}.")

# PLOT ALL THE COVID DATA
def plot_data(plot_log, category, mode):
        global data
        
        print("Preparing plot...")
        plt.figure("COVID-19 Plot")

        if mode == "delta":
                data = get_delta()
        elif mode == "growth":
                data = get_growth()

        for key in data:
                i = 4
                plot_data = []
                while i < len(data[key]):
                        plot_data += [int(data[key][i])]
                        i += 1

                plt.plot(plot_data, label=f"{key.capitalize()}")

        i = 0
        string = f"{category} in "
        for key in data:
                if i > 0:
                        string += " vs "

                if data[key][0] == "":
                        string += f"{key.capitalize()}"
                else:
                        string += f"{data[key][0]}, {key.capitalize()}"
                i += 1

        plt.title(string)

        plt.legend()
        plt.xlabel(f"days since {header[4]} [mm/dd/yy]")
        plt.ylabel(modes[mode])
        if plot_log:
                plt.yscale('log')
        plt.show()
        
        print("Goodbye.")

def main():
        args = parse_user()

        if len(args.country) > 1 and not args.province == "":
                print("Comparing countries ONLY. Please delete province input.")
                return
        if not args.mode.lower() in modes:
                print("Invalid plot mode.")
                return
        
        init_repo()
        get_data(args.category.lower(), args.country, args.province)
        if args.file:
                print_file(args.file)
        if not args.no_plot:
                plot_data(args.log, args.category.capitalize(), args.mode.lower())

main() #do stuff
