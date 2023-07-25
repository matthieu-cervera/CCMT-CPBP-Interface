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
import java.util.Locale;
import java.util.Scanner;

import java.io.BufferedReader;
import java.io.FileWriter;


import static minicpbp.cp.Factory.*;

import jep.NDArray;
import jep.Jep;
import jep.JepException;
import jep.SharedInterpreter;
import jep.python.PyObject;


public class samplingPitch {

    // Variables to pick from arguments
    public static final int nbVar = 128;
    public static final int nbVarPerBar = 16;
    public static final int nbBar = 8;
    public static final int nbVal = 50;

    public static final int[] CMajorPitchClass = {0, 4, 7};//do mi sol

    public static final int nbPitchClass = 12;
    public static final int rhythmOnsetToken = 2;
    public static final int rhythmHoldToken = 1;
    public static final int rhythmRestToken = 0;
    public static final int pitchHoldToken = 48;
    public static final int pitchRestToken = 49;

    public static void main(String[] args) {

        //retrieve useful static args
        int seed = Integer.parseInt(args[1]);
        String userConstraints = args[0];
        int K = Integer.parseInt(args[2]);
        try (Jep jepInterpreter = new SharedInterpreter()){

            // import libraries and set working directory
            jepInterpreter.eval("import os");
            jepInterpreter.eval("os.chdir(\"/usagers4/p118640/User_Interface_Project-main/CMT_CPBP_Manchot/\")");
            jepInterpreter.eval("import sys");
            jepInterpreter.eval("sys.path.append(\"/usagers4/p118640/User_Interface_Project-main/CMT_CPBP_Manchot/\")");
            jepInterpreter.eval("import jeptest");

            jepInterpreter.set("seed", seed);

            // initialize python variables
            jepInterpreter.eval("model, pitch_result, rhythm_result, rhythm_emb, chord_hidden = jeptest.initialize_model_pitch(seed)");
            Object model = jepInterpreter.getValue("model");
            Object pitch_result = jepInterpreter.getValue("pitch_result");
            Object rhythm_emb = jepInterpreter.getValue("rhythm_emb");
            Object chord_hidden = jepInterpreter.getValue("chord_hidden");

            float[] rhythm_result_float = new float[nbVar];
            float[] pitch_result_float = new float[nbVar];
            for (int j=0; j<nbVar; j++){
                jepInterpreter.set("index", j);
                jepInterpreter.eval("pitch_value = jeptest.tensor_values_by_index(pitch_result, index)");
                jepInterpreter.eval("rhythm_value = jeptest.tensor_values_by_index(rhythm_result, index)");
                Double pitch_value_double = (Double) jepInterpreter.getValue("pitch_value");
                float pitch_value = pitch_value_double.floatValue();
                Double rhythm_value_double = (Double) jepInterpreter.getValue("rhythm_value");
                float rhythm_value = rhythm_value_double.floatValue();
                rhythm_result_float[j] = rhythm_value;
                pitch_result_float[j] = pitch_value;
            }

           int[] rhythm_result = new int[rhythm_result_float.length];
            for (int i=0; i<rhythm_result_float.length; i++){
                rhythm_result[i] = (int) Math.floor(rhythm_result_float[i]);
            }



            // Create the solver
            Solver cp = Factory.makeSolver();
            double oracleWeight = 1.0;
            postConstraints_X x_arrays = postConstraints(0, nbVar, nbBar, rhythm_result, pitch_result_float, cp, userConstraints, oracleWeight, K);

            // Sampling phase
            for (int nextTokenIdx = 0; nextTokenIdx<nbVar; nextTokenIdx ++){

                // Get marginals from CMT layers - forward
                jepInterpreter.set("model", model);
                jepInterpreter.set("pitch_result", pitch_result);
                jepInterpreter.set("chord_hidden", chord_hidden);
                jepInterpreter.set("rhythm_emb", rhythm_emb);
                jepInterpreter.set("iteration", nextTokenIdx);
                jepInterpreter.eval("marginals = jeptest.pitchForward_CMT(model, iteration, pitch_result, rhythm_emb, chord_hidden)");
                NDArray marginals_ndarray = (NDArray) jepInterpreter.getValue("marginals");
                Object pitch_out = jepInterpreter.getValue("marginals");
                float[] marginals = (float[]) marginals_ndarray.getData();


                // Adding constraints to marginals
                // post constraints and solve the cp problem for the pointed token
                double[] minicpbp_probs = solveCSP(nextTokenIdx, cp, x_arrays.x_onsets, x_arrays.x, x_arrays.indices,  marginals, rhythm_result, pitch_result_float, oracleWeight);


                // CMT token generation
                //jepInterpreter.set("probs", marginals);
                jepInterpreter.set("probs_cp", minicpbp_probs);
                jepInterpreter.eval("pitch_result = jeptest.sample_pitch_token(iteration, probs_cp, pitch_result)");
                pitch_result = jepInterpreter.getValue("pitch_result");

                for (int j=0; j<nbVar; j++){
                    jepInterpreter.set("index", j);
                    jepInterpreter.eval("pitch_value = jeptest.tensor_values_by_index(pitch_result, index)");
                    Double pitch_value_double = (Double) jepInterpreter.getValue("pitch_value");
                    float pitch_value = pitch_value_double.floatValue();
                    pitch_result_float[j] = pitch_value;
                }
            }

            // Get final result
            // Write results for python code
            FileWriter fileWriter = new FileWriter("minicpbp/src/main/java/minicpbp/examples/data/MusicCP/results_pitch.txt", false);
            for (int i = 0; i < nbVar; i++) {
                jepInterpreter.set("index", i);
                jepInterpreter.eval("pitch_result_value = jeptest.tensor_values_by_index(pitch_result, index)");
                Double pitch_value_double = (Double) jepInterpreter.getValue("pitch_result_value");
                fileWriter.write(pitch_value_double+" ");
            }
            fileWriter.close();
            jepInterpreter.close();

            }

    catch (JepException e) {
       System.err.println("Error -1: " + e.getMessage()) ;
       e.printStackTrace();}
    catch (Exception e) {
        System.err.println("Error 0: " + e.getMessage()) ;
        e.printStackTrace();}
    }


