'''
Imports
'''
from scipy.fftpack import ss_diff
from scipy.special import rel_entr
from zipfile import ZipFile
import torch.nn as nn
import os
import subprocess
import time
import torch
import torch.nn.functional as F

class ConstraintProgramming():
    RHYTHM = 'rhythm'
    PITCH = 'pitch'
    BASIC_JAVA_CMD = f'java -cp ../../../target/minicpbp-1.0.jar minicpbp.examples.'
    FILENAME_TOKEN_RHYTHM = f'token_rhythm.dat'

    def __init__(self, config, frame_per_bar):
        self.config = config
        self.frame_per_bar = frame_per_bar
        self.java_process = None
        self.profiler = []

        self.config[self.RHYTHM]['weight_variation']['rate'] = (self.config[self.RHYTHM]['weight_variation']['weight_max'] - self.config[self.RHYTHM]['weight_variation']['weight_min']) / ((self.frame_per_bar * self.config[self.RHYTHM]['weight_variation']['nb_bars_group']) - 1)
        self.config[self.PITCH]['weight_variation']['rate'] = (self.config[self.PITCH]['weight_variation']['weight_max'] - self.config[self.PITCH]['weight_variation']['weight_min']) / ((self.frame_per_bar * self.config[self.PITCH]['weight_variation']['nb_bars_group']) - 1)

        # minicpbp useful paths
        self.minicpbp_path = config['minicpbp_path']
        self.minicpbp_music_path = os.path.join(self.minicpbp_path, 'src', 'main', 'java', 'minicpbp', 'examples', 'data', 'MusicCP')
        self.minicpbp_working_dir = os.path.join(self.minicpbp_path, 'src', 'main', 'java')
    
    def save_rhythm_token(self, rhythm_tokens):
        with open(os.path.join(self.minicpbp_music_path, self.FILENAME_TOKEN_RHYTHM), 'w') as f:
            num_sample = rhythm_tokens.shape[0]
            for j in range(num_sample):
                f.write(' '.join(map(str, rhythm_tokens[j].tolist())))
                f.write('\n')

    '''
    Popen is a function from subprocess library that allows a process to start and run in the background (the python code doesn't "wait"
    for the process to end). This is the function to create a new process. We access it to begin rhythm or pitch generation with
    constraints or when an error occured in the previous process
    '''
    def create_java_process(self, tokens, output, epoch, beamWidth, i, device, cp_on_rhythm):
        ml_weight = 1.0
        num_sample = tokens.shape[0]
        key = self.RHYTHM if cp_on_rhythm else self.PITCH
        probs = F.softmax(output, dim=-1)
        filename = f'cp_{key}_{epoch}_{i}.dat'

        with open(os.path.join(self.minicpbp_music_path, filename), 'w') as f:
            for j in range(num_sample):
                f.write(' '.join(map(str, tokens[j].tolist()[:i])))
                f.write(' ' + ' '.join(map(str, probs[j].tolist())))
                f.write('\n')

        cmd = self._get_java_command(key, filename, num_sample, i, ml_weight, beamWidth)

        # Set JavaNeeded line to True and sent args with json
        with open(os.path.join(self.minicpbp_music_path, "JavaNeeded.txt"), "w") as f:
            f.write("True")
        with open(os.path.join(self.minicpbp_music_path, 'JavaArgs.txt'), 'w') as f:
            f.write(f"{i},{filename}")

        # get belief propagation probs from minicpbp
        current_dir_backup = os.getcwd()
        os.chdir(self.minicpbp_working_dir)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        print(f'New Java MiniCPBP process created')
        os.chdir(current_dir_backup)
        return process

    
    '''
    This is the function that communicates with the java process which runs in background. It is called at each step when we 
    sample a token with constraints
    '''
    def _cpbp_java_popen(self, java_process, tokens, output, epoch, beam_index, i, device, cp_on_rhythm, beam_search=False):
        ml_weight = 1.0

        key = self.RHYTHM if cp_on_rhythm else self.PITCH
        i_title = f'Popen__{key}______i:{i}_______w:{ml_weight}_______'
        print(i_title)

        num_sample = tokens.shape[0]
        probs = F.softmax(output, dim=-1)
        filename = f'cp_{key}_{epoch}_{i}.dat'

        # create .dat files for java CP model
        with open(os.path.join(self.minicpbp_music_path, filename), 'w') as f:
            for j in range(num_sample):
                f.write(' '.join(map(str, tokens[j].tolist()[:i])))
                f.write(' ' + ' '.join(map(str, probs[j].tolist())))
                f.write('\n')

        # Set arguments to JavaArgs
        with open(os.path.join(self.minicpbp_music_path,'JavaArgs.txt'), 'w') as f:
            f.write(f"{i},{filename},{beam_index}")

        # Set JavaNeeded line to True
        with open(os.path.join(self.minicpbp_music_path, "JavaNeeded.txt"), "w") as f:
            f.write("True")
            print("Sent to java")

        # Wait for Java to set JavaNeeded line to False
        max_timeout = 1000 if cp_on_rhythm else 150     # timeout needs to be different because rhythm process tends to be longer
        timeout = 0
        java_running = True
        while java_running:
            with open(os.path.join(self.minicpbp_music_path, "JavaNeeded.txt"), "r") as f:
                if f.readline().strip() == "False":
                    print('Java ended')
                    java_running = False
            timeout += 1
            time.sleep(0.01)
            if timeout > max_timeout:
                print(f'Java MiniCPBP failed: timeout')
                line = java_process.stderr.readline()
                if line:
                    print('Read last log error: ')
                    print(line)
                    line = java_process.stderr.readline()
                    while line:
                        print(line)
                        line = java_process.stderr.readline()
                line = java_process.stdout.readline()
                if line:
                    print(f'Read last log : {line}')
                    line = java_process.stdout.readline()
                    while line:
                        print(line)
                        line = java_process.stdout.readline()
                # RHYTHM : replace probs with [1,0,0] --> java failed so just generate rest tokens
                if str(key) == 'rhythm':
                    for j in range(num_sample):
                        probs_cp = torch.as_tensor(list(map(float, (['1.0', '0.0', '0.0'])))).to(device)
                        probs[j] = probs_cp
                # PITCH : replace probs with [0,0,0,...,0,1] --> java failed so just generate rest tokens
                elif str(key) == 'pitch':
                    for j in range(num_sample):
                        probs_list = ['0.0' for i in range(49)]
                        probs_list.append('1.0')
                        probs_cp = torch.as_tensor(list(map(float, (probs_list))))
                        probs[j] = probs_cp
                return probs, True

        # Error Handling
        if java_process.returncode != 0 and java_process.returncode != None:       
            print(f'Java MiniCPBP failed: {java_process.stderr.read()} - ')

            # RHYTHM : replace probs with [1,0,0] --> java failed so just generate rest tokens
            if str(key) == 'rhythm':
                for j in range(num_sample):
                    probs_cp = torch.as_tensor(list(map(float, (['1.0', '0.0', '0.0'])))).to(device)
                    probs[j] = probs_cp

            # PITCH : replace probs with [0,0,0,...,0,1] --> java failed so just generate rest tokens
            elif str(key) == 'pitch':
                for j in range(num_sample):
                    probs_list = ['0.0' for i in range(49)]
                    probs_list.append('1.0')
                    probs_cp = torch.as_tensor(list(map(float, (probs_list))))
                    probs[j] = probs_cp

            java_process.kill()
            return probs, True

        # Java process didn't return any 'error' but we still check the logs
        else:
            # replace probs with new ones from belief propagation (Oracle.txt can be used to debug)
            with open(os.path.join(self.minicpbp_music_path, filename[:-4] + '_results.dat'), 'r') as f, open(
                    'Oracle.txt', 'a') as f2, open(os.path.join(self.minicpbp_music_path, filename[:-4] + '_logs.dat'),
                                                   'r') as flogs:
                f2.write(i_title + '\n')
                for j in range(num_sample):
                    line = f.readline()
                    print('\n Read file : ')
                    print(line.split())
                    print('\n Read Logs :')
                    newline_logs = flogs.readline()
                    while newline_logs != '':
                        print(newline_logs)
                        newline_logs = flogs.readline()
                    print('\n')
                    
                    probs_cp = torch.as_tensor(list(map(float, (line.split())))).to(device)

                    probs[j] = probs_cp
                    f2.write(line)

        # if sampling rhythm token, direclty get the token value
        if cp_on_rhythm and not(beam_search):
            idx = torch.multinomial(probs, 1).squeeze()  # sampling from marginals of cp solver
            print("idx = " + str(idx.item()) + "\n")
            return idx, False

        # else return the distribution and model.py will sample from the top 5 probs
        return probs, False
    
    def _get_java_command(self, key, filename, num_sample, i, ml_weight, beamWidth):
        constraintsRhythm = self.config[self.RHYTHM]['model']['userconstraints']
        constraintsPitch = self.config[self.PITCH]['model']['userconstraints']
        return self._get_java_command_rhythm_global(filename, num_sample, i, ml_weight, constraintsRhythm, beamWidth) if key is self.RHYTHM else self._get_java_command_pitch_global(filename, num_sample, i, ml_weight, constraintsPitch, beamWidth)

    def _get_java_command_rhythm_global(self, filename, num_sample, i, ml_weight, userConstraints, beamWidth):
        cp_model_name = self.config[self.RHYTHM]['model']['name']
        if 'durationModel' in cp_model_name or 'jep' in cp_model_name or 'test' in cp_model_name:
            return f'{self.BASIC_JAVA_CMD}{cp_model_name} {filename} {num_sample} {i} {ml_weight} {userConstraints} {beamWidth}'.split()
        else:
            raise Exception(f'Not a valid cp global model on {self.RHYTHM}')

    def _get_java_command_pitch_global(self, filename, num_sample, i, ml_weight, userConstraints, beamWidth):
        cp_model_name = self.config[self.PITCH]['model']['name']
        k = self.config[self.PITCH]['model']['k']
        nb_bars_group = self.config[self.PITCH]['weight_variation']['nb_bars_group']
        min_weight = self.config[self.PITCH]['weight_variation']['weight_min']
        if 'pitchModel' in cp_model_name or 'jep' in cp_model_name:
            return f'{self.BASIC_JAVA_CMD}{cp_model_name} {filename} {num_sample} {i} {self.FILENAME_TOKEN_RHYTHM} {min_weight} {k} {userConstraints} {beamWidth}'.split()
        else:
            raise Exception(f'Not a valid cp global model on {self.PITCH}')