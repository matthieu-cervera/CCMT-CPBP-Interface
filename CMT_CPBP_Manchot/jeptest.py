'''
Imports
'''
import numpy as np
from cp import ConstraintProgramming as CP
import torch
import torch.nn as nn
import torch.nn.functional as F
import dill
import random
from utils.hparams import HParams
from model import ChordConditionedMelodyTransformer as CMT
from loss import FocalLoss

'''
This python file is used by JEP to sample new token using the CMT.
'''


def initialize_model(seed, batch_size = 1):
    seed_set(seed)
    # Load model (CMT class deserialize)
    with open('model.pkl', 'rb') as f:
        model = dill.load(f)
    with open('chord.pkl', 'rb') as f:
        chord = dill.load(f)
    with open('prime_rhythm.pkl', 'rb') as f:
        prime_rhythm = dill.load(f)

    chord_hidden = model.chord_forward(chord)
    pad_length = model.max_len - prime_rhythm.size(1)
    rhythm_pad = torch.zeros([batch_size, pad_length], dtype=torch.long).to(prime_rhythm.device)
    rhythm_result = torch.cat([prime_rhythm, rhythm_pad], dim=1)
    return(model, rhythm_result, chord_hidden)


def forward_CMT(model, iteration, rhythm_result, chord_hidden, seed):
    rhythm_dec_result = model.rhythm_forward(rhythm_result.long(), chord_hidden, attention_map=False, masking=True)
    rhythm_out = model.rhythm_outlayer(rhythm_dec_result['output'])
    rhythm_out = model.log_softmax(rhythm_out)
    return(rhythm_out[:,iteration-1,:].detach().numpy())


def sample_token(iteration, probs_cp, rhythm_out, rhythm_result, seed):
    probs_np = np.zeros(len(probs_cp))
    for i in range(len(probs_cp)):
        probs_np[i] = probs_cp[i]

    probs =torch.tensor(probs_np)

    if iteration == 0:
        # Clear the contents of the file
        with open('debug_idx.txt', 'a') as file:
            pass

    with open('debug_idx.txt', 'a') as file:
        file.write(f'iteration{iteration} probs')
        file.write(str(probs))

    idx = torch.multinomial(probs, 1).squeeze()  # sampling from marginals of cp solver
    rhythm_result[:,iteration] = idx
    return(rhythm_result)


def tensor_to_np(tensor):
    return(tensor.numpy().tolist())


def tensor_values_by_index(tensor, index):
    try:
        nptensor = tensor.numpy()
    except AttributeError:
        nptensor = tensor
    return(float(nptensor[:,index]))

def initialize_model_pitch(seed, batch_size=1):
    seed_set(seed)

    # Load model (CMT class deserialize) and rhythm result
    with open('model.pkl', 'rb') as f:
        model = dill.load(f)
    with open('chord.pkl', 'rb') as f:
        chord = dill.load(f)
    with open('rhythm_result.pkl', 'rb') as f:
        rhythm_result = dill.load(f)
    with open('prime_pitch.pkl', 'rb') as f:
        prime_pitch = dill.load(f)

    chord_hidden = model.chord_forward(chord)

    # Compute rhythm embedding
    rhythm_dict = model.rhythm_forward(rhythm_result, chord_hidden, attention_map=False, masking=True)
    rhythm_out = model.rhythm_outlayer(rhythm_dict['output'])
    rhythm_out = model.log_softmax(rhythm_out)
    idx = torch.argmax(rhythm_out[:, -1, :], dim=1)
    rhythm_temp = torch.cat([rhythm_result[:, 1:], idx.unsqueeze(-1)], dim=1)
    rhythm_enc_dict = model.rhythm_forward(rhythm_temp, chord_hidden, attention_map=False, masking=False)
    rhythm_emb = rhythm_enc_dict['output']


    pad_length = model.max_len - prime_pitch.size(1)
    pitch_pad = torch.ones([batch_size, pad_length], dtype=torch.long).to(prime_pitch.device)
    pitch_pad *= (model.num_pitch - 1)
    pitch_result = torch.cat([prime_pitch, pitch_pad], dim=1)
    return(model, pitch_result, rhythm_result, rhythm_emb, chord_hidden)

def pitchForward_CMT(model, iteration, pitch_result, rhythm_emb, chord_hidden):
    pitch_emb = model.pitch_emb(pitch_result)
    emb = torch.cat([pitch_emb, chord_hidden[0], chord_hidden[1], rhythm_emb], -1)
    emb *= torch.sqrt(torch.tensor(model.hidden_dim, dtype=torch.float))
    pitch_dict = model.pitch_forward(emb, attention_map=False)


    if iteration ==0:
            marginals = F.softmax(pitch_dict['output'][:, iteration, :], dim=-1)
    else:
       marginals = F.softmax(pitch_dict['output'][:, iteration - 1, :], dim=-1)

    with open('debug_idx.txt', 'a') as file:
        file.write(f'\n marginals : ')
        file.write(str(marginals.detach().numpy()) + "\n")

    return(marginals.detach().numpy())


def sample_pitch_token(iteration, probs_cp, pitch_result):

    probs_np = np.zeros(len(probs_cp))
    for i in range(len(probs_cp)):
        probs_np[i] = probs_cp[i]


    with open('debug_idx.txt', 'a') as file:
        file.write(f'marginals miniCPBP : ')
        file.write(str(probs_np) + "\n")

    probs = torch.tensor(probs_np)

    topk_probs, topk_idxs = torch.topk(probs, 5, dim=-1)

    with open('debug_idx.txt', 'a') as file:
        file.write(f'\n sampling pitch token at iteration {iteration} \n')
        file.write(str(topk_probs) + " ")
        file.write(str(topk_idxs) + "\n")

    idx = torch.gather(topk_idxs, 0, torch.multinomial(topk_probs, 1)).squeeze()
    with open('debug_idx.txt', 'a') as file:
        file.write(f'idx : {idx} \n')
    pitch_result[:, iteration] = idx
    return(pitch_result)



def seed_set(seed):
    if seed > 0:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)