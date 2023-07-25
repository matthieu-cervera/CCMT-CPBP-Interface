from music21 import *

import argparse
import glob

def mxl2midi_2tracks(file_path):
    c = converter.parse(file_path)
    parts = instrument.partitionByInstrument(c)
    notes_to_parse = None
    # File has instrument parts
    if parts: 
        notes_to_parse = parts.parts[0].recurse()
    # File has notes in a flat structure
    else: 
        notes_to_parse = c.flat.notes

    melody_stream = stream.Part()
    chords_stream = stream.Part()
    chord_duration = []

    # Extract melody and chords into 2 seperate parts
    for element in notes_to_parse:
        if isinstance(element, harmony.ChordSymbol):
            # Songs that have one-note-chord are skipped
            if len(element.pitchClasses) < 2:
                return
            chords_stream.insert(element.offset, element)
            chord_duration.append(element.offset)
        elif isinstance(element, note.Note):
            melody_stream.insert(element.offset, element)
    
    # Make the chords end when the next chord starts
    for i in range(0, len(chord_duration) - 1):
        # This loop handles the case where there are more than 1 chord played at the same time.
        # Otherwise, the current chord will have a duration of 0. 
        for j in range(i + 1, len(chord_duration)):
            if chord_duration[i] != chord_duration[j]:
                chords_stream[i].duration = duration.Duration(chord_duration[j] - chord_duration[i])
                break
    
    # Make the last chord(s) last until the song ends
    last_chord_duration = duration.Duration(notes_to_parse.duration.quarterLength - chords_stream[-1].offset)
    for i in range(0, len(chord_duration)):
        if chords_stream[-(i + 1)].offset == chords_stream[-1].offset:
            chords_stream[-(i + 1)].duration = last_chord_duration
        else:
            break

    score = stream.Score([melody_stream, chords_stream])
    # .mid file will be created in same directory as .mxl file
    dest_path = file_path[:-4] + '.mid'
    score.write('midi', fp=dest_path)

def dataset_xml_2_dataset_midi_2tracks(dataset_path):
    mxl_files = sorted(glob.glob(f'{dataset_path}/**/*.mxl', recursive=True))
    print(f'number of .mxl files: {len(mxl_files)}')

    error_count = 0
    count = 0
    for mxl_file in mxl_files:
        try:
            print(f'{count}: Parsing {mxl_file}')
            mxl2midi_2tracks(mxl_file)
        except Exception as e:
            print(f'Error: {e}')
            error_count += 1
        count += 1

    print(f'Dataset conversion ended with {error_count} errors')

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, help='path of the dataset')
args = parser.parse_args()
dataset_xml_2_dataset_midi_2tracks(args.path)
