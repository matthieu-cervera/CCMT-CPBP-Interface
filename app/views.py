'''
VIEWS
    Views is the most important py file for the flask app (and the website). It is the core of the application.
    This is where all routes are specified, where we choose how to redirect the user and how to compute requests.
    The file is separated in 5 parts :
        Homepage : all the functions used from the homepage of the website (often about the user log)
        
        Constraints & Parameters : functions that will change the constraints and the HP of the project
        
        Gen & results : functions that execute the CCMT-CPBP, save the results in DB and display them to the user
        
        Turing Test : functions linked to the Turing Test
        
        functions used without routing : useful functions that aren't really part of the 'views' but needed in other functions
'''


'''
Imports
'''
import shutil
import random
import subprocess
from flask import request, flash, \
    redirect, url_for, render_template, make_response, send_file
from flask import jsonify
import os
from werkzeug.urls import url_parse
from app import app
from app import midi_files_proc_music21 as mfpm
from flask_cors import CORS, cross_origin
import yaml
from flask_login import current_user, login_user, logout_user, login_required
from app.modelDB import User, Music_sample
from app import app, db
from app.config_commands import Commands
commands = Commands()

# user uses his sample or one of our dataset
user_sample = False

# To message the user (see flashes.html and flash_not_empty functions)
current_message = ""
current_category = ""


'''
=============================================================================================================================
======================================================= HOMEPAGE ============================================================
=============================================================================================================================
'''

'''
HOMEPAGE
    homepage_not_logged route, this is the main base page from the website so whenever you open https://localhost:port/,
    it will open this homepage
'''
@app.route('/', methods=['GET', 'POST'])
# add the CORS package to solve the problems of CORS policy when we make Request to the Flask functions
@cross_origin(origin='*')
def homepage_not_logged():
    flash_not_empty(current_message, current_category)
    if current_user.is_authenticated:
        return redirect(url_for('homepage_logged'))
    return render_template('homepage_not_logged.html')

'''
HOMEPAGE
    homepage_logged route, when a user logs in it redirects to logged homepage
'''
@app.route('/homepage_logged', methods=['POST','GET'])
@login_required
def homepage_logged():
    global current_message, current_category, user_info
    flash_not_empty(current_message, current_category)
    print(current_user)
    user_info = {
        'inputUsername' : current_user.username,
        'rendTempUsername': current_user.username,
        'rendTempEmail': current_user.email,
        'stringMIDI': current_user.midiFilesList
    }
    return(render_template('homepage_logged.html',  **user_info))

'''
HOMEPAGE - login
    checks if the user entered valid credentials and if so redirect him to logged homepage
'''
@app.route('/login', methods=['GET', 'POST'])
@cross_origin(origin='*')
def login():
    global current_message, current_category
    if current_user.is_authenticated:
        return redirect(url_for('homepage_logged'))

    form = request.form
    username = form['username']
    password = form['password']
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return(make_response(jsonify({'error': 'Invalid login or password'}), 400))
    
    if login_user(user, remember=True, force=True):
        create_paths()

        current_message = 'Welcome, {}.'.format(current_user.username)
        current_category = 'success'
        print(current_user)
        return redirect(url_for('homepage_logged'))
    else:
        return(make_response(jsonify({'error': 'Unable to log in'}), 400))


'''
HOMEPAGE - logout
    logs the user out (using flask functions)
'''
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    global current_message, current_category
    try:
        logout_user()
    except Exception as e:
        return (make_response(jsonify({'error': e}), 400))
    current_message = 'Logged out'
    current_category = 'danger'
    return redirect(url_for('homepage_not_logged'))

