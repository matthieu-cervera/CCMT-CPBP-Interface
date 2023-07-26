package minicpbp.examples;

import minicpbp.cp.Factory;
import minicpbp.engine.core.Constraint;
import minicpbp.engine.core.IntVar;
import minicpbp.engine.core.Solver;
import minicpbp.util.exception.InconsistencyException;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Scanner;

import java.io.BufferedReader;
import java.io.FileWriter;


import static minicpbp.cp.Factory.*;

import jep.NDArray;
import jep.Jep;
import jep.JepException;
import jep.SharedInterpreter;
import jep.python.PyObject;


public class samplingRhythm {

    // Variables to pick from arguments
    public static final int nbVar = 128;
    public static final int nbVarPerBar = 16;
    public static final int nbBar = 8;
    public static final int nbVal = 3;

    public static final int onsetToken = 2;
    public static final int holdToken = 1;
    public static final int restToken = 0;

    public static void main(String[] args) {

        //retrieve useful static args
        //String sequencePrefixFile = args[0];
        int seed = Integer.parseInt(args[1]);
        //double minOracleWeight = Double.parseDouble(args[4]);
        String userConstraints = args[0];
        try (Jep jepInterpreter = new SharedInterpreter()){

            // Create the solver
            Solver cp = Factory.makeSolver();

            IntVar[] x = new IntVar[nbVar];
            for (int i = 0; i < nbVar; i++) {
                x[i] = makeIntVar(cp, 0, nbVal - 1);
                x[i].setName("x" + "[" + i + "]");
            }

            // import libraries and set working directory
            jepInterpreter.eval("import os");
            jepInterpreter.eval("os.chdir(\"/usagers4/p118640/User_Interface_Project-main/CMT_CPBP_Manchot/\")");
            jepInterpreter.eval("import sys");
            jepInterpreter.eval("sys.path.append(\"/usagers4/p118640/User_Interface_Project-main/CMT_CPBP_Manchot/\")");
            jepInterpreter.eval("import jeptest");

            jepInterpreter.set("seed", seed);

            // initialize python variables
            jepInterpreter.eval("model, rhythm_result, chord_hidden = jeptest.initialize_model(seed)");
            Object model = jepInterpreter.getValue("model");
            Object rhythm_result = jepInterpreter.getValue("rhythm_result");
            Object chord_hidden = jepInterpreter.getValue("chord_hidden");





            // Sampling phase
            for (int nextTokenIdx = 0; nextTokenIdx<nbVar; nextTokenIdx ++){

                // Get marginals from CMT layers - forward
                jepInterpreter.set("model", model);
                jepInterpreter.set("rhythm_result", rhythm_result);
                jepInterpreter.set("chord_hidden", chord_hidden);
                jepInterpreter.set("iteration", nextTokenIdx);
                jepInterpreter.eval("marginals = jeptest.forward_CMT(model, iteration, rhythm_result, chord_hidden, seed)");
                
                //NDArray marginals_ndarray = (NDArray) jepInterpreter.getValue("marginals");
                Object rhythm_out = jepInterpreter.getValue("marginals");
                float[] marginals = new float[nbVal];
                float[] result = new float[nbVar];
                
                for (int j=0; j<nbVal; j++){
                    jepInterpreter.set("index", j);
                    jepInterpreter.eval("float_value = jeptest.tensor_values_by_index(marginals, index)");
                    jepInterpreter.eval("result_value = jeptest.tensor_values_by_index(rhythm_result, index)");
                    Double double_value = (Double) jepInterpreter.getValue("float_value");
                    float float_value = double_value.floatValue();
                    Double result_value_double = (Double) jepInterpreter.getValue("result_value");
                    float result_value = result_value_double.floatValue();
                    marginals[j] = float_value;
                    result[j] = result_value;
                }
                for (int j=nbVal; j<nbVar ; j++){
                    jepInterpreter.set("index", j);
                    jepInterpreter.eval("result_value = jeptest.tensor_values_by_index(rhythm_result, index)");
                    Double result_value_double = (Double) jepInterpreter.getValue("result_value");
                    float result_value = result_value_double.floatValue();
                    result[j] = result_value;
                }

                // Transform the rhythm 'result' tensor into double[] variable
                //jepInterpreter.eval("result = jeptest.tensor_to_np(rhythm_result)");
                //NDArray result_ndarray = (NDArray) jepInterpreter.getValue("result");
                //float[] result = (float[]) jepInterpreter.getValue("result");
                //float[] result = (float[]) result_ndarray.getData();


                // Adding constraints to marginals
                                  //  double[] minicpbp_probs = new double[nbVal];

                                  //  for (int i = 0; i < nbVal; i++) {
                                 //       minicpbp_probs[i] =  marginals[i];
                                 //   }


                 // essayer de save marginals et result pour vérifier pq les contraintes sont insatisfiables

                // post constraints and solve the cp problem for the pointed token
                double oracleWeight = 1.0;
                double[] minicpbp_probs = solveCSP(x, nextTokenIdx, nbVar, nbBar, marginals, result, cp, userConstraints, oracleWeight);


                // CMT token generation
                //jepInterpreter.set("probs", marginals);
                jepInterpreter.set("probs", minicpbp_probs);
                jepInterpreter.set("rhythm_out", rhythm_out);
                jepInterpreter.eval("rhythm_result = jeptest.sample_token(iteration, probs, rhythm_out, rhythm_result, seed)");
                rhythm_result = jepInterpreter.getValue("rhythm_result");
            }

            // Get final result
            //jepInterpreter.eval("rhythm_result_np = jeptest.tensor_to_np(rhythm_result)");
           // NDArray rhythm_result_ndarray = (NDArray) jepInterpreter.getValue("rhythm_result_np");
            //float[] results = (float[]) rhythm_result_ndarray.getData();


            // Write results for python code
            FileWriter fileWriter = new FileWriter("minicpbp/src/main/java/minicpbp/examples/data/MusicCP/results_rhythm.txt", false);
            for (int i = 0; i < nbVar; i++) {
                jepInterpreter.set("index", i);
                jepInterpreter.eval("rhythm_result_token = jeptest.tensor_values_by_index(rhythm_result, index)");
                Double result_value_double = (Double) jepInterpreter.getValue("rhythm_result_token");
                fileWriter.write(result_value_double + " ");
            }
            jepInterpreter.close();
            fileWriter.close();

            }

    catch (JepException e) {
       System.err.println("Error -1: " + e.getMessage()) ;
       e.printStackTrace();}
    catch (Exception e) {
        System.err.println("Error 0: " + e.getMessage()) ;
        e.printStackTrace();}
    }

