#!/usr/bin/python
import os
import itertools
import intervaltree
from matplotlib import pyplot as plt
import pprint
import utils

pp = pprint.PrettyPrinter(indent=2)


def _get_tpx_lines(full_file_path):
    result = []
    with open(full_file_path) as input_file:
        for line in input_file.readlines():
            if line[0] == "#":
                continue
            result.append(line)
    return result


def _get_tpx_lines_by_chromosome(full_file_path):
    result = {}
    with open(full_file_path) as input_file:
        for line in input_file.readlines():
            if line[0] == "#":
                continue
            cols = line.split('\t')
            if cols[0] not in result:
                result[cols[0]] = []
            result[cols[0]].append(line)
    return result


def plot_length_distributions(full_file_paths, filenames, options):
    """ """
    plt.clf()
    # out_filename = filenames[0] + ".combined.plot.png"
    out_filename = filenames[0] + ".plot.png"
    markers = ["o", "s"]
    colors = ["green", "red"]
    for key, filename in enumerate(filenames):
        full_file_path = full_file_paths[key]
        print ("Plotting " + filename)
        lengths = {}
        max_len = 0

        for line in _get_tpx_lines(full_file_path):
            cols = line.split('\t')
            if line[0] == '#':
                continue

            tfo_start = int(cols[1])
            tfo_end = int(cols[2])
            tfo_len = tfo_end - tfo_start
            lengths[tfo_len] = 1 if tfo_len not in lengths else lengths[tfo_len] + 1
            if lengths[tfo_len] > max_len:
                max_len = lengths[tfo_len]

        # pp.pprint(lengths)
        plt.xlim(10, 50)
        plt.ylim(0, max_len + 1000)
        plt.title("Length distribution")
        plt.ylabel("#triplexes")
        plt.xlabel("triplex length")

        sorted_length_keys = sorted(list(lengths.keys())[:50])
        sorted_length_values = [lengths[x] for x in sorted_length_keys]

        plt.plot(sorted_length_keys, sorted_length_values, label=filename, marker=markers[key], color=colors[key])
        print lengths
    plt.legend(loc='upper right')
    plt.savefig(options.dataOutDir + "/" + out_filename, dpi=150)


def clean_nonmatching_chromosomes(full_file_path):
    """
    Remove triplexes which are located on different chromosomes.
    :param full_file_path:
    :param tpx_content:
    :return:
    """
    print ("Cleaning " + full_file_path)

    tpx_content = _get_tpx_lines(full_file_path)
    tpx_file_write = open(full_file_path, 'wb')

    cleaned_content = []
    for line in tpx_content:
        cols = line.split('\t')
        if line[0] != '#' and cols[0] != cols[3]:
            continue
        annotated_line = line.replace(cols[0], cols[0]+":0") if ':' not in cols[0] else line
        # annotated_line = line.replace(":0:0", ":0")  # if ':' not in cols[0] else line
        cleaned_content.append(annotated_line)

    tpx_file_write.writelines(cleaned_content)
    tpx_file_write.close()


def get_first_line(full_file_path):
    with open(full_file_path) as input_file:
        result = input_file.readlines()[0]
    return result


##########################################################################################################
def create_triplex_superset_tree(full_file_path):
    print ("Creating triplex superset TREE VERSION for file: " + full_file_path)
    tree = intervaltree.IntervalTree()
    content = _get_tpx_lines_by_chromosome(full_file_path)

    output_file = open(full_file_path.replace('.tpx', '.ss.tpx'), 'w')
    output_file.write(get_first_line(full_file_path))

    def compare(iv1, iv2):
        if iv1[0] < iv2[0]:  # start is smaller
            return -1
        elif iv1[0] > iv2[0]:  # start is larger
            return 1
        else:  # starts are equal, check for end point
            return iv2[1] - iv1[1]

    for chrom in content.keys():
        print ("Processing #" + str(len(content[chrom])) + " triplexes from chromosome " + chrom)
        sorted_intervals = set()
        for index, line in enumerate(content[chrom]):
            cols = line.split('\t')
            (tfo_chr, tfo_start_offset) = cols[0].split(':')
            (tts_chr, tts_start_offset) = cols[3].split(':')
            tfo_start_offset = int(tfo_start_offset)
            tts_start_offset = int(tts_start_offset)
            (tfo_start_pos, tfo_end_pos, tts_start_pos, tts_end_pos) = (int(cols[1]) + tfo_start_offset,
                                                                        int(cols[2]) + tfo_start_offset,
                                                                        int(cols[4]) + tts_start_offset,
                                                                        int(cols[5]) + tts_start_offset)
            sorted_intervals.add((tts_start_pos, tts_end_pos, index))
            assert (tfo_chr == tts_chr)

        sorted_intervals = sorted(sorted_intervals, cmp=compare)

        # add first interval always
        tree.add(intervaltree.Interval(sorted_intervals[0][0], sorted_intervals[0][1], sorted_intervals[0][2]))
        output_file.write(content[chrom][sorted_intervals[0][2]])
        for iv in sorted_intervals[1:]:
            overlaps_start = set([x.data for x in tree.top_node.search_overlap([iv[0]])])
            contained = False
            for iv_overlap in tree.top_node.search_overlap([iv[1]]):
                if iv_overlap.data in overlaps_start:
                    contained = True
            if not contained:
                tree.add(intervaltree.Interval(iv[0], iv[1], iv[2]))
                output_file.write(content[chrom][iv[2]])
    output_file.close()