    // process constraints string, post constraints and solve the CP
    public static postConstraints_X postConstraints(int nextTokenIdx, int nbVar, int nbBar, int[] rhythm_result, float[] pitch_result, Solver cp, String userConstraints, double oracleWeight, int K){
        try {
            int pitchOccInRange = Math.floorDiv(nbVal - 2, nbPitchClass);
            int[][] pitchIdx = new int[nbPitchClass][pitchOccInRange];
            for (int i = 0; i < nbPitchClass; i++) {
                for (int j = 0; j < pitchOccInRange; j++) {
                    pitchIdx[i][j] = (j * nbPitchClass) + i;
                }
            }

            IntVar[] x = new IntVar[nbVar];
            for (int i = 0; i < nbVar; i++) {
                x[i] = makeIntVar(cp, 0, nbVal - 1);
                x[i].setName("x" + "[" + i + "]");
            }

            // set value of previously fixed vars
            for (int i = 0; i < nextTokenIdx; i++) {
                x[i].assign((int) Math.floor(pitch_result[i]));
            }

            // read current rhythm token
            int token = rhythm_result[nextTokenIdx];
            if (token == rhythmOnsetToken) {
                x[nextTokenIdx].remove(pitchHoldToken);
                x[nextTokenIdx].remove(pitchRestToken);
            }
            else {
                x[nextTokenIdx].assign(token == rhythmHoldToken ? pitchHoldToken : pitchRestToken);
            }

             // Create a subset of x with only onset pitches
             // Need to convert rhythm result to int array
            int[] onsetCountsTotal = countOnsetTokens(nextTokenIdx, 0, 128, rhythm_result);


            IntVar[] x_onsets = new IntVar[onsetCountsTotal[0]];
            for (int i = 0; i < onsetCountsTotal[0]; i++) {
                x_onsets[i] = makeIntVar(cp, 0, nbVal - 3);
                x_onsets[i].setName("x_onsets" + "[" + i + "]");
            }

            // initialize x_onsets with CMT values
            // Array onset_indices stores, for each index of the sequence, its index in the "onsets only" sequence
            int[] onset_indices = new int[nbVar];
            int onset_index = 0;
            for (int i = 0; i < nextTokenIdx; i++) {
                onset_indices[i] = onset_index;
                if (rhythm_result[i] == rhythmOnsetToken){
                    // set value of previously fixed pitch vars
                    x_onsets[onset_index].assign((int) Math.floor(pitch_result[i]));
                    onset_index ++;
                }
            }

            for (int i = nextTokenIdx; i<nbVar; i++){
                onset_indices[i] = onset_index;
                if (rhythm_result[i] == rhythmOnsetToken){
                    onset_index ++;
                }
            }

            //###################################################
            //############## READ USER CONSTRAINTS  #############
            //###################################################
            String[] userConstraintsList = userConstraints.split(";");
            String[] constraintNames = new String[userConstraintsList.length];
            int[][] constraintBars = new int[userConstraintsList.length][2];
            int[][] constraintSepBars = new int[userConstraintsList.length][2];
            int[] constraintTokenValues = new int[userConstraintsList.length];
            ArrayList<int[]> constraintPitchValues = new ArrayList<>();
            for (int i = 0; i < userConstraintsList.length; i++) {
                String[] split_constraint = userConstraintsList[i].split(":");
                constraintNames[i]=split_constraint[0];
                int[] bar = {Integer.parseInt(split_constraint[1]),Integer.parseInt(split_constraint[2])};

                if (split_constraint[0].contains("Sep")){       // This is a constraint with separate measures
                    int[] sepBar = {Integer.parseInt(split_constraint[3]),Integer.parseInt(split_constraint[4])};
                    constraintSepBars[i] = sepBar;
                    int[] foo_pitch = {};   
                    constraintPitchValues.add(foo_pitch);
                }
                else if (split_constraint[0].contains("Token")){     // This isn't a constraint on measures, but on a token  
                    if (split_constraint.length > 5){
                        // Multiple pitches
                        int pointed_token = Integer.parseInt(split_constraint[3]);
                        constraintTokenValues[i] = pointed_token;
                        int[] pitches = new int[split_constraint.length - 4];
                    
                        for (int j = 4; j < split_constraint.length; j++) {
                            pitches[j - 4] = Integer.parseInt(split_constraint[j]);
                        }

                        constraintPitchValues.add(pitches); 
                    }
                    else {
                        // Single pitch
                        int pointed_token = Integer.parseInt(split_constraint[3]);
                        constraintTokenValues[i] = pointed_token;
                        int[] pitch = {Integer.parseInt(split_constraint[4])};   
                        constraintPitchValues.add(pitch);
                    }
                }
                else if (split_constraint[0].contains("Force")){     // Constraint to force a musical scale
                    int[] pitches = new int[split_constraint.length - 3];
                    
                    for (int j = 3; j < split_constraint.length; j++) {
                        pitches[j - 3] = Integer.parseInt(split_constraint[j]);
                    }

                    constraintPitchValues.add(pitches); 
                }
                else {  // Classic constraint
                    int[] foo_pitch = {};   
                    constraintPitchValues.add(foo_pitch);
                }  
                
                constraintBars[i] = bar;
            }

            //###################################################
            //############ APPLY USER CONSTRAINTS ###############
            //###################################################
            for (int k=0; k < constraintNames.length; k++){

                // Useful variables
                int groupSize = 1 + constraintBars[k][1] - constraintBars[k][0];
                int beginIdx = (constraintBars[k][0]-1) * nbVarPerBar;
                int[] onsetCounts = countOnsetTokens(nextTokenIdx, beginIdx, constraintBars[k][1]*nbVarPerBar, rhythm_result);
               
                IntVar[] x_onsets_subset = Arrays.copyOfRange(x_onsets, onset_indices[beginIdx], onset_indices[constraintBars[k][1] * nbVarPerBar - 1]);

                if (constraintNames[k].equals("pitchOnsetKey")) {

                    IntVar[] o = new IntVar[nbPitchClass];
                    for (int i = 0; i < nbPitchClass; i++) {
                        boolean inKey = false;
                        for (int l = 0; l < CMajorPitchClass.length; l++) {
                            if (CMajorPitchClass[l] == i) {
                                inKey = true;
                                break;
                            };
                        }
                        if (inKey) {
                            o[i] = makeIntVar(cp, K, onsetCounts[0]);
                        }
                        else {
                            o[i] = makeIntVar(cp, 0, onsetCounts[0]);
                        }
                        o[i].setName("o"+"["+i+"]");
                    }

                    for (int i = 0; i < nbPitchClass; i++) {
                        cp.post(Factory.among(x_onsets_subset, pitchIdx[i], o[i]));
                    }

                   IntVar s = makeIntVar(cp, onsetCounts[0], onsetCounts[0]);
                   cp.post(Factory.lessOrEqual(Factory.sum(o), s));
                }

                if (constraintNames[k].equals("pitchAllSame")) {
                    for (int i=1; i< x_onsets_subset.length; i++){
                        cp.post(Factory.equal(x_onsets_subset[i], x_onsets[i-1]));
                    }
                }

                if (constraintNames[k].equals("pitchAllSameFixed")) {

                    // find the note fixed by the user
                    int allSameNoteChoice = Integer.parseInt(constraintNames[k].split("ed")[1]);
                    IntVar[] o = new IntVar[nbPitchClass];
                    for (int i = 0; i < nbPitchClass; i++) {
                        if (i == allSameNoteChoice){
                        o[i] = makeIntVar(cp, onsetCounts[0], onsetCounts[0]);
                        }
                        else{
                        o[i] = makeIntVar(cp, 0, 0);
                        }
                        o[i].setName("o"+"["+i+"]");
                    }

                    for (int i = 0; i < nbPitchClass; i++) {
                        cp.post(Factory.among(x_onsets_subset, pitchIdx[i], o[i]));
                    }

                    IntVar s = makeIntVar(cp, onsetCounts[0], onsetCounts[0]);
                    cp.post(Factory.lessOrEqual(Factory.sum(o), s));
                }

                if (constraintNames[k].equals("pitchAllDiff")) {
                    IntVar[] o = new IntVar[nbPitchClass];
                    for (int i = 0 ; i < nbPitchClass ; i++) {
                        o[i] = makeIntVar(cp, 0, 1);
                        o[i].setName("o" + "[" + i + "]");
                        cp.post(Factory.among(x_onsets_subset, pitchIdx[i], o[i]));
                    }
                }

                if (constraintNames[k].equals("pitchIncrease")) {
                    for (int i=1; i< x_onsets_subset.length; i++){
                        cp.post(Factory.less(x_onsets_subset[i-1], x_onsets_subset[i]));
                    }
                }

                if (constraintNames[k].equals("pitchDecrease")) {
                    for (int i=1; i< x_onsets_subset.length; i++){
                        cp.post(Factory.less(x_onsets_subset[i], x_onsets_subset[i-1]));
                    }
                }

                if (constraintNames[k].equals("Sep-pitchSame")) {
                    IntVar[] x_onsets_subsetsep = Arrays.copyOfRange(x_onsets, onset_indices[beginIdx], onset_indices[constraintSepBars[k][1] * nbVarPerBar]);
                    for (int i = 0 ; i <  onsetCounts[0]; i++) {
                        cp.post(Factory.equal(x_onsets_subsetsep[i], x_onsets_subsetsep[onset_indices[(constraintSepBars[k][0] - constraintBars[k][0]) * nbVarPerBar] + i]));
                    }
                }

                if (constraintNames[k].equals("pitchTokenSingle")) {
                    int[] pitches = constraintPitchValues.get(k);
                    x_onsets[onset_indices[constraintTokenValues[k]]].assign(pitches[0]);    // we know that pitches has only one value in this case
                }

                if (constraintNames[k].equals("pitchTokenMultiple")) {
                    int[] pitches = constraintPitchValues.get(k);
                    for (int i = 0; i < nbPitchClass; i++) {
                        boolean inKey = false;
                        for (int l = 0; l < pitches.length; l++) {
                            if (pitches[l] == i) {
                                inKey = true;
                                break;
                            };
                        }
                        if (!inKey) {       // remove the not inKey values
                            for (int j = 0; j < pitchOccInRange; j++) {
                                x_onsets[onset_indices[constraintTokenValues[k]]].remove(pitchIdx[i][j]);
                            }    
                        }
                    }
                }
                
                if (constraintNames[k].equals("pitchForceMultiple")) {
                    int[] pitches = constraintPitchValues.get(k);
                    for (int i = 0; i < nbPitchClass; i++) {
                        boolean inKey = false;
                        for (int l = 0; l < pitches.length; l++) {
                            if (pitches[l] == i) {
                                inKey = true;
                                break;
                            };
                        }
                        if (!inKey) {       // remove the not inKey values
                            for (int j = 0; j < pitchOccInRange; j++) {
                                for (int m=0; m< x_onsets_subset.length; m++){
                                    x_onsets_subset[m].remove(pitchIdx[i][j]);
                                }
                                
                            }    
                        }
                    }
                }
            }

            return new postConstraints_X(x_onsets, x, onset_indices);
        }

        catch (InconsistencyException e) {
            System.err.println("Error 2: " + "Inconsistency Exception at iteration " + nextTokenIdx);
			System.err.println("StackTrace : ");
			e.printStackTrace();
            return new postConstraints_X(null, null, null);

        }

        catch (Exception  e) {
            System.err.println("Error 3: " + e.getMessage());
			System.err.println("StackTrace : ");
			e.printStackTrace();
            System.exit(3) ;
            return new postConstraints_X(null, null, null);
        }
    }

