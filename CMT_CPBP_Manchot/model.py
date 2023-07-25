'''
Imports
'''
import torch
import torch.nn as nn
import torch.nn.functional as F
import random

import subprocess
import numpy as np
import time
from cp import ConstraintProgramming as CP
from layers import DynamicPositionEmbedding, SelfAttentionBlock
from torch.autograd import Variable
import dill
import os
from utils import logger


'''
SAMPLING FUNCTIONS :
-----------------------------------------------------------------------------------------------------------------------------------
1) sampling : classic CMT sampling, requesting (if activated) the marginals from miniCPBP using functions from cp.py and java files
    it uses subprocess.popen(), allowing the java process to stay alive during all the sampling and avoid recreating the solver and
    the process at each token generation
    Uses javaNeeded.txt and javaArgs.txt files to know if it's python or java turn and to pass args
-----------------------------------------------------------------------------------------------------------------------------------
2) sampling_beam_rhythm : uses beam search to generate the rhythm sequence. Pitch is generated like the base sampling function.
    Both token generations can use java the same way as the base sampling function
-----------------------------------------------------------------------------------------------------------------------------------
3) sampling_beam_pitch : uses beam search to generate the pitch sequence. Rhythm is generated like the base sampling function.
Both token generations can use java the same way as the base sampling function
-----------------------------------------------------------------------------------------------------------------------------------
4) sampling_java : When activated, samples the melody directly in java using JEP (java embedding python) module to make the 
    needed computes. Useful and more computationally efficient when there are constraints for both pitch and rhythm.
    Uses different java files (samplingPitch.java & samplingRhythm.java) and pkl files to store python variables throughout the 
    process (chord.pkl, model.pkl, prime_pitch.pkl, prime_rhythm.pkl, rhythm_result.pkl)
-----------------------------------------------------------------------------------------------------------------------------------
'''