    // process constraints string, post constraints and solve the CP
    public static double[] solveCSP(IntVar[] x, int nextTokenIdx, int nbVar, int nbBar, float[] CMTMarginals, float[] result, Solver cp, String userConstraints, double oracleWeight){
        try {
            double[] minicpbp_marginals = new double[nbVal];
            
            // set value of previously fixed vars
            for (int i = 0; i < nextTokenIdx; i++) {
                x[i].assign((int) Math.floor(result[i]));
            }

            // set initial scores (marginals) for variable being fixed (next token in the sequence) according to NN
            double[] scores = new double[nbVal];
            int[] vals = new int[nbVal];
            for (int i = 0; i < nbVal; i++) {
                scores[i] = CMTMarginals[i];
                vals[i] = i;
            }

            Constraint orac = Factory.oracle(x[nextTokenIdx], vals, scores);
            orac.setWeight(oracleWeight);
            cp.post(orac);

            // Read user constraints
            String[] userConstraintsList = userConstraints.split(";");
            String[] constraintNames = new String[userConstraintsList.length];
            int[][] constraintBars = new int[userConstraintsList.length][2];
            int[][] constraintSepBars = new int[userConstraintsList.length][2];
            int[] constraintTokenValues = new int[userConstraintsList.length];
            ArrayList<int[]> constraintRhythmValues = new ArrayList<>();
            for (int i = 0; i < userConstraintsList.length; i++) {
                String[] split_constraint = userConstraintsList[i].split(":");
                constraintNames[i]=split_constraint[0];
                int[] bar = {Integer.parseInt(split_constraint[1]),Integer.parseInt(split_constraint[2])};

                if (split_constraint[0].contains("Sep")){       // This is a constraint with separate measures
                    int[] sepBar = {Integer.parseInt(split_constraint[3]),Integer.parseInt(split_constraint[4])};
                    constraintSepBars[i] = sepBar;
                    int[] foo_rhythm = {};   
                    constraintRhythmValues.add(foo_rhythm);
                }
                else if (split_constraint[0].contains("Token")){     // This isn't a constraint on measures, but on a token    
                    int token = Integer.parseInt(split_constraint[3]);
                    constraintTokenValues[i] = token;
                    
                    if (split_constraint.length > 4){                    int[] rhythms = new int[split_constraint.length - 4];
                        for (int j = 4; j < split_constraint.length; j++) {
                            rhythms[j - 4] = Integer.parseInt(split_constraint[j]);
                        }
                     
                        constraintRhythmValues.add(rhythms);
                    }
                    else {
                        int[] foo_rhythm = {};   
                        constraintRhythmValues.add(foo_rhythm);
                    }
                }
                else{
                    int[] foo_rhythm = {};   
                    constraintRhythmValues.add(foo_rhythm);
                }

                
                constraintBars[i] = bar;
            }

            //###################################################
            //##### DURATION CONSTRAINTS OVER A SINGLE SPAN #####
            //###################################################

            // find starting index of ongoing note and duration of latest completed note
            int latestDuration = 0;
            int ongoingNoteStartIdx = nextTokenIdx;
            int idx = nextTokenIdx - 1;
            while (idx >= 0 && x[idx].min() == holdToken) idx--; // pass through ongoing note
            if (idx >= 0 && x[idx].min() == onsetToken) { // move past ongoing note
                ongoingNoteStartIdx = idx;
                idx--;
            }
            while (idx >= 0 && x[idx].min() == restToken) idx--; // find end of lastest completed note
            while (idx >= 0 && x[idx].min() != onsetToken) { // pass through latest note
                latestDuration++;
                idx--;
            }
            if (idx >= 0) latestDuration++; // include onset in duration

            //###################################################
            //############ APPLY USER CONSTRAINTS ###############
            //###################################################

            int currentBar = (nextTokenIdx / nbVarPerBar) + 1 ;

            // Duration constraints names : durationAllsame, durationAllsameFixed8, durationAllDiff, durationSpeedUp, durationSlowDown
            for (int k=0; k < constraintNames.length; k++){

                boolean activateConstraint = ((constraintBars[k][0]<=currentBar) && (currentBar<=constraintBars[k][1])) || ((constraintSepBars[k][0]<=currentBar) && (currentBar<=constraintSepBars[k][1]));

                if (activateConstraint) {
                    int groupSize = 1 + constraintBars[k][1] - constraintBars[k][0];
                    //System.out.println("Iteration "+ nextTokenIdx + "Constraint Activated " + constraintNames[k] + " ");
                    if (constraintNames[k].equals("durationAllDiff")) {
                        // AllDiff
                        IntVar[] o = new IntVar[groupSize];
                        for (int i = 0 ; i < groupSize; i++) {
                            o[i] = makeIntVar(cp, 0, nbVarPerBar);
                            o[i].setName("o" + "[" + i + "]");
                        }
                        for (int i = 0 ; i < groupSize; i++) {
                            IntVar[] x_subset = Arrays.copyOfRange(x, (constraintBars[k][0] - 1 + i) * nbVarPerBar, (constraintBars[k][0] + i) * nbVarPerBar);
                            cp.post(Factory.among(x_subset, onsetToken, o[i]));
                        }
                        cp.post(Factory.allDifferent(o));
                    }

                    // remove transitions from the automaton according to the constraint
                    if (constraintNames[k].equals("durationAllSame")) {

                        int[][] constraintsAutomaton = initAutomaton(groupSize);
                        // all-the-same constraint
                        for (int i = 1; i < latestDuration; i++) { // must continue note
                            constraintsAutomaton[i][onsetToken] = -1;
                            constraintsAutomaton[i][restToken] = -1;
                        }
                        constraintsAutomaton[latestDuration][holdToken] = -1; // must end note

                        // post constraint about note durations on remaining span, including the ongoing note
                        IntVar[] x_subset = Arrays.copyOfRange(x, (constraintBars[k][0]-1)*nbVarPerBar, constraintBars[k][1]*nbVarPerBar);  // 2nd arg is excluding
                        cp.post(Factory.regular(x_subset, constraintsAutomaton));
                    }

                    if (constraintNames[k].equals("durationSpeedUp")) {

                        int[][] constraintsAutomaton = initAutomaton(groupSize);

                        // increasing constraint
                        for (int i = 1; i <= latestDuration; i++) { // must continue note
                            constraintsAutomaton[i][onsetToken] = -1;
                            constraintsAutomaton[i][restToken] = -1;
                        }

                        // post constraint about note durations on remaining span, including the ongoing note
                        IntVar[] x_subset = Arrays.copyOfRange(x, ongoingNoteStartIdx, constraintBars[k][1]*nbVarPerBar);
                        cp.post(Factory.regular(x_subset, constraintsAutomaton));
                    }

                    if (constraintNames[k].equals("durationSlowDown")) {

                        int[][] constraintsAutomaton = initAutomaton(groupSize);

                        int subsetStartingId = ongoingNoteStartIdx;

                        if ((constraintBars[k][0]-1)*nbVarPerBar == nextTokenIdx){	// This is the first iteration of the activated constraint
                            subsetStartingId = (constraintBars[k][0]-1)*nbVarPerBar;
                            latestDuration = groupSize * nbVarPerBar - 1 ;	// we put the latestDuration to a high number on purpose
                        }

                        if ((constraintBars[k][0]-1)*nbVarPerBar > ongoingNoteStartIdx){ // the ongoing note didn't start in the constrained bars
                            subsetStartingId = (constraintBars[k][0]-1)*nbVarPerBar;
                        }

                        // decreasing constraint
                        switch (latestDuration) {
                            case 0: // nothing to do: no completed note yet
                                break;
                            case 1:
                                constraintsAutomaton[0][onsetToken] = -1; // no note is short enough
                                break;
                            case 2:
                                constraintsAutomaton[latestDuration - 1][holdToken] = -1; // must end note
                                constraintsAutomaton[latestDuration - 1][onsetToken] = -1; // should not begin a new note
                                break;
                            default: // >= 3
                                constraintsAutomaton[1][onsetToken] = -1;	// if the previous token generated is an onset, we can't generate another one
                                constraintsAutomaton[latestDuration - 1][holdToken] = -1; // must end note
                        }

                        // post constraint about note durations on remaining span, including the ongoing note
                        IntVar[] x_subset = Arrays.copyOfRange(x, subsetStartingId, constraintBars[k][1]*nbVarPerBar);
                        cp.post(Factory.regular(x_subset, constraintsAutomaton));
                    }

                    if (constraintNames[k].contains("durationAllSameFixed")) {
                        int[][] constraintsAutomaton = initAutomaton(groupSize);

                        // Find the fixed duration wanted by the user
                        int fixedDuration = Integer.parseInt(constraintNames[k].split("ed")[1]);

                        // all-the-same constraint
                        for (int i = 1; i < fixedDuration; i++) { // must continue note
                            constraintsAutomaton[i][onsetToken] = -1;
                            constraintsAutomaton[i][restToken] = -1;
                        }
                        constraintsAutomaton[fixedDuration][holdToken] = -1; // must end note

                        // post constraint about note durations on remaining span, including the ongoing note
                        IntVar[] x_subset = Arrays.copyOfRange(x, (constraintBars[k][0]-1)*nbVarPerBar, constraintBars[k][1]*nbVarPerBar);
                        cp.post(Factory.regular(x_subset, constraintsAutomaton));
                    }

                    if (constraintNames[k].contains("maximumSilence")) {
                        // Find the maximum silence proportion wanted by the user
                        int silencePercentage = Integer.parseInt(constraintNames[k].split("Silence")[1]);
                        int silenceMaxNumber = groupSize * nbVarPerBar * silencePercentage/100 ;

                        // Constraint Atmost
                        IntVar[] x_subset = Arrays.copyOfRange(x, (constraintBars[k][0]-1)*nbVarPerBar, constraintBars[k][1]*nbVarPerBar);
                        cp.post(Factory.atmost(x_subset, restToken, silenceMaxNumber));
                    }


                    if (constraintNames[k].equals("Sep-durationSameStructure")) {
                        // Apply the same rhythmic structure on bars and separate bars
                        IntVar[] x_subset = Arrays.copyOfRange(x, (constraintBars[k][0] - 1) * nbVarPerBar, (constraintSepBars[k][1]) * nbVarPerBar);
                        for (int i = 0 ; i < groupSize * nbVarPerBar; i++) {
                            cp.post(Factory.equal(x_subset[i], x_subset[(constraintSepBars[k][0] - constraintBars[k][0]) * nbVarPerBar + i]));
                        }
                    }

                    if (constraintNames[k].equals("durationTokenSingle")) {
                        x[constraintTokenValues[k]].assign(onsetToken); 
                    }

                    if (constraintNames[k].equals("durationForceRhythmToken")) {
                        int[] rhythms = constraintRhythmValues.get(k);
                        for (int i=0; i < rhythms.length; i++){
                            x[constraintTokenValues[k] + i].assign(rhythms[i]);
                        }
                    }

                }
            }

            // let the CP-BP solver compute the marginals
            cp.fixPoint();
            cp.beliefPropa();

            // output the computed marginals (probability mass function to sample from) for the next token
            for (int i = 0; i < nbVal; i++) {
                minicpbp_marginals[i] = (x[nextTokenIdx].contains(i) ? x[nextTokenIdx].marginal(i) : 0);
            }

            return minicpbp_marginals;
        }

        catch (InconsistencyException e) {
            System.err.println("Error 2: " + "Inconsistency Exception at iteration " + nextTokenIdx);
			System.err.println("StackTrace : ");
			e.printStackTrace();
            //System.exit(2) ;
            double[] minicpbp_marginals = new double[]{1.0, 0.0, 0.0};
            return minicpbp_marginals;
        }

        catch (Exception  e) {
            System.err.println("Error 3: " + e.getMessage());
			System.err.println("StackTrace : ");
			e.printStackTrace();
            System.exit(3) ;
            double[] minicpbp_marginals = new double[]{1.0, 0.0, 0.0};
            return minicpbp_marginals;
        }
    }