    public static double[] solveCSP(int nextTokenIdx, Solver cp, IntVar[] x_onsets, IntVar[] x, int[] onset_indices, float[] CMTMarginals, int[] rhythm_result, float[] pitch_result, double oracleWeight){
        try {
            double[] minicpbp_marginals = new double[nbVal];

            if(rhythm_result[nextTokenIdx]==rhythmHoldToken){
                // output the marginals for hold token
                for (int i = 0; i < nbVal; i++) {
                    if (i==pitchHoldToken){
                         minicpbp_marginals[i] = 1.0 ;
                    }
                    else{
                     minicpbp_marginals[i] = 0.0;
                    }
                }
            }

            else if(rhythm_result[nextTokenIdx]==rhythmRestToken){
                // output the marginals for rest token
                for (int i = 0; i < nbVal; i++) {
                    if (i==pitchRestToken){
                         minicpbp_marginals[i] = 1.0 ;
                    }
                    else{
                     minicpbp_marginals[i] = 0.0;
                    }
                }
            }
            else{
                int onset_index = 0;
                for (int i = 0; i < nextTokenIdx; i++) {
                        if (rhythm_result[i] == rhythmOnsetToken){
                            // set value of previously fixed pitch vars
                            x_onsets[onset_index].assign((int) Math.floor(pitch_result[i]));
                            onset_index ++;
                        }
                    }


                // set initial scores (marginals) for variable being fixed (next token in the sequence) according to NN
                double[] scores = new double[nbVal];
                int[] vals = new int[nbVal];
                for (int i = 0; i < nbVal; i++) {
                    scores[i] = (double) CMTMarginals[i];
                    vals[i] = i;
                }

                Constraint orac = Factory.oracle(x_onsets[onset_indices[nextTokenIdx]], vals, scores);
                orac.setWeight(oracleWeight);
                cp.post(orac);

                // let the CP-BP solver compute the marginals
                cp.fixPoint();
                cp.beliefPropa();

                for (int i = 0; i < nbVal; i++) {
                    minicpbp_marginals[i] = (x_onsets[onset_indices[nextTokenIdx]].contains(i) ? x_onsets[onset_indices[nextTokenIdx]].marginal(i) : 0);
                }
            }

            return minicpbp_marginals;
        }
    catch (InconsistencyException e) {
            System.err.println("Error 2: " + "Inconsistency Exception at iteration " + nextTokenIdx);
			System.err.println("StackTrace : ");
			e.printStackTrace();
            double[] minicpbp_marginals = new double[nbVal];
            Arrays.fill(minicpbp_marginals, 0.0);
            minicpbp_marginals[nbVal -1 ] = 1.0;
            return minicpbp_marginals;
        }

        catch (Exception  e) {
            System.err.println("Error 3: " + e.getMessage());
			System.err.println("StackTrace : ");
			e.printStackTrace();
            System.exit(3) ;
            double[] minicpbp_marginals = new double[nbVal];
            Arrays.fill(minicpbp_marginals, 0.0);
            minicpbp_marginals[nbVal -1 ] = 1.0;
            return minicpbp_marginals;
        }
    }

    public static int[] countOnsetTokens(int currentIdx, int beginIdx, int endIdx, int[] sRhythm) {
        int onsetCount = 0;
        int onsetUntilIdxCount = 0;

        for (int i=beginIdx; i<endIdx; i++){
            if (sRhythm[i] == rhythmOnsetToken){
                onsetCount ++;
                if (i<currentIdx){
                    onsetUntilIdxCount ++;
                }
            }
        }
        return new int[]{onsetCount, onsetUntilIdxCount};
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

    public static class postConstraints_X {
        public final IntVar[] x_onsets;
        public final IntVar[] x;
        public final int[] indices;
        public postConstraints_X(IntVar[] x_onsets, IntVar[] x, int[] indices) {
            this.x_onsets = x_onsets;
            this.x = x;
            this.indices = indices;
        }
    }
}


