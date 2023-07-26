CCMT\_CPBP and User Interface
=========

CCMT-CPBP is a neuro-symbolic artificial intelligence system (combining machine learning and constraint programming) that generates musical melodies based on given chords while providing more control over these melodies than the base transformer. This project is the direct following of Virasone Manibod's project CMT-CPBP (), with computational optimization, new specific constraints and new implementations for the model. 

It is a modified version of CCMT (Chord Conditioned Melody Transformer, <https://ieeexplore.ieee.org/abstract/document/9376975>) that includes beam search and where constraints can be imposed on the generated melodies using constraint programming (CP) solver MiniCPBP <https://jair.org/index.php/jair/article/view/11487>.

The User Interface allows a user to choose a sample from the database or upload any sample to try the CCMT-CPBP. The user can specify which constraints he wants to apply to the melody and several other hyperparameters (seed, beam width, etc...). He can then listen to the generated sample an compare it to the base sample. The interface also allows the user to play to a Turing test with all the generated and base samples. 

A updated and deployed version of the Turing test is for the moment available here thanks to Dunstan Becht : <https://music-ccmt-cpbp.highhopes.fr>. You can try with 5 random samples from the database and see your score. This website was developped for statistics purposes as it is relevant to rate the quality of generated art with human evaluation. It is not meant for phone users (but can be still used with a smartphone).


Requirements
------------

### System
* Python:
 3 or above.
* Java:
 1.8 or above.
* JDK:
 1.8 or above (this is to execute Maven; it still allows you to build against 1.3
 and prior JDKs).
* Maven:
 3.9 or above 
* JEP:
 used to optimize computation with the MiniCPBP solver <https://github.com/ninia/jep>
* MuseScore:
 3 or above (this is to compute the music scores of the sample and to display them to the user).
* Cmake:
 3.26.4 or above (this is for MuseScore to work).
* SQLite:
 3.40.1 or above (for the flask app)


### Python 3
The required libraries for python are inside the requirements.txt file. You can also access to the requirements for the CCMT-CPBP without the interface at CCMT_CPBP_Manchot/requirements_model.txt



File Architecture Overview
--------------------------

### ***CCMT-CPBP-Interface*** Folder
The top-level folder houses essential components and modules that constitute the core of the application.

- ***app folder:*** This folder contains the primary application code, static assets, templates, and other supporting files.

- ***CMT_CPBP_Manchot folder:*** This folder is dedicated to the CCMT_CPBP model. It can work on its own.

- **app.db:** The `app.db` file is the SQLite database used by the application to store and manage samples, users and votes.

- **config.py:** The `config.py` file contains essential configuration settings for the Flask app.

- **run.py:** The `run.py` file serves as the entry point for the Flask app, initiating the application's execution in debug mode.

### ***app*** folder
The `app` folder is the central hub of the Flask application, containing its main components.

- ***static folder:*** The `static` folder houses static assets, such as CSS files for styling, JavaScript scripts, images and music samples that are directly served to clients.

- ***templates folder:*** The `templates` folder stores HTML templates used to render web pages.

- **views.py:** The `views.py` file contains Python functions, also known as views or routes, responsible for handling incoming requests and generating responses. It is the core of the Flask app.

- **modelDB.py** Configuration of flask SQLalchemy tables.

- **preprocess.py** Create pkl files from MIDI files (the MIDI file needs to have two parts - melody and chords).

- **midi_files_proc_music21.py** Create two tracks MIDI files from MIDI file and other useful functions.

- **config_commands.py** Config file for views. Change paths for the flask application to run correctly


### ***CCMT_CPBP_Manchot*** folder

- **run_CCMT_CPBP.py:** The `run_CCMT_CPBP.py` file serves as a script for the CCMT-CPBP model.

- **trainer.py:** The `trainer.py` file contains utilities for loading, training, sampling and saving models.

- **model.py:** The `model.py` file is the implementation of CCMT and of the beam search.

- **cp.py:** This is the implementation to call MiniCPBP from the CCMT.

- **jeptest.py** This python file is used by JEP (java embedding python) in java. It allows to do all the sampling operations that rely on the CCMT directly from java.

- **dataset.py:** Loads preprocessed pkl data.

- **generation_metrics.py:** Generates the metrics calculated on the melodies.

- **loss.py:** Defines loss functions

- **layers.py:** Self attention block and relative multi-head attention layers

- **hparams.yaml:** The `hparams.yaml` file contains hyperparameters and other settings such as paths to load data or save results for the CCMT_CPBP model.

- ***pkl_files_EWLD folder:*** The `pkl_files_EWLD` folder contains all the samples used to train, or test the model related to the CCMT-CPBP project. In the current hparams files, this is where the loaders search for pkl data.

- ***minicpbp folder:*** The `minicpbp` folder contains all the MiniCPBP solver implementation from <https://github.com/PesantGilles/MiniCPBP/tree/master>, and jep package. The implemented constraints and models can be found in `minicpbp/src/main/java/minicpbp/`.

- ***results folder:*** The `results` folder serves as a storage location for output results and trained checkpoints generated during the execution of the CCMT_CPBP model.

- ***python3-midi-master*** No changes have been made in the midi library for python 3 from the original code <https://github.com/louisabraham/python3-midi>


### ***minicpbp/src/main/java/minicpbp/examples*** folder

- **durationModel.java:** This is the base model for CP on rhythm. This model contains all the already implemented constraints and works with python subprocess.Popen

- **pitchModel.java:** This is the base model for CP on pitch. It works the same way as the durationModel

- **samplingRhythm.java:** This is the model that samples directly the rhythm from java, using JEP and `jeptest.py`.

- **samplingPitch.java:** This is the model that samples directly the pitch from java, using JEP and `jeptest.py`. 

- ***data/MusicCP folder:*** This folder contains all files serving the data exchange between java and python (sampled data, CP solver results, logs, javaNeeded.txt, javaArgs.txt)



Model
------

### CCMT

CCMT (Chord Conditioned Melody Transformer) is a machine-learning model for generating a melody according to a given chord sequence. It is a transformer composed of a chord encoder, a rhythm decoder and a pitch decoder. As in the base paper, I trained the transformer on the EWLD dataset in two stages (first the rhythm decoder is trained, then the rhythm decoder is used to encode the rhythm sequence and the pitch decoder is trained).
CCMT's original code: <https://github.com/ckycky3/CMT-pytorch>.

### Beam Search

Beam Search is a heuristic search algorithm widely used in artificial intelligence tasks. It explores multiple potential solutions simultaneously by maintaining a fixed-size set of the most promising candidates called the 'beam.' During each step, the algorithm expands the set of candidates by considering all possible next steps and retaining only the top candidates based on assigned probabilities (in the project, top candidates can be sampled or just choosen by max probability). This process efficiently prunes less promising solutions, striking a balance between exploration and exploitation and providing approximate solutions to complex problems with large search spaces. In art generation, it allows us to enlarge and vary our resulting melodies. In a way, it simulates human creativity.
Beam search also allows to generate a melody with 'hard feasible' constraints. Without it, the sampling process could lead to a dead-end (a melody that doesn't satisfy the constraint) but with it, other melodies from the beam could end satisfying the constraint.

### MiniCPBP

MiniCPBP (constraint programming belief propagation) is a constraint programming solver in which belief propagation (BP) has been added to the MiniCP solver. BP is a message-passing algorithm between constraints and probabilities, designed to perform inference on graphical models. It approximates the marginal distribution of individual variables from their joint distribution (the probability that a variable value is part of a feasible solution). MiniCPBP can handle different types of constraints on a given problem and efficiently search for solutions that satisfy these constraints. 
The commit version of MiniCPBP is: `6bd0144997998f069c67b5f6feb61341fcba8b48`. However, it may be recommended to use the more recent one, refer to <https://github.com/PesantGilles/MiniCPBP>. 


### CCMT-CPBP

The intuition of the project is to add the constraints during inference to avoid having to re-train the model each time. Constraint programming takes effect as soon as a token is to be sampled. For each token to be generated (at each time step, first for the rhythm and then for the pitch), the transformer returns a probability distribution of the possible values of the token. This distribution is injected into the MiniCPBP solver in the form of an 'oracle' constraint to preserve the music style learned by the CCMT, along with other constraints given on the melody. The solver then returns a modified distribution, taking into account the constraints and the initial distribution. When beam search is activated, it uses the modified distribution to create and choose candidates for the beam.


### MGEval framework

Some functions in `mgeval\core.py` from the MGEval framework has been modified so that the metrics were calculated on the melody track of the .mid file. MGEval's original code: <https://github.com/RichardYang40148/mgeval>.


Training CMT
------------

The checkpoint of CMT trained on the EWLD dataset and used in our experiments is given in `results\idx002\model\`. If you wish to train your own checkpoint please see CCMT's original code.

Beam Search
-----------
You can activate beam search on the rhythm or on the pitch, and you can choose whether you prefer to sample or to choose by max probability the candidates sequences. In our tests, it seems like the beam search is best used on rhythm, as the pitch will also be different.

MiniCPBP
--------

Check the README in the `minicpbp\`. 

### Constraints implemented

The constraints are implemented in the .java files. Each constraint is characterized by its name and has the following syntax : `constraintName:StartingBar:EndingBar;` or if more informations are needed `constraintName:StartingBar:EndingBar:PointedToken:value:value:value;` or for separated constraints  `Sep-constraintName:StartingBar:EndingBar:StartingSeparatedBar:EndingSeparatedBar;`

### Implement a new constraint

To add a new constraint, just add the constraint name and code logic in the conditional statement of the java models. 
Then execute `mvn package` command in the `minicpbp\` folder.


Sampling CCMT
-------------

Generate the melodies by executing run_CCMT_CPBP.py. Make sure to include the `--load_rhythm`, `--sample options` and `--constraints`.


Generating melodies with the interface 
---------------------------------------

The interface allows to generate melodies easily and to compare the results. If you wish to run the flask app on localhost, set the port in the `run.py` and in the `app/static/js/config.js` file and then run `run.py`. The app will be accessible at ***https://localhost:port/***.
