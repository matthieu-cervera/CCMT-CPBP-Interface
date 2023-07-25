import music21
import os
import shutil
import stat
import sys

'''
midi file processing
    Create MIDI files and put them into folders to be ready to be processed and transformed to pkl files. Also there are several
    useful folder manipulation functions
'''

def MIDIConverter(path_to_file, cm_path, om_path, garbage_path):

    midifileMusicScore = music21.converter.parse(path_to_file)
    partsMIDIMusicScore = len(midifileMusicScore.recurse().getElementsByClass(music21.stream.Part))
    return(midifileMusicScore, partsMIDIMusicScore)


def MIDISelector(path_to_file, cm_path, om_path, garbage_path,midifileMusicScore,part_vble, filename):
    create_folder_if_not_exists(cm_path)
    create_folder_if_not_exists(om_path)
    create_folder_if_not_exists(garbage_path)
    # the music Score we create as an output only for the Melody
    outputMusicScoreOM = music21.stream.Score()

    # the music Score we create as an output for the Melody + Chords
    outputMusicScoreMC = music21.stream.Score()

    # First we extract the Chord Part using .chordify()
    streamChords = midifileMusicScore.chordify()
    for c in streamChords.recurse().getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)

    streamMelody = midifileMusicScore.getElementsByClass(music21.stream.Part)[part_vble]

    # our MIDI File input contains Melody as well as Chords, so we create 2 MIDI Files, 1 with C&M, and the other one only with M
    outputMusicScoreMC.insert(0, streamMelody)
    outputMusicScoreMC.insert(0, streamChords)
    outputMusicScoreOM.insert(0, streamMelody)

    # for the MIDI File we created only for Melody
    shutil.move(str(outputMusicScoreOM.write(fmt="Midi")), os.path.join(om_path, filename))
    # for the MIDI File we created with M&C
    shutil.move(str(outputMusicScoreMC.write(fmt="Midi")), os.path.join(cm_path, filename))
    # we need to store the MIDI Files we used for create the MusicScores (used for generating more MIDI FIles), and delete it after
    shutil.move(path_to_file, garbage_path)

def delete_folder_if_exists(path_in):
    if(os.path.exists(path_in)):
        os.chmod(path_in, stat.S_IRWXU)
        shutil.rmtree(path_in)

def create_folder_if_not_exists(path_in):
    if(os.path.exists(path_in) == False):
        os.mkdir(path_in)

def path_establish(username):
    cwd = os.getcwd().replace('\\', '/')
    directory = cwd + '/users/' + username + '/midi_files_checking'
    path_om = directory + "/only_melody_midi"
    path_cm = directory + "/chords_melody_midi"
    path_MIDI_garbage = directory + "/garbage"
    return(cwd, directory, path_om, path_cm, path_MIDI_garbage)

#------------------------------------MAIN------------------------------#
def process():
    #we establish our paths
    print('files processing')
    cwd = os.getcwd().replace('\\', '/')
    directory = cwd + '/midi_files_checking'
    path_om = directory + "/only_melody_midi"
    path_cm = directory + "/chords_melody_midi"
    path_MIDI_garbage = directory + "/garbage"

    #we check if the files where we have to store the MIDI files have been created previously, in order to delete them and its content
    delete_folder_if_exists(path_om)
    delete_folder_if_exists(path_cm)
    #just if there's any problem with the garbage file where we store Files
    delete_folder_if_exists(path_MIDI_garbage)

    for f in os.scandir(directory):
        if (f.is_file() and f.name.endswith('.mid')):
            MIDIConverter(str(f.path), path_cm, path_om, path_MIDI_garbage)

    #we delete the MIDI FIles we could not move (the raw ones with M&C)
    delete_folder_if_exists(path_MIDI_garbage)




