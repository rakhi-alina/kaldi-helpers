#!/usr/bin/python3.6

"""
# Copyright 2018 The University of Queensland (Author: Nicholas Lambourne)
# LICENCE: MIT
"""

from argparse import ArgumentParser
from csv import reader
from pathlib import Path
from typing import Dict, Tuple
from praatio import tgio
import codecs


def ctm_to_dictionary(ctm_file_name: str,
                      segments_dictionary: Dict[str, str]) -> dict:
    with codecs.open(ctm_file_name, encoding="utf8") as file:
        ctm_entries = list(reader(file, delimiter=" "))
    textgrid_dictionary = dict()
    for entry in ctm_entries:
        utterance_id, segment_start_time = segments_dictionary[entry[0]]
        if utterance_id not in textgrid_dictionary:
            textgrid_dictionary[utterance_id] = []
        relative_start_time = float(entry[2])
        absolute_start_time = segment_start_time + relative_start_time
        absolute_end_time = absolute_start_time + float(entry[3])
        inferred_text = entry[4]
        utterance_segment = (str(absolute_start_time),
                             str(absolute_end_time),
                             inferred_text)
        textgrid_dictionary[utterance_id].append(utterance_segment)
    return textgrid_dictionary


def get_segment_dictionary(segment_file_name: str) -> Dict[str, Tuple[str, float]]:
    with open(segment_file_name, "r") as file:
        segment_entries = list(reader(file, delimiter=" "))
    segment_dictionary = dict()
    for entry in segment_entries:
        segment_id = entry[0]
        utterance_id = entry[1]
        start_time = float(entry[2])
        segment_dictionary[segment_id] = (utterance_id, start_time)
    return segment_dictionary


def wav_scp_to_dictionary(scp_file_name: str) -> dict:
    wav_dictionary = dict()
    with open(scp_file_name) as file:
        wav_entries = list(reader(file, delimiter=" "))
        for entry in wav_entries:
            utterance_id = entry[0]
            wav_file_path = entry[1]
            wav_dictionary[utterance_id] = wav_file_path
    return wav_dictionary


def create_textgrid(wav_dictionary: Dict[str, str],
                    ctm_dictionary: dict,
                    output_directory: str) -> None:
    for index, utterance_id in enumerate(wav_dictionary.keys()):
        textgrid = tgio.Textgrid()
        tier = tgio.IntervalTier(name='phones',
                                 entryList=ctm_dictionary[utterance_id],
                                 minT=0,
                                 pairedWav=str(Path(wav_dictionary[utterance_id])))
        textgrid.addTier(tier)
        textgrid.save(str(Path(output_directory, f"utterance-{index}.TextGrid")))


def main() -> None:
    parser: ArgumentParser = ArgumentParser(description="Converts Kaldi CTM format to Praat Textgrid Format.")
    parser.add_argument("--ctm", type=str, help="The input_scripts CTM format file", required=True)
    parser.add_argument("--wav", type=str, help="The input_scripts wav.scp file", required=True)
    parser.add_argument("--seg", type=str, help="The segment to utterance mapping", default="./segments")
    parser.add_argument("-o", "--outdir", type=str, help="The directory path for the Praat TextGrid output_scripts",
                        default=".")
    arguments = parser.parse_args()

    segments_dictionary = get_segment_dictionary(arguments.seg)
    ctm_dictionary = ctm_to_dictionary(arguments.ctm, segments_dictionary)
    wav_dictionary = wav_scp_to_dictionary(arguments.wav)
    output_directory = Path(arguments.outdir)

    if not output_directory.parent:
        Path.mkdir(output_directory.parent, parents=True)

    output_directory = str(output_directory)

    create_textgrid(wav_dictionary,
                    ctm_dictionary,
                    output_directory)


if __name__ == '__main__':
    main()