class ChordConditionedMelodyTransformer(nn.Module):
    def __init__(self, num_pitch=89, frame_per_bar=16, num_bars=8,
                 chord_emb_size=128, pitch_emb_size=128, hidden_dim=128,
                 key_dim=128, value_dim=128, num_layers=6, num_heads=4,
                 input_dropout=0.0, layer_dropout=0.0, attention_dropout=0.0, cp=None):
        super(ChordConditionedMelodyTransformer, self).__init__()

        self.max_len = frame_per_bar * num_bars
        self.frame_per_bar = frame_per_bar
        self.num_chords = 12
        self.num_pitch = num_pitch
        self.num_rhythm = 3

        # self.rhythm_emb_size = chord_emb
        self.chord_emb_size = chord_emb_size
        self.rhythm_emb_size = pitch_emb_size // 8
        self.pitch_emb_size = pitch_emb_size
        self.chord_hidden = 7 * (pitch_emb_size // 32)  # 2 * chord_hidden + rhythm_emb = rhythm_hidden
        self.rhythm_hidden = 9 * (pitch_emb_size // 16)   # 2 * chord_hidden + rhythm_hidden = pitch_emb
        self.hidden_dim = hidden_dim

        # embedding layer
        self.chord_emb = nn.Parameter(torch.randn(self.num_chords, self.chord_emb_size,
                                                  dtype=torch.float, requires_grad=True))
        self.rhythm_emb = nn.Embedding(self.num_rhythm, self.rhythm_emb_size)
        self.pitch_emb = nn.Embedding(self.num_pitch, self.pitch_emb_size)

        lstm_input = self.chord_emb_size
        self.chord_lstm = nn.LSTM(lstm_input, self.chord_hidden, num_layers=1,
                                  batch_first=True, bidirectional=True)
        self.rhythm_pos_enc = DynamicPositionEmbedding(self.rhythm_hidden, self.max_len)
        self.pos_encoding = DynamicPositionEmbedding(self.hidden_dim, self.max_len)

        # embedding dropout
        self.emb_dropout = nn.Dropout(input_dropout)

        # Decoding layers
        rhythm_params = (
            2 * self.chord_hidden + self.rhythm_emb_size,
            self.rhythm_hidden,
            key_dim // 4,
            value_dim // 4,
            num_heads,
            self.max_len,
            False,      # include succeeding elements' positional embedding also
            layer_dropout,
            attention_dropout
        )
        self.rhythm_decoder = nn.ModuleList([
            SelfAttentionBlock(*rhythm_params) for _ in range(num_layers)
        ])
        
        pitch_params = (
            2 * self.pitch_emb_size,
            self.hidden_dim,
            key_dim,
            value_dim,
            num_heads,
            self.max_len,
            True,       # preceding only
            layer_dropout,
            attention_dropout
        )
        self.pitch_decoder = nn.ModuleList([
            SelfAttentionBlock(*pitch_params) for _ in range(num_layers)
        ])

        # output layer
        self.rhythm_outlayer = nn.Linear(self.rhythm_hidden, self.num_rhythm)
        self.pitch_outlayer = nn.Linear(self.hidden_dim, self.num_pitch)
        self.log_softmax = nn.LogSoftmax(dim=-1)

        self.cp = CP(cp, frame_per_bar=self.frame_per_bar)

    def init_lstm_hidden(self, batch_size):
        h0 = Variable(torch.zeros(2, batch_size, self.chord_hidden))
        c0 = Variable(torch.zeros(2, batch_size, self.chord_hidden))
        return (h0, c0)

    # rhythm : time_len + 1   (input & target)
    # pitch : time_len      (input only)
    # chord : time_len + 1  (input & target)
    def forward(self, rhythm, pitch, chord, attention_map=False, rhythm_only=False):
        # chord_hidden : time_len   (target timestep)
        chord_hidden = self.chord_forward(chord)

        rhythm_dec_result = self.rhythm_forward(rhythm[:, :-1], chord_hidden, attention_map, masking=True)
        rhythm_out = self.rhythm_outlayer(rhythm_dec_result['output'])
        rhythm_out = self.log_softmax(rhythm_out)
        result = {'rhythm': rhythm_out}

        if not rhythm_only:
            rhythm_enc_result = self.rhythm_forward(rhythm[:, 1:], chord_hidden, attention_map, masking=False)
            rhythm_emb = rhythm_enc_result['output']
            pitch_emb = self.pitch_emb(pitch)
            emb = torch.cat([pitch_emb, chord_hidden[0], chord_hidden[1], rhythm_emb], -1)
            emb *= torch.sqrt(torch.tensor(self.hidden_dim, dtype=torch.float))
            pitch_output = self.pitch_forward(emb, attention_map)
            result['pitch'] = pitch_output['output']

            if attention_map:
                result['weights_rdec'] = rhythm_dec_result['weights']
                result['weights_renc'] = rhythm_enc_result['weights']
                result['weights_pitch'] = pitch_output['weights']
        return result

    def chord_forward(self, chord):
        size = chord.size()
        chord_emb = torch.matmul(chord.float(), self.chord_emb)

        h0, c0 = self.init_lstm_hidden(size[0])
        self.chord_lstm.flatten_parameters()
        chord_out, _ = self.chord_lstm(chord_emb, (h0.to(chord.device), c0.to(chord.device)))
        chord_for = chord_out[:, 1:, :self.chord_hidden]
        chord_back = chord_out[:, 1:, self.chord_hidden:]
        return chord_for, chord_back
    
    def rhythm_forward(self, rhythm, chord_hidden, attention_map=False, masking=True):
        rhythm_emb = self.rhythm_emb(rhythm)
        rhythm_emb = torch.cat([rhythm_emb, chord_hidden[0], chord_hidden[1]], -1)
        rhythm_emb *= torch.sqrt(torch.tensor(self.rhythm_hidden, dtype=torch.float))
        rhythm_emb = self.rhythm_pos_enc(rhythm_emb)
        rhythm_emb = self.emb_dropout(rhythm_emb)
        
        weights = []
        for _, layer in enumerate(self.rhythm_decoder):
            result = layer(rhythm_emb, attention_map, masking)
            rhythm_emb = result['output']
            if attention_map:
                weights.append(result['weight']) 
        
        result = {'output': rhythm_emb}
        if attention_map:
            result['weights'] = weights
        
        return result

    def pitch_forward(self, pitch_emb, attention_map=False, masking=True):
        emb = self.pos_encoding(pitch_emb)
        emb = self.emb_dropout(emb)

        # pitch model
        pitch_weights = []
        for _, layer in enumerate(self.pitch_decoder):
            pitch_result = layer(emb, attention_map, masking)
            emb = pitch_result['output']
            if attention_map:
                pitch_weights.append(pitch_result['weight'])

        # output layer
        output = self.pitch_outlayer(emb)
        output = self.log_softmax(output)
        
        result = {'output': output}
        if attention_map:
            result['weights'] = pitch_weights
        
        return result


    

    '''
    Classic CMT-CPBP sampling (cp.profiler helps computing the execution time)
    '''
    def sampling(self, prime_rhythm, prime_pitch, chord, epoch, topk=None, attention_map=False):
        chord_hidden = self.chord_forward(chord)
        
        #============================================== RHYTHM ==============================================
        # batch_size * prime_len * num_outputs
        batch_size = prime_pitch.size(0)
        pad_length = self.max_len - prime_rhythm.size(1)
        rhythm_pad = torch.zeros([batch_size, pad_length], dtype=torch.long).to(prime_rhythm.device)
        rhythm_result = torch.cat([prime_rhythm, rhythm_pad], dim=1)

        # sampling phase
        for i in range(prime_rhythm.size(1), self.max_len):
            rhythm_dec_result = self.rhythm_forward(rhythm_result, chord_hidden, attention_map, masking=True)
            rhythm_out = self.rhythm_outlayer(rhythm_dec_result['output'])
            rhythm_out = self.log_softmax(rhythm_out)

            if i == prime_rhythm.size(1):
                with open('debug_idx_nojav.txt', 'w') as file:
                    pass

            if topk is None:
                idx = torch.argmax(rhythm_out[:, i - 1, :], dim=1)

            else:
                if self.cp.config['rhythm']['activate']:
                    start = time.time()

                    # Call the java processes with beam_width = 1 and beam_index = 0 because there is no beam search
                    if self.cp.java_process is None:
                        self.cp.java_process = self.cp.create_java_process(rhythm_result, rhythm_out[:, i - 1, :], epoch, 1, i, prime_pitch.device, True)

                    idx, error = self.cp._cpbp_java_popen(self.cp.java_process, rhythm_result,
                                                          rhythm_out[:, i - 1, :], epoch, 0, i,
                                                          prime_pitch.device, True)

                    end = time.time()
                    self.cp.profiler.append(end-start)

                    if error:
                        print('error in popen java')
                        self.cp.java_process = None
                        top3_probs, top3_idxs = torch.topk(rhythm_out[:, i - 1, :], 3, dim=-1)
                        idx = torch.gather(top3_idxs, 1, torch.multinomial(F.softmax(top3_probs, dim=-1), 1)).squeeze()

                else:

                    top3_probs, top3_idxs = torch.topk(rhythm_out[:, i - 1, :], 3, dim=-1)
                    idx = torch.gather(top3_idxs, 1, torch.multinomial(F.softmax(top3_probs, dim=-1), 1)).squeeze()


            rhythm_result[:, i] = idx

        if len(self.cp.profiler) != 0:
            print(f'ExecTime - mean : {sum(self.cp.profiler)/len(self.cp.profiler)}')
        self.cp.profiler = []

        if not(self.cp.java_process is None):
            self.cp.java_process.kill()
        self.cp.java_process = None

        #============================================== PITCH ==============================================
        rhythm_dict = self.rhythm_forward(rhythm_result, chord_hidden, attention_map, masking=True)
        rhythm_out = self.rhythm_outlayer(rhythm_dict['output'])
        rhythm_out = self.log_softmax(rhythm_out)
        idx = torch.argmax(rhythm_out[:, -1, :], dim=1)
        rhythm_temp = torch.cat([rhythm_result[:, 1:], idx.unsqueeze(-1)], dim=1)
        rhythm_enc_dict = self.rhythm_forward(rhythm_temp, chord_hidden, attention_map, masking=False)
        rhythm_emb = rhythm_enc_dict['output']
        if self.cp.config['pitch']['activate']:
            self.cp.save_rhythm_token(rhythm_result)

        pad_length = self.max_len - prime_pitch.size(1)
        pitch_pad = torch.ones([batch_size, pad_length], dtype=torch.long).to(prime_pitch.device)
        pitch_pad *= (self.num_pitch - 1)
        pitch_result = torch.cat([prime_pitch, pitch_pad], dim=1)
        for i in range(prime_pitch.size(1), self.max_len):
            pitch_emb = self.pitch_emb(pitch_result)
            emb = torch.cat([pitch_emb, chord_hidden[0], chord_hidden[1], rhythm_emb], -1)
            emb *= torch.sqrt(torch.tensor(self.hidden_dim, dtype=torch.float))
            pitch_dict = self.pitch_forward(emb, attention_map)
            if topk is None:
                idx = torch.argmax(pitch_dict['output'][:, i - 1, :], dim=1)
            else:
                if self.cp.config['pitch']['activate']:

                    start = time.time()

                    # Call the java processes with beam_width = 1 and beam_index = 0 because there is no beam search
                    if self.cp.java_process is None:
                        self.cp.java_process = self.cp.create_java_process(pitch_result, pitch_dict['output'][:, i - 1, :], epoch, 1, i, prime_pitch.device, False)

                    probs_cp, error = self.cp._cpbp_java_popen(self.cp.java_process, pitch_result,
                                                          pitch_dict['output'][:, i - 1, :], epoch, 0, i,
                                                          prime_pitch.device, False)

                    end = time.time()
                    self.cp.profiler.append(end - start)

                    if error:
                        print('error in popen java')
                        self.cp.java_process = None
                        idx = torch.argmax(pitch_dict['output'][:, i - 1, :], dim=1)
                    else:
                        topk_probs, topk_idxs = torch.topk(probs_cp, topk, dim=-1)
                        idx = torch.gather(topk_idxs, 1, torch.multinomial(topk_probs, 1)).squeeze()
                else:
                    topk_probs, topk_idxs = torch.topk(pitch_dict['output'][:, i - 1, :], topk, dim=-1)
                    idx = torch.gather(topk_idxs, 1, torch.multinomial(F.softmax(topk_probs, dim=-1), 1)).squeeze()

                    if i==0:
                        test =pitch_dict['output'][:, i - 1, :]
                        print(f'probs_cp={test}')
                        print(f'\nprobs={topk_probs} and idx={topk_idxs}')

            pitch_result[:, i] = idx

        if len(self.cp.profiler) != 0:
            print(f'ExecTime - mean : {sum(self.cp.profiler)/len(self.cp.profiler)}')
        if not (self.cp.java_process is None):
            self.cp.java_process.kill()
        result = {'rhythm': rhythm_result,
                  'pitch': pitch_result}
        if attention_map:
            result['weights_rdec'] = rhythm_dict['weights']
            result['weights_renc'] = rhythm_enc_dict['weights']
            result['weights_pitch'] = pitch_dict['weights']

        return result


    '''
    Uses beam search to generate the rhythm sequence. In the beam search, new sequences can be chosen by max marginal (base 
    beam search) or by sampling.
    '''
    def sampling_beam_rhythm(self, prime_rhythm, prime_pitch, chord, epoch, topk=None, beam_width=0, attention_map=False):
        
        #========================================== RHYTHM (beam search) ==========================================
        results = []    # store the W best sequences chosen by the beam search into the results list

        chord_hidden = self.chord_forward(chord)

        # batch_size * prime_len * num_outputs
        batch_size = prime_pitch.size(0)
        pad_length = self.max_len - prime_rhythm.size(1)
        rhythm_pad = torch.zeros([batch_size, pad_length], dtype=torch.long).to(prime_rhythm.device)
        rhythm_result = torch.cat([prime_rhythm, rhythm_pad], dim=1)

        chosen_sequences = [torch.cat([prime_rhythm, rhythm_pad], dim=1) for _ in range(beam_width)]
        chosen_marginals = [1 for _ in range(beam_width)]
        # sampling phase
        for i in range(prime_rhythm.size(1), self.max_len):
            candidates_sequences = []
            candidates_marginals = []

            # Initialize beams
            if i==prime_rhythm.size(1):
                rhythm_dec_result = self.rhythm_forward(rhythm_result, chord_hidden, attention_map, masking=True)
                rhythm_out = self.rhythm_outlayer(rhythm_dec_result['output'])
                rhythm_out = self.log_softmax(rhythm_out)

                # Get marginals from CP Solver
                if self.cp.config['rhythm']['activate']:
                    if self.cp.java_process is None:
                        self.cp.java_process = self.cp.create_java_process(rhythm_result, rhythm_out[:, i - 1, :], epoch, beam_width, i, prime_pitch.device, True)

                    marginals_out, error = self.cp._cpbp_java_popen(self.cp.java_process, rhythm_result,
                                                          rhythm_out[:, i - 1, :], epoch, 0, i,
                                                          prime_pitch.device, True, True)
                    marginals_out = marginals_out.tolist()[0]

                    if error:
                        print('error in popen java')
                        self.cp.java_process = None
                        marginals_out = F.softmax(rhythm_out[:, i - 1, :], dim=-1).tolist()[0]
                # Get marginals from CMT
                else:
                    marginals_out = F.softmax(rhythm_out[:, i - 1, :], dim=-1).tolist()[0]

                # Create Candidate Sequences and Marginals
                for idx, marginal in enumerate(marginals_out):
                    candidates_marginals.append(marginal)
                    new_candidate = rhythm_result.detach().clone()
                    new_candidate[:, i] = idx
                    candidates_sequences.append(new_candidate)

            else:

                for j, candidate in enumerate(chosen_sequences):
                    rhythm_dec_result = self.rhythm_forward(candidate, chord_hidden, attention_map, masking=True)
                    rhythm_out = self.rhythm_outlayer(rhythm_dec_result['output'])
                    rhythm_out = self.log_softmax(rhythm_out)

                    # Get marginals from CP Solver
                    if self.cp.config['rhythm']['activate']:
                        if self.cp.java_process is None:
                            self.cp.java_process = self.cp.create_java_process(candidate, rhythm_out[:, i - 1, :], epoch, beam_width, i, prime_pitch.device, True)

                        marginals_out, error = self.cp._cpbp_java_popen(self.cp.java_process, candidate,
                                                            rhythm_out[:, i - 1, :], epoch, j, i,
                                                            prime_pitch.device, True, True)
                        marginals_out = marginals_out.tolist()[0]

                        if error:
                            print('error in popen java')
                            self.cp.java_process = None
                            marginals_out = F.softmax(rhythm_out[:, i - 1, :], dim=-1).tolist()[0]

                    # Get marginals from CMT
                    else:
                        marginals_out = F.softmax(rhythm_out[:, i - 1, :], dim=-1).tolist()[0]
                
                    # Create Candidate Sequences and Marginals
                    for idx, marginal in enumerate(marginals_out):
                        candidates_marginals.append(marginal * chosen_marginals[j])
                        new_candidate = candidate.detach().clone()
                        new_candidate[:, i] = idx
                        candidates_sequences.append(new_candidate)

            # Normalize marginals
            print(candidates_marginals)
            z = np.sum(candidates_marginals)
            nb_candidates = len(candidates_marginals)
            weighted_probs = [prob ** 0.9 for prob in candidates_marginals]     # close up the marginals
            candidates_marginals = weighted_probs / np.sum(weighted_probs)

            #==================================== BASE BEAM SEARCH ==================================
            # Get the indices that would sort the marginals in ascending order
            sorted_indices = sorted(range(nb_candidates), key=lambda x: - candidates_marginals[x])

            # Sort the sequences and marginals based on the sorted indices
            sorted_sequences = [candidates_sequences[i] for i in sorted_indices]
            sorted_marginals = [candidates_marginals[i] for i in sorted_indices]

            for k in range(beam_width):
                candidate, marginal = sorted_sequences[k % nb_candidates], sorted_marginals[k % nb_candidates]
                chosen_sequences[k] = candidate
                chosen_marginals[k] = marginal

            # ================================ SAMPLING BEAM SEARCH ================================
            # # Sample indices from the candidate marginals
            # sampled_indices = random.choices(range(nb_candidates), weights=candidates_marginals, k=beam_width)
            # print(f'SAMPLED INDICES : {sampled_indices}')
            # for k, sampled_index in enumerate(sampled_indices):
            #     chosen_sequences[k] = candidates_sequences[sampled_index]
            #     chosen_marginals[k] = candidates_marginals[sampled_index]


        if not(self.cp.java_process is None):
            self.cp.java_process.kill()
        self.cp.java_process = None

        #============================================== PITCH ==============================================
        emb_tensors = []
        for beam in range(beam_width):
            rhythm_dict = self.rhythm_forward(chosen_sequences[beam], chord_hidden, attention_map, masking=True)
            rhythm_out = self.rhythm_outlayer(rhythm_dict['output'])
            rhythm_out = self.log_softmax(rhythm_out)
            idx = torch.argmax(rhythm_out[:, -1, :], dim=1)
            rhythm_temp = torch.cat([chosen_sequences[beam][:, 1:], idx.unsqueeze(-1)], dim=1)
            rhythm_enc_dict = self.rhythm_forward(rhythm_temp, chord_hidden, attention_map, masking=False)
            rhythm_emb = rhythm_enc_dict['output']
            emb_tensors.append(rhythm_emb)

            if self.cp.config['pitch']['activate']:
                self.cp.save_rhythm_token(chosen_sequences[beam])

            pad_length = self.max_len - prime_pitch.size(1)
            pitch_pad = torch.ones([batch_size, pad_length], dtype=torch.long).to(prime_pitch.device)
            pitch_pad *= (self.num_pitch - 1)
            pitch_result = torch.cat([prime_pitch, pitch_pad], dim=1)
            for i in range(prime_pitch.size(1), self.max_len):
                pitch_emb = self.pitch_emb(pitch_result)
                emb = torch.cat([pitch_emb, chord_hidden[0], chord_hidden[1], rhythm_emb], -1)
                emb *= torch.sqrt(torch.tensor(self.hidden_dim, dtype=torch.float))
                pitch_dict = self.pitch_forward(emb, attention_map)
                if topk is None:
                    idx = torch.argmax(pitch_dict['output'][:, i - 1, :], dim=1)
                else:
                    if self.cp.config['pitch']['activate']:

                        start = time.time()

                        # This is to solve a bug I didn't understand where the process times out when sampling pitch on a new beam for i=0
                        if (i==0) and (beam>0):
                            if self.cp.java_process != None:
                                self.cp.java_process.kill()
                            self.cp.java_process = self.cp.create_java_process(pitch_result, pitch_dict['output'][:, i - 1, :], epoch, beam_width, i, prime_pitch.device, False)

                            
                        if self.cp.java_process is None:
                            self.cp.java_process = self.cp.create_java_process(pitch_result, pitch_dict['output'][:, i - 1, :], epoch, beam_width, i, prime_pitch.device, False)

                        probs_cp, error = self.cp._cpbp_java_popen(self.cp.java_process, pitch_result,
                                                              pitch_dict['output'][:, i - 1, :], epoch, beam, i,
                                                              prime_pitch.device, False)

                        if error:
                            print('error in popen java')
                            self.cp.java_process = None
                            idx = torch.argmax(pitch_dict['output'][:, i - 1, :], dim=1)
                        else:
                            topk_probs, topk_idxs = torch.topk(probs_cp, topk, dim=-1)
                            print(probs_cp, topk_probs)
                            idx = torch.gather(topk_idxs, 1, torch.multinomial(topk_probs, 1)).squeeze()
                    else:
                        topk_probs, topk_idxs = torch.topk(pitch_dict['output'][:, i - 1, :], topk, dim=-1)
                        idx = torch.gather(topk_idxs, 1, torch.multinomial(F.softmax(topk_probs, dim=-1), 1)).squeeze()

                pitch_result[:, i] = idx

            if len(self.cp.profiler) != 0:
                print(f'ExecTime - mean : {sum(self.cp.profiler)/len(self.cp.profiler)}')
            if not (self.cp.java_process is None):
                self.cp.java_process.kill()
            result = {'rhythm': chosen_sequences[beam],
                      'pitch': pitch_result}
            if attention_map:
                result['weights_rdec'] = rhythm_dict['weights']
                result['weights_renc'] = rhythm_enc_dict['weights']
                result['weights_pitch'] = pitch_dict['weights']

            results.append(result)
        return results


    '''
    Uses beam search to generate the pitch sequence. In the beam search, new sequences can be chosen by max marginal (base 
    beam search) or by sampling.
    '''
    def sampling_beam_pitch(self, prime_rhythm, prime_pitch, chord, epoch, topk=None, beam_width=0, attention_map=False):
        results = []    # store the W best sequences chosen by the beam search into the results list

        chord_hidden = self.chord_forward(chord)

        #============================================== RHYTHM ==============================================
        # batch_size * prime_len * num_outputs
        batch_size = prime_pitch.size(0)
        pad_length = self.max_len - prime_rhythm.size(1)
        rhythm_pad = torch.zeros([batch_size, pad_length], dtype=torch.long).to(prime_rhythm.device)
        rhythm_result = torch.cat([prime_rhythm, rhythm_pad], dim=1)

        # sampling phase
        for i in range(prime_rhythm.size(1), self.max_len):
            rhythm_dec_result = self.rhythm_forward(rhythm_result, chord_hidden, attention_map, masking=True)
            rhythm_out = self.rhythm_outlayer(rhythm_dec_result['output'])
            rhythm_out = self.log_softmax(rhythm_out)

            if topk is None:
                idx = torch.argmax(rhythm_out[:, i - 1, :], dim=1)
            else:
                if self.cp.config['rhythm']['activate']:

                    if self.cp.java_process is None:
                        self.cp.java_process = self.cp.create_java_process(rhythm_result, rhythm_out[:, i - 1, :], epoch, 1, i, prime_pitch.device, True)

                    idx, error = self.cp._cpbp_java_popen(self.cp.java_process, rhythm_result,
                                                          rhythm_out[:, i - 1, :], epoch, 0, i,
                                                          prime_pitch.device, True)

                    if error:
                        print('error in popen java')
                        self.cp.java_process = None
                        top3_probs, top3_idxs = torch.topk(rhythm_out[:, i - 1, :], 3, dim=-1)
                        idx = torch.gather(top3_idxs, 1, torch.multinomial(F.softmax(top3_probs, dim=-1), 1)).squeeze()

                else:
                    top3_probs, top3_idxs = torch.topk(rhythm_out[:, i - 1, :], 3, dim=-1)
                    idx = torch.gather(top3_idxs, 1, torch.multinomial(F.softmax(top3_probs, dim=-1), 1)).squeeze()
            rhythm_result[:, i] = idx


        if not(self.cp.java_process is None):
            self.cp.java_process.kill()
        self.cp.java_process = None

        #============================================== PITCH (beam search) ==============================================
        rhythm_dict = self.rhythm_forward(rhythm_result, chord_hidden, attention_map, masking=True)
        rhythm_out = self.rhythm_outlayer(rhythm_dict['output'])
        rhythm_out = self.log_softmax(rhythm_out)
        idx = torch.argmax(rhythm_out[:, -1, :], dim=1)
        rhythm_temp = torch.cat([rhythm_result[:, 1:], idx.unsqueeze(-1)], dim=1)
        rhythm_enc_dict = self.rhythm_forward(rhythm_temp, chord_hidden, attention_map, masking=False)
        rhythm_emb = rhythm_enc_dict['output']

        if self.cp.config['pitch']['activate']:
            self.cp.save_rhythm_token(rhythm_result)

        pad_length = self.max_len - prime_pitch.size(1)
        pitch_pad = torch.ones([batch_size, pad_length], dtype=torch.long).to(prime_pitch.device)
        pitch_pad *= (self.num_pitch - 1)
        pitch_result = torch.cat([prime_pitch, pitch_pad], dim=1)

        chosen_sequences = [pitch_result for _ in range(beam_width)]
        chosen_marginals = [1 for _ in range(beam_width)]

        for i in range(prime_pitch.size(1), self.max_len):
            candidates_sequences = []
            candidates_marginals = []

            # Initialize beams
            if i == prime_pitch.size(1):
                pitch_emb = self.pitch_emb(pitch_result)
                emb = torch.cat([pitch_emb, chord_hidden[0], chord_hidden[1], rhythm_emb], -1)
                emb *= torch.sqrt(torch.tensor(self.hidden_dim, dtype=torch.float))
                pitch_dict = self.pitch_forward(emb, attention_map)
                
                # Get marginals from CP Solver
                if self.cp.config['pitch']['activate']:
                    if self.cp.java_process is None:
                        self.cp.java_process = self.cp.create_java_process(pitch_result, pitch_dict['output'][:, i - 1, :], epoch, beam_width, i, prime_pitch.device, False)

                    marginals_out, error = self.cp._cpbp_java_popen(self.cp.java_process, pitch_result,
                                                          pitch_dict['output'][:, i - 1, :], epoch, 0, i,
                                                          prime_pitch.device, False)
                    marginals_out = marginals_out.tolist()[0]
                    
                    if error:
                        print('error in popen java')
                        self.cp.java_process = None
                        marginals_out = F.softmax(pitch_dict['output'][:, i - 1, :], dim=1).tolist()[0]

                # Get marginals from CMT
                else:
                    marginals_out = F.softmax(pitch_dict['output'][:, i - 1, :], dim=1).tolist()[0]

                # Create Candidate Sequences and Marginals
                for idx, marginal in enumerate(marginals_out):
                    candidates_marginals.append(marginal)
                    new_candidate = pitch_result.detach().clone()
                    new_candidate[:, i] = idx
                    candidates_sequences.append(new_candidate)


            # search for candidates
            else:

                for j, candidate in enumerate(chosen_sequences):
                    pitch_emb = self.pitch_emb(candidate)
                    emb = torch.cat([pitch_emb, chord_hidden[0], chord_hidden[1], rhythm_emb], -1)
                    emb *= torch.sqrt(torch.tensor(self.hidden_dim, dtype=torch.float))
                    pitch_dict = self.pitch_forward(emb, attention_map)

                    if self.cp.config['pitch']['activate']:
                        if self.cp.java_process is None:
                            self.cp.java_process = self.cp.create_java_process(candidate, pitch_dict['output'][:, i - 1, :], epoch, beam_width, i, prime_pitch.device, False)

                        marginals_out, error = self.cp._cpbp_java_popen(self.cp.java_process, candidate,
                                                                pitch_dict['output'][:, i - 1, :], epoch, j, i,
                                                                prime_pitch.device, False)
                        marginals_out = marginals_out.tolist()[0]
                        
                        if error:
                            print('error in popen java')
                            self.cp.java_process = None
                            marginals_out = F.softmax(pitch_dict['output'][:, i - 1, :], dim=1).tolist()[0]

                    # Get marginals from CMT
                    else:
                        marginals_out = F.softmax(pitch_dict['output'][:, i - 1, :], dim=1).tolist()[0]

                    # Create Candidate Sequences and Marginals 
                    for idx, marginal in enumerate(marginals_out):
                        candidates_marginals.append(marginal * chosen_marginals[j])
                        new_candidate = candidate.detach().clone()
                        new_candidate[:, i] = idx
                        candidates_sequences.append(new_candidate)

            # Normalize marginals
            z = np.sum(candidates_marginals)
            nb_candidates = len(candidates_marginals)
            weighted_probs = [prob ** 0.9 for prob in candidates_marginals]
            candidates_marginals = weighted_probs / np.sum(weighted_probs)

            #==================================== BASE BEAM SEARCH ==================================
            # Get the indices that would sort the marginals in ascending order
            sorted_indices = sorted(range(nb_candidates), key=lambda x: - candidates_marginals[x])

            # Sort the sequences and marginals based on the sorted indices
            sorted_sequences = [candidates_sequences[i] for i in sorted_indices]
            sorted_marginals = [candidates_marginals[i] for i in sorted_indices]

            for k in range(beam_width):
                candidate, marginal = sorted_sequences[k % nb_candidates], sorted_marginals[k % nb_candidates]
                chosen_sequences[k] = candidate
                chosen_marginals[k] = marginal

            #================================== SAMPLING BEAM SEARCH ================================
            # # Sample indices from the candidate marginals
            # sampled_indices = random.choices(range(nb_candidates), weights=candidates_marginals, k=beam_width)
            # print(f'SAMPLED INDICES : {sampled_indices}')
            # for k, sampled_index in enumerate(sampled_indices):
            #     chosen_sequences[k] = candidates_sequences[sampled_index]
            #     chosen_marginals[k] = candidates_marginals[sampled_index]
                  
        if not (self.cp.java_process is None):
            self.cp.java_process.kill()

        for beam in range(beam_width):
            result = {'rhythm': rhythm_result,
                      'pitch': chosen_sequences[beam]}
            if attention_map:
                result['weights_rdec'] = rhythm_dict['weights']
                result['weights_renc'] = rhythm_enc_dict['weights']
                result['weights_pitch'] = pitch_dict['weights']


            results.append(result)
        return results

    
    '''
    Samples the melody directly in java using JEP (java embedding python) module
    ''' 
    def sampling_with_java(self, prime_rhythm, prime_pitch, chord, epoch, seed, topk=None, attention_map=False):
        
        #============================================== RHYTHM ==============================================
        # Save python variables into pkl files to access them inside JEP
        with open('model.pkl', 'w+b') as f:
            dill.dump(self, f)
        with open('chord.pkl', 'w+b') as f:
            dill.dump(chord, f)
        with open('prime_rhythm.pkl', 'w+b') as f:
            dill.dump(prime_rhythm, f)

        # Execute java code
        current_dir_backup = os.getcwd()
        os.chdir(self.cp.minicpbp_working_dir)
        cp_model_name = 'samplingRhythm'
        userConstraints = self.cp.config[self.cp.RHYTHM]['model']['userconstraints']
        cmd = f'{self.cp.BASIC_JAVA_CMD}{cp_model_name} {userConstraints} {seed}'.split()
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        batch_size = prime_pitch.size(0)
        pad_length = self.max_len - prime_rhythm.size(1)

        os.chdir(current_dir_backup)

        rhythm_pad = torch.zeros([batch_size, pad_length], dtype=torch.long).to(prime_rhythm.device)
        rhythm_result = torch.cat([prime_rhythm, rhythm_pad], dim=1)

        if process.returncode != 0:
            print(f'Java MiniCPBP rhythm failed: {process.stderr}')
        else :
            print(f'java miniCPBP rhythm succeed, process returncode :{process.returncode} - {process.stdout} - {process.stderr}')
            with open(os.path.join(self.cp.minicpbp_music_path, 'results_rhythm.txt'), 'r') as f:
                line = f.readline()
                tokens = line.split()
                print('\n Read file : ')
                print(tokens)
                for j in range(128):
                    rhythm_result[:,j] = float(tokens[j])

        #============================================== PITCH ==============================================
        # Save python variables into pkl files to access them inside JEP
        with open('prime_pitch.pkl', 'w+b') as f:
            dill.dump(prime_pitch, f)
        with open('rhythm_result.pkl', 'w+b') as f:
            dill.dump(rhythm_result, f)

        # Execute java code
        os.chdir(self.cp.minicpbp_working_dir)
        cp_model_name = 'samplingPitch'
        userConstraints = self.cp.config[self.cp.PITCH]['model']['userconstraints']
        k = self.cp.config[self.cp.PITCH]['model']['k']
        cmd = f'{self.cp.BASIC_JAVA_CMD}{cp_model_name} {userConstraints} {seed} {k}'.split()
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        batch_size = prime_pitch.size(0)
        pad_length = self.max_len - prime_pitch.size(1)

        os.chdir(current_dir_backup)

        pitch_pad = torch.zeros([batch_size, pad_length], dtype=torch.long).to(prime_pitch.device)
        pitch_result = torch.cat([prime_pitch, pitch_pad], dim=1)

        if process.returncode != 0:
            print(f'\nJava MiniCPBP pitch failed: {process.stderr}')
        else:
            print(
                f'\njava miniCPBP pitch succeed, process returncode :{process.returncode} - {process.stdout} - {process.stderr}')
            with open(os.path.join(self.cp.minicpbp_music_path, 'results_pitch.txt'), 'r') as f:
                line = f.readline()
                tokens = line.split()
                print('\n Read file : ')
                print(tokens)
                for j in range(128):
                    pitch_result[:, j] = float(tokens[j])

        result = {'rhythm': rhythm_result,
                  'pitch': pitch_result}
        if attention_map:
            result['weights_rdec'] = rhythm_dict['weights']
            result['weights_renc'] = rhythm_enc_dict['weights']
            result['weights_pitch'] = pitch_dict['weights']
        return result