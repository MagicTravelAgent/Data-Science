from Levenshtein import distance as lev
import re

#This script has been used to compare the output of a few ocr's (Delpher's, easyocr module, pyocr module) to a transcript file.

#Define paths and filenames
output_dir = "###"
trial_filenames = ["delpherocr.txt","easyocr.txt","pyocr.txt"]
transcript_filename = "transcript.txt"

def average(numbers):
    return sum(numbers) / len(numbers)

def sd(numbers):
    avg = average(numbers)
    return average([((num - avg) ** 2) ** 0.5 for num in numbers])

#For each comparison (between one of the ocr's and the transcript) and for each text, calculate:
# - the Levenshtein distance (minimum number of insertions/substitutions/deletions needed to go from transcript text to ocr text)
# - the corresponding percentage of text that would need to be altered to go from transcript text to ocr text (Levenshtein distance / length of transcript text * 100%)
lev_dist_arrays = []
perc_arrays = []
for trial_filename in trial_filenames:
    with open(output_dir + transcript_filename) as transcript_file:
        with open(output_dir + trial_filename) as trial_file:
            lev_dists = []
            percs = []
            while(True):
                try:
                    trans_line = next(transcript_file).lower()
                    trial_line = next(trial_file).lower()
                    dist = lev(trans_line, trial_line)
                    lev_dists.append(dist)
                    percs.append(int(dist / len(trans_line) * 1000) / 10)
                except StopIteration:
                    break
    lev_dist_arrays.append(lev_dists)
    perc_arrays.append(percs)

#Calculate averages and standard deviations and write to file
with open(output_dir + "comparison.csv","w") as output_file:
    output_file.write(",Score1,Score2,Score3,Score4,Score5,Score6,Score7,Score8,Score9,Score10,Avg.,Sd.\n")
    for x in range(min(len(lev_dist_arrays),len(perc_arrays))):
        lev_dists = lev_dist_arrays[x]
        percs = perc_arrays[x]
        output_file.write("%s, " % (re.sub(".txt$","",trial_filenames[x])))
        for y in range(min(len(lev_dists),len(percs))):
            output_file.write("%d (%.1f%%), " % (lev_dists[y], percs[y]))
        output_file.write("%.1f (%.1f%%), %.1f (%.1f%%)\n" % (average(lev_dists), average(percs), sd(lev_dists), sd(percs)))