'''
HOMEPAGE - sign in
    signs the user in - adds the user into DB
'''
@app.route('/register', methods=['GET', 'POST'])
def register():
    global current_message, current_category, user_info
    if current_user.is_authenticated:
        return redirect(url_for('homepage_logged'))
    form = request.form
    username, email, password = form['username'], form['email'], form['password']
    if User.query.filter_by(username=username).first() is not None:
        return(make_response(jsonify({'error' : 'username already taken'}), 409))
    elif User.query.filter_by(email=email).first() is not None:
        return(make_response(jsonify({'error' : 'email already exists'}), 400))
    user = User(username, email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    if login_user(user, remember=True, force=True):
        current_message = 'You are now registered'
        current_category = 'success'
        create_paths()
        user_info = {
            'inputUsername': current_user.username,
            'rendTempUsername': current_user.username,
            'rendTempEmail': current_user.email,
            'stringMIDI': current_user.midiFilesList
        }
        return(request.args.get("next") or render_template('homepage_logged.html', **user_info))
    else:
        return(make_response(jsonify({'error' : 'Unable to log in. Please try again'}), 400))
     

'''
HOMEPAGE - delete user
    deletes the user from DB if exists
'''
@app.route('/deleteAccount', methods=['POST'])
@login_required
def deleteAccount():
    global current_message, current_category
    if current_user.is_authenticated:
        try:
            user_to_delete = User.query.filter_by(username=current_user.username).first()
            db.session.delete(user_to_delete)
            db.session.commit()
            current_message = 'Account deleted'
            current_category = 'danger'
            logout_user()
            return (redirect(url_for('homepage_not_logged')))
        except Exception as e:
            return (make_response(jsonify({'error': e}), 400))
    return (make_response(jsonify({'error': 'you are not connected'}), 409))


'''
HOMEPAGE - download midi file 
    Midi file(s) saving route. Whenever a user changes the input of his uploaded midifiles, the function sendMIDIFile
    in MainPage.js sends a POST request to /saveMidFile with the files.
'''
@app.route("/saveMidFile", methods=["OPTIONS", "POST"])
@login_required
def receive_midi_file():
    global current_message, current_category

    # Change working directory to save midi files to /midi_files_checking
    cwd = os.getcwd()
    os.chdir(cwd +'/users/' + current_user.username +'/midi_files_checking')
    # Receive the request and get relevant data
    data_received = request.get_data()
    filename = (str(data_received).split('filename="')[1]).split('"\\')[0]
    data_string = data_received.decode("ISO-8859-1")

    # Get midi data and encode it to bytes format (strip() removes the \n ; split() allows to take just midi data
    midi_data = data_string.split('/mid')[1].split('------WebKitForm')[0].strip().encode("ISO-8859-1")

    # Write midifile to temporary working directory
    with open(filename, 'wb') as saveMidFile:
        saveMidFile.write(midi_data)
        print('Downloaded {} successfully.'.format(filename))

    # Save the filename to the user DB
    current_user.midiFilesList += str(filename)+" "
    db.session.commit()

    os.chdir(cwd)

    current_message = '{} selected'.format(filename)
    current_category = 'success'

    flash_not_empty(current_message,current_category)
    return ""

'''
HOMEPAGE - delete midi file
    Delete the MIDI File selected by the user.
'''
@app.route("/deleteMidiFile", methods=["POST"])
@login_required
def delete_midifile():
    found = False
    data_received = request.json
    midiFileToDelete = data_received["Filename"]
    cwd,directory,path_om,path_cm,path_MIDI_garbage = mfpm.path_establish(current_user.username)

    for f in os.scandir(directory):
        if (f.is_file() and f.name.endswith('.mid') and not found):
            if f.name == midiFileToDelete:
                path_to_file = str(f.path)
                #once we find it we delete the MIDI File
                delete_MIDI_path(path_to_file)

                #delete in the db
                file_list = current_user.midiFilesList.split()
                file_list.remove(midiFileToDelete)
                current_user.midiFilesList = " ".join(file_list)
                db.session.commit()

                found = True

    return ""


'''
HOMEPAGE - midi file upload
    checks if midi file was correctly downloaded
'''
@app.route('/checkIfMidiUploaded', methods=['GET'])
@cross_origin(origin='*')
@login_required
def midiuploaded():
    midiFilesList = current_user.midiFilesList.split()
    midiUpl = False
    cwd,directory,path_om,path_cm,path_MIDI_garbage = mfpm.path_establish(current_user.username)
    for f in os.scandir(directory):
        if (f.is_file() and f.name.endswith('.mid')):
            if f.name not in midiFilesList:
                midiFilesList.append(f.name)

            midiUpl = True
    
    current_user.midiFilesList = " ".join(midiFilesList)
    db.session.commit()

    response = jsonify(answer=midiUpl, midis=' '.join(midiFilesList))  
    return response


'''
HOMEPAGE - user chose to use one of our samples
    If the user wants to use one of our samples, we delete the MIDI Files and we do not pass throught PartsChoosing. We pick the 
    sample accordingly to the user choice, and copy it into the 'test' folder (the folder used for sampling)
'''
@app.route('/dataSelected', methods=['GET', 'POST'])
@login_required
def dataSelected():
    global user_sample, user_info
    user_sample = False

    sample_number = int(request.form.get('sample_number') or -1)

    see_gt_melody = request.form.get('see_gt_melody')

    userpath = os.getcwd() + '/users/' + current_user.username
    recreateFolder(userpath, '/midi_files_checking')

    # choose sample from our repo 
    pkl_folder_path = os.getcwd() + commands.pkl_folder_rel_path
    folder_path = pkl_folder_path + '/all'
    files = os.listdir(folder_path)

    if sample_number>-1:
        # User choice
        file_path = os.path.join(folder_path, files[sample_number])
    else:
        # Random choice
        file_path = os.path.join(folder_path, random.choice(files))
    
    # copy the chosen sample to specific folder for generation
    recreateFolder(pkl_folder_path, '/test')       # commented to fill DB
    subprocess.run(f'cp -R "{file_path}" {pkl_folder_path}/test', shell=True)


    # Run generation process and transform the gt midi file to png
    
    # Specify that we just want pkl to midi on the YAML file
    with open(commands.hparams_rel_path, 'r') as file:  
        data = yaml.load(file, Loader=yaml.FullLoader)

    data['experiment']['gen_groundtruth_mid'] = True

    if see_gt_melody:
        data['experiment']['gen_groundtruth_melody'] = True
    else:        
        data['experiment']['gen_groundtruth_melody'] = False

    with open(commands.hparams_rel_path, 'w') as file:
        yaml.dump(data, file)

    cwd = os.getcwd()
    os.chdir(f'{cwd}/{commands.CMT_CPBP_folder_name}')
 
    subprocess.run(commands.CMT_CPBP_command(seed=42), shell=True)

    path_to_midi = os.path.join(os.getcwd(), f'{commands.results_rel_path}epoch100_groundtruth00.mid')

    destination_folder = commands.static_images_path
    path_to_png = os.path.join(destination_folder, 'groundtruth00.png')
    png_name = path_to_png.split('.png')[0] + '-1.png'
    os.chdir(commands.results_path)
    subprocess.run(commands.midi2png(path_to_midi.split('/')[-1], path_to_png))
    os.chdir(cwd)

    return render_template('constraintSelector.html', **user_info, midi_image=png_name.split('app')[-1])

'''
HOMEPAGE - user chose to use his sample(s)
    The user uploaded his sample. We need to process it and transform it to pkl file : for each sample if there are more than 
    2 parts, the user is invited to choose which part is to be considered as the melody (he is redirected to the function 
    'fileprocessNew' until all his MIDI files are processed)
''' 
@app.route('/parts', methods=['POST'])
@login_required
def ChooseParts():
    userinput = int(request.form['text'])
    print('received'+ str(userinput))
    cwd,directory,path_om,path_cm,path_MIDI_garbage = mfpm.path_establish(current_user.username)

    for f in os.scandir(directory):
        if (f.is_file() and f.name.endswith('.mid')):
            MusicScore, partsMIDIMusicScore = mfpm.MIDIConverter(str(f.path), path_cm, path_om, path_MIDI_garbage)
            path_to_file = str(f.path)
            break

    if userinput < 0 or userinput >= partsMIDIMusicScore:
        display_text = "Please select a valid range: [0, " + str(partsMIDIMusicScore - 1) + "]"
        melody_name = str(f.path).split("/")[-1] 
        return render_template('PartsChoosing.html', PartsRange=display_text, CurrentMelodyNumberParts=partsMIDIMusicScore, CurrentMelodyName=melody_name)

    filename = f.name

    mfpm.MIDISelector(path_to_file, path_cm, path_om, path_MIDI_garbage,MusicScore,userinput, filename)
    return redirect(url_for('fileProcessNew', firstprocess=1))

'''
HOMEPAGE - user chose to use his sample(s)
    Creates new MIDI file with melody (which part is used, is chosen by the user) and chords. If there aren't any other MIDI file, 
    redirects to MIDI to pkl transformation, otherwise allows the user to choose which part will be used for melody for the 
    remaining MIDI files
''' 
@app.route('/processing&<int:firstprocess>', methods=['GET', 'POST'])
@login_required
def fileProcessNew(firstprocess):
    global current_message, current_category, user_sample
    #variable user_sample to True, we will generate melodies from the MIDI Files we have in the user's folder
    user_sample = True

    # establish paths
    print('Files processing')
    cwd, directory, path_om, path_cm, path_MIDI_garbage = mfpm.path_establish(current_user.username)

    if (firstprocess == 0):
        # we check if the files where we have to store the MIDI files have been created previously, in order to delete them and its content
        mfpm.delete_folder_if_exists(path_om)
        mfpm.delete_folder_if_exists(path_cm)
        mfpm.delete_folder_if_exists(path_MIDI_garbage)

    # The current process of separating the melody and the chords is useless and doesn't work well so we replace the
    # mid file by the 'OG' midifile

    for f in os.scandir(directory):
        if (f.is_file() and f.name.endswith('.mid')):
            
            mfpm.create_folder_if_not_exists(path_cm)
            shutil.move(str(f.path), path_cm)
            
            midifileMusicScore, partsMIDIMusicScore = mfpm.MIDIConverter(str(f.path), path_cm, path_om, path_MIDI_garbage)

            # MIDIFile with only Melody
            if partsMIDIMusicScore == 1:
                mfpm.create_folder_if_not_exists(path_cm)
                shutil.move(str(f.path), path_cm)
            else:
                display_text = "Interval: [0, " + str(partsMIDIMusicScore - 1) + "]"
                melody_name = str(f.path).split("/")[-1] 
                return render_template('PartsChoosing.html', PartsRange=display_text, CurrentMelodyNumberParts=partsMIDIMusicScore, CurrentMelodyName=melody_name)

    #we delete the MIDI FIles we could not move (the raw ones with M&C)
    mfpm.delete_folder_if_exists(path_MIDI_garbage)
    return redirect(url_for('midiTopkl'))


'''
=============================================================================================================================
=============================================== Parameters & constraints ====================================================
=============================================================================================================================
'''

'''
CONSTRAINTS SELECTOR PAGE
    The user's MIDI files are ready to be transformed to pkl files for generation : applies the transformation and
    renders the constraints choosing route
'''
@app.route('/midtopkl', methods=['POST','GET'])
@login_required
def midiTopkl():
    global current_message, current_category, user_info

    # mid to pkl conversion
    print('Start converting files (mid to pkl)')
    cwd = os.getcwd()
    command = commands.python_path + ' '+ cwd +'/app/preprocess.py --root_dir '+ cwd +'/users/'+ current_user.username + '/midi_files_checking --midi_dir chords_melody_midi'
    subprocess.run(command, shell=True)
    print('mid to pkl done')

    # copy the chosen samples to specific folder for generation      
    pkl_folder_path = os.getcwd() + commands.pkl_folder_rel_path  
    files_path = os.getcwd() + '/users/' + current_user.username + '/midi_files_checking/pkl_files/' 
    recreateFolder(pkl_folder_path, '/test')
    
    for file in os.listdir(files_path):
        source_path = os.path.join(files_path, file)
        shutil.copytree(source_path, f'{pkl_folder_path}/test/{file}')
    
    current_message = 'Preprocessing successful'
    current_category = 'success'
    flash_not_empty(current_message,current_category)

    # Remove 'uploaded midi files' from user 
    current_user.midiFilesList = ""
    db.session.commit()
    
    return render_template('constraintSelector.html', **user_info)


'''
PARAMETERS SELECTOR PAGE
    Retrieves the user constraints and renders the other parameters selector page.
'''
@app.route("/project_parameters", methods=["GET", "POST"])
@login_required
def parametersSelector():
    global user_info
    pitchConstraints = request.form.get('pitchConstraintString')
    durationConstraints = request.form.get('durConstraintString')
    constraints ={"rhythm" : durationConstraints,
                  "pitch" : pitchConstraints}
    return render_template('paramSelector.html', **user_info, **constraints)

'''
GENERATION PAGE
    Retrieves the parameters chosen by the user and changes the hparams-gen.yaml file accordingly. When everything is changed,
    the sampling is ready and it just renders the button to launch the sampling
'''
@app.route("/CMT", methods=["GET", "POST"])
@login_required
def CMT_preprocess():
    global user_info, current_message, current_category, beam_width, seed

    current_message = 'CMT selected'
    current_category = 'success'
    flash_not_empty(current_message,current_category)

    # Get User Model parameters
    beam_search = int(request.form.get('beam_search', 0))
    beam_search_type = request.form.get('beam_search_type', '')
    pitch_constraints = request.form.get('added_Pconstraints', '')
    rhythm_constraints = request.form.get('added_Rconstraints', '')

    beam_width = request.form.get('beam_width', type=int)
    num_prime = request.form.get('num_prime', default=0, type=int)
    seed = request.form.get('seed', default=42, type=int)
    topk = request.form.get('topk', default=5, type=int)

    # Check if parameters are coherent
    if not(beam_width):
        beam_width = -1

    if beam_search:
        if beam_width<0:
            return render_template('project_choosing.html', **user_info)

    # Load the YAML file
    with open(commands.hparams_rel_path, 'r') as file:  
        data = yaml.load(file, Loader=yaml.FullLoader)

    # Modify the values according to user parameters
    data['experiment']['gen_groundtruth_mid'] = False
    data['experiment']['gen_groundtruth_melody'] = False
    data['model']['cp']['rhythm']['activate'] = False
    data['model']['cp']['pitch']['activate'] = False
    data['experiment']['sampling_java'] = False
    data['experiment']['topk'] = topk
    data['experiment']['num_prime'] = num_prime


    # Constraints
    if len(pitch_constraints)>0:
        data['model']['cp']['pitch']['model']['userconstraints'] = pitch_constraints
        data['model']['cp']['pitch']['activate'] = True
        data['experiment']['sampling_java'] = True
        data['experiment']['sampling_java_seed'] = seed

    if len(rhythm_constraints)>0:
        data['model']['cp']['rhythm']['model']['userconstraints'] = rhythm_constraints
        data['model']['cp']['rhythm']['activate'] = True
        data['experiment']['sampling_java'] = True
        data['experiment']['sampling_java_seed'] = seed


    # Beam Search
    data['experiment']['beam_mode'] = beam_search_type
    if beam_search:
        data['experiment']['beam_width'] = beam_width
        data['experiment']['sampling_java'] = False
    else:
        data['experiment']['beam_width'] = 0

    # Save the modified YAML file
    with open(commands.hparams_rel_path, 'w') as file:
        yaml.dump(data, file)

    return render_template('generation.html', **user_info)


'''
=============================================================================================================================
===================================================== GEN & RESULTS =========================================================
=============================================================================================================================
'''

'''
GENERATION & RESULTS PAGE
    Generates the melodies, and saves the generated melodies to the DB. Renders the results to ther user afterwards.
'''
@app.route('/generation', methods=['POST', 'GET'])
@login_required
def generation():
    global current_category, current_message, user_info, user_sample, beam_width, seed

    cwd = os.getcwd()
    os.chdir(f'{cwd}/{commands.CMT_CPBP_folder_name}')
    subprocess.run(commands.CMT_CPBP_command(seed), shell=True)
    os.chdir(cwd)
    
    # Save files for turing test
    # find name(s) of the sample(s)
    parent_directory = os.getcwd() + f'{commands.pkl_folder_rel_path}/test/'
    folders = os.listdir(parent_directory)

    repo_path = os.path.join(os.getcwd(), commands.midi_repo_rel_path)

    all_images = []
    all_midi = []

    for i, filename in enumerate(folders):
        result_path = os.path.join(os.getcwd() , commands.results_rel_path, 'epoch100_sample%02d.mid' % i)
        result_path_gt = os.path.join(os.getcwd(), commands.results_rel_path, 'epoch100_groundtruth%02d.mid' % i)
        result_path_beam = []
        for j in range(beam_width):
            result_path_beam.append(os.path.join(os.getcwd(), commands.results_rel_path, 'epoch100_sample%02d_beam%02d.mid' % (i, j)))

        filename = os.path.basename(filename) # remove problematic characters
        # Change the names if filenames already exist
        index = 0
        while os.path.exists(f'{repo_path}/{filename}_sample{index}.mid'):
            index += 1
        new_filename_sample = f'{repo_path}/{filename}_sample{index}.mid'

        save_gt = True
        if os.path.exists(f'{repo_path}/{filename}_gt.mid'): 
            save_gt = False
        new_filename_gt = f'{repo_path}/{filename}_gt.mid'

        save_beam = (beam_width > 0)

        # Save samples in DB and folder
        if save_gt :
            # save generated groundtruth
            shutil.copy(result_path_gt, new_filename_gt)
            sample_gt = Music_sample(os.path.relpath(new_filename_gt), False, False)
            db.session.add(sample_gt)
            
            # create score from gt MIDI file
            path_to_png = os.path.join(commands.static_images_path, f'{filename}_gt.png')
            os.chdir(commands.midi_repo_path)
            subprocess.run(commands.midi2png(new_filename_gt.split('/')[-1], path_to_png))   
            os.chdir(cwd)
            gt_png = (path_to_png.split('app')[-1]).split('.png')[0] + '-1.png'
            gt_mid = os.path.join('static/midi_files_repository', f'{filename}_gt.mid')

        if save_beam:
            index_beam = 0
            for beam in result_path_beam:  
                # save generated beam sample            
                new_filename_beam = f'{repo_path}/{filename}_sample{index}_beam{index_beam}.mid'  
                shutil.copy(beam, new_filename_beam)
                sample_beam = Music_sample(os.path.relpath(new_filename_beam), True, True)
                db.session.add(sample_beam)
                
                # create score from MIDI file
                cwd = os.getcwd()
                path_to_midi = os.path.join('static/midi_files_repository', f'{filename}_sample{index}_beam{index_beam}.mid')
                path_to_png = os.path.join(commands.static_images_path, f'{filename}_sample{index}_beam{index_beam}.png')
                png_name = path_to_png.split('.png')[0] + '-1.png'
                os.chdir(commands.midi_repo_path)
                subprocess.run(commands.midi2png(path_to_midi.split('/')[-1], path_to_png))
                os.chdir(cwd)
                
                all_images.append(png_name.split('app')[-1])
                all_midi.append(path_to_midi)
                index_beam += 1

        else:
            # save generated sample
            shutil.copy(result_path, new_filename_sample)   
            sample = Music_sample(os.path.relpath(new_filename_sample), True, False)
            db.session.add(sample)
            
            # create score from MIDI file
            cwd = os.getcwd()
            path_to_midi = os.path.join('static/midi_files_repository', new_filename_sample.split("/")[-1])
            path_to_png = os.path.join(commands.static_images_path, (new_filename_sample.split("/")[-1]).split('.mi')[0] + '.png')
            png_name = path_to_png.split('.png')[0] + '-1.png'
            os.chdir(commands.midi_repo_path)
            subprocess.run(commands.midi2png(path_to_midi.split('/')[-1], path_to_png))
            os.chdir(cwd)
            
            all_images.append(png_name.split('app')[-1])
            all_midi.append(path_to_midi)
    
    db.session.commit()

    return render_template('results.html', **user_info, all_images=all_images, all_midi=all_midi, midi_file_path=path_to_midi, gt_png=gt_png, gt_mid=gt_mid)


'''
RESULTS PAGE
    Deletes the pointed sample from the DB.
'''
@app.route('/sampleDelete', methods=["GET", "POST"])
@login_required
def delete_sample_from_db():
    global current_category, current_message
    sample_path = request.form.get('sample_path', '')
    sample_path = os.path.join('app',sample_path)
    try:
        #delete file in folder
        os.remove(sample_path)

        sample_to_delete = Music_sample.query.filter_by(path=sample_path).first()
        if sample_to_delete:
            db.session.delete(sample_to_delete)
            db.session.commit()
            current_message = 'Sample deleted'
            current_category = 'danger'
            return (make_response(jsonify({'Success': 'Sample deleted'}), 200))
        else:
            print('sample not found')
            return (make_response(jsonify({'error': 'sample not found'}), 404))      
    
    except Exception as e:
        print(e)
        return (make_response(jsonify({'error': f'{e}'}), 400))

'''
RESULTS PAGE
    Downloads the pointed sample to the user's computer.
'''
@app.route('/filedownload', methods=["GET", "POST"])
@login_required
def make_file_downloadable():
    filename = request.form.get('sample_path', '')
    midi_path = os.path.join(os.getcwd(), filename)
    return send_file(midi_path, as_attachment=True)


'''
=============================================================================================================================
====================================================== TURING TEST ==========================================================
=============================================================================================================================
'''

'''
TURING TEST PAGE
    Picks a random sample from DB and renders the turing test templates
'''
@app.route('/turing_test')
def turing_test():
    # random sample choice
    sample_folder_path = os.path.join(os.getcwd(), commands.midi_repo_rel_path) 
    samples = os.listdir(sample_folder_path)
    path = os.path.join('static/midi_files_repository', random.choice(samples))
    
    return render_template('turing_test.html', listening=True, midi_file_path=path)

'''
TURING TEST PAGE
    Checks if the user is right or wrong and shows him the results of the turing test
'''
@app.route('/turing_test_result')
def turing_test_result():
    choice = request.args.get('choice', default = -1, type = int)
    name = request.args.get('name', default = '*', type = str)
    name = os.path.join('app', name)

    # check whether it is an AI generated or not
    sample = Music_sample.query.filter_by(path=name).first()

    if sample is None:
        result = {
        'message': 'An error occured, please try again',
        'answer': False,
        }
    else:
        if sample.AIgenerated == bool(choice):  # good answer
            # save the answer in DB
            sample.answers_correct += 1                    
            if sample.AIgenerated:
                result = {
                    'message': 'Right ! It was AI generated',
                    'answer': True,
                }
            else:
                result = {
                    'message': 'Right ! It was a processed human sample',
                    'answer': True,
                }
        else:
            sample.answers_incorrect += 1

            if sample.AIgenerated:
                result = {
                    'message': 'Wrong ! It was AI generated',
                    'answer': False,
                }
            else:
                result = {
                    'message': 'Wrong ! It was a human processed sample',
                    'answer': False,
                }
        db.session.commit()
    return render_template('turing_test_result.html', **result)



'''
=============================================================================================================================
========================================= FUNCTIONS USED WITHOUT ROUTING ====================================================
=============================================================================================================================
'''
def recreateFolder(cwd_path, folder):
    # delete the existing folder
    mfpm.delete_folder_if_exists(cwd_path + folder)
    # recreate the folder
    mfpm.create_folder_if_not_exists(cwd_path + folder)

def delete_MIDI_path(path_in):
    if os.path.exists(path_in):
        os.remove(path_in)


def create_paths():
    recreateFolder(os.getcwd(), '/users/' + current_user.username)
    userpath = os.getcwd() + '/users/' + current_user.username
    recreateFolder(userpath, '/midi_files_checking')

def flash_not_empty(message, category):
    if message != "":
        flash(message,category)
        message = ""