    public static int[][] initAutomaton(int nbBar){

		// in order to express constraints about note durations, build next-duration automaton
		int[][] nextDurationAutomaton = new int[nbVarPerBar * nbBar][nbVal]; // state nb corresponds to duration;

		// initial state
		nextDurationAutomaton[0][onsetToken] = 1; // start a note
		nextDurationAutomaton[0][restToken] = 0;
		nextDurationAutomaton[0][holdToken] = -1; // cannot start with hold token

		for (int i = 1; i < nextDurationAutomaton.length - 1; i++) {
			nextDurationAutomaton[i][onsetToken] = 1; // start a note
			nextDurationAutomaton[i][restToken] = 0;
			nextDurationAutomaton[i][holdToken] = i + 1; // continue the note
		}

		// max-duration state
		nextDurationAutomaton[nextDurationAutomaton.length - 1][onsetToken] = 1; // start a note
		nextDurationAutomaton[nextDurationAutomaton.length - 1][restToken] = 0;
		nextDurationAutomaton[nextDurationAutomaton.length - 1][holdToken] = -1; // cannot continue the note

		return nextDurationAutomaton;
	}

    public static void redirectStdout() {
        try {
            PrintStream fileOut = new PrintStream("minicpbp/examples/data/MusicCP/results.txt");
            System.setOut(fileOut);
        }
        catch(FileNotFoundException e) {
            System.err.println("Error 1: " + e.getMessage()) ;
            System.exit(1) ;
        }
    }
}


