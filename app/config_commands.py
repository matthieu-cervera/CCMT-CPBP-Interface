
'''
CONFIG
    Config file for views. Change paths for the flask application to run correctly
'''
import os

class Commands():
    # software paths
    python_path = '/usagers4/p118640/anaconda3/bin/python'
    mscore_path = '/usagers4/p118640/.local/bin/musescore-portable'
    
    # CMT-CPBP paths
    CMT_CPBP_folder_name = 'CMT_CPBP_Manchot'
    pkl_folder_rel_path = '/CMT_CPBP_Manchot/pkl_files_EWLD/instance_pkl_8bars_fpb16_48p_ckey'
    results_path = '/usagers4/p118640/User_Interface_Project-main/CMT_CPBP_Manchot/results/idx002/sampling_results/epoch_100/'
    results_rel_path = 'CMT_CPBP_Manchot/results/idx002/sampling_results/epoch_100/'
    hparams_rel_path = 'CMT_CPBP_Manchot/hparams-gen.yaml'
    sampling_file_path = '/usagers4/p118640/User_Interface_Project-main/CMT_CPBP_Manchot/run_CCMT_CPBP.py'

    
    # CMT-CPBP fixed parameters
    idx = 2
    restore_epoch = 100
    
    # Flask app paths
    static_images_path = '/usagers4/p118640/User_Interface_Project-main/app/static/images' 
    midi_repo_rel_path = 'app/static/midi_files_repository'
    midi_repo_path = '/usagers4/p118640/User_Interface_Project-main/' + midi_repo_rel_path

    def __init__(self):
        self.application_path = os.getcwd()

    def midi2png(self, path_to_midi, path_to_png):
        command = [self.mscore_path, path_to_midi,  '--export-to',  path_to_png, '-T', '0']
        return(command)

    def midi2pkl(self, username):
        command = [self.python_path, self.application_path, '/app/preprocess.py', '--root_dir', self.application_path, '/users/', username, '/midi_files_checking', '--midi_dir', 'chords_melody_midi']
        return(command)


    def CMT_CPBP_command(self, seed):
        command = f'{self.python_path} {self.sampling_file_path} --idx {self.idx} --gpu_index 0 --ngpu 1 --optim_name adam --restore_epoch {self.restore_epoch} --seed {seed} --load_rhythm --sample --constraints'
        return(command)