##########################################################################################################
def create_triplex_superset(full_file_path):
    print ("Creating triplex superset for file: " + full_file_path)
    content = _get_tpx_lines_by_chromosome(full_file_path)

    output_file = open(full_file_path.replace('.tpx', '.ss.tpx'), 'w')
    output_file.write(get_first_line(full_file_path))

    for chrom in content.keys():
        print ("Processing #" + str(len(content[chrom])) + " triplexes from chromosome " + chrom)
        result = []
        sorted_intervals = set()
        for index, line in enumerate(content[chrom]):
            cols = line.split('\t')
            (tfo_chr, tfo_start_offset) = cols[0].split(':')
            (tts_chr, tts_start_offset) = cols[3].split(':')
            tfo_start_offset = int(tfo_start_offset)
            tts_start_offset = int(tts_start_offset)
            (tfo_start_pos, tfo_end_pos, tts_start_pos, tts_end_pos) = (int(cols[1]) + tfo_start_offset,
                                                                        int(cols[2]) + tfo_start_offset,
                                                                        int(cols[4]) + tts_start_offset,
                                                                        int(cols[5]) + tts_start_offset)
            sorted_intervals.add((tts_start_pos, tts_end_pos, index))
            assert (tfo_chr == tts_chr)

        sorted_intervals = sorted(sorted_intervals, key=lambda t: (t[0], t[1]))
        length = len(sorted_intervals)

        def overlaps(p, c):
            return c[0] <= p[1] <= c[1] or p[0] <= c[0] <= p[1]

        for index in range(length):
            parent = sorted_intervals[index]
            if parent is None:
                continue
            if parent not in result:
                result.append(parent)

            for child_index in range(index + 1, length):
                child = sorted_intervals[child_index]

                if child is None:  # means interval is already contained in another one, hence was set to None
                    continue

                if not overlaps(parent, child):  # reached a non-overlapping interval, can break loop now
                    break

                if parent[0] <= child[0] and parent[1] >= child[1]:
                    sorted_intervals[child_index] = None

        for r in result:
            output_file.write(content[chrom][r[2]])
    output_file.close()


##########################################################################################################
def normalize_sequence_length(full_file_path, nz_len):
    """ Cut each sequence into several sequences of exactly nz_len basepairs. """
    print ("Normalizing sequence length for file: " + full_file_path)
    content = _get_tpx_lines(full_file_path)

    result = []

    for l in range(0, len(content), 2):
        seq_desc = content[l].rstrip()
        seq = content[l + 1].rstrip()
        if len(seq) < nz_len:
            raise ValueError("Found sequence that is smaller than nz_len!: " + seq)
        elif len(seq) > nz_len:
            for shift in range(0, len(seq) - nz_len + 1):
                result.append(seq_desc + "_segment_#" + str(shift) + "\n")
                result.append(seq[shift:shift + nz_len] + "\n")

    output_file = open(full_file_path.replace('.fa', '.nz.fa'), 'w')
    output_file.writelines(result)
    output_file.close()


def do_data_analysis(options):
    for filename in os.listdir(options.dataInDir):
        if filename.startswith(options.dataPrefix) and filename.endswith(options.dataExtension):
            full_file_path = options.dataInDir + '/' + filename
            if os.path.isfile(full_file_path):
                # clean_nonmatching_chromosomes(full_file_path, tpx_content)
                if options.dataAnalysis == "superset":
                    create_triplex_superset_tree(full_file_path)
                elif options.dataAnalysis == "clean":
                    clean_nonmatching_chromosomes(full_file_path)
                elif options.dataAnalysis == "plot-ld":
                    # plot_length_distributions([full_file_path.replace(".ss.tpx", ".tpx"), full_file_path], [filename.replace(".ss.tpx", ".tpx"), filename], options)
                    plot_length_distributions([full_file_path], [filename], options)
                elif options.dataAnalysis == "normalize":
                    normalize_sequence_length(full_file_path, 20)




