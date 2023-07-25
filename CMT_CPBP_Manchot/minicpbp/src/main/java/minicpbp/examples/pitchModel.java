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
import java.util.List;
import java.util.Locale;
import java.util.Scanner;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;


import static minicpbp.cp.Factory.*;

public class pitchModel {

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
        try{
            //###################################################
            //################ First call of java ###############
            //###################################################
            
            //retrieve useful static args
            String sequencePrefixFile = args[0];
            int nbSample = Integer.parseInt(args[1]);
            int nextTokenIdx = Integer.parseInt(args[2]);
            String filenameTokenRhythm = args[3];
            double minOracleWeight = Double.parseDouble(args[4]);
            int K = Integer.parseInt(args[5]);
            String userConstraints = args[6];
            int beam_index = 0;
            int beamWidth = Integer.parseInt(args[7]);

            // Create the solvers List 
            List<Solver> solverList = new ArrayList<>();
            List<postConstraintsResult> resultList = new ArrayList<>();

            for (int i = 0; i < beamWidth; i++) {
                Solver cp = Factory.makeSolver();
                solverList.add(cp);
            }

            // Post CONSTRAINTS
            for (int i = 0; i < beamWidth; i++) {
                postConstraintsResult result = postConstraints(filenameTokenRhythm, nextTokenIdx, sequencePrefixFile, solverList.get(i), userConstraints, minOracleWeight, K);
                resultList.add(result);
            }

            // Check if java is needed
            boolean javaNeeded = false;
            String[] arguments = null;


            //###################################################
            //########### Loop to generate all tokens ###########
            //###################################################
            while(!javaNeeded && nextTokenIdx<128){
               
                BufferedReader brActivation = new BufferedReader(new FileReader("minicpbp/examples/data/MusicCP/JavaNeeded.txt"));
                String line = brActivation.readLine();
                javaNeeded = Boolean.parseBoolean(line);
                brActivation.close();


                if (javaNeeded){
                    // set arguments
                    BufferedReader brArguments = new BufferedReader(new FileReader("minicpbp/examples/data/MusicCP/JavaArgs.txt"));
                    String argsline = brArguments.readLine();
                    arguments = argsline.split(",");
                    nextTokenIdx = Integer.parseInt(arguments[0]);
                    sequencePrefixFile = arguments[1];
                    beam_index = Integer.parseInt(arguments[2]);
                    
                    
                    // solve the cp problem for the pointed token (and pointed beam if there is beam search)
                    solveCP(filenameTokenRhythm, nextTokenIdx, sequencePrefixFile, solverList.get(beam_index), userConstraints, minOracleWeight, K, resultList.get(beam_index).x_onsets, resultList.get(beam_index).indices);

                    // set javaNeeded to false and put false in the javaNeeded file
                    javaNeeded = false;
                    FileWriter fileWriter = new FileWriter("minicpbp/examples/data/MusicCP/JavaNeeded.txt", false);
                    fileWriter.write("False");
                    fileWriter.close();
                }
            }
        }
        catch (IOException e) {
        System.err.println("Error 0: " + e.getMessage()) ;
        e.printStackTrace();}
        catch (Exception e){
            System.err.println("Error 1: " + e.getMessage()) ;
            System.err.println("StackTrace : ");
            e.printStackTrace();
        }
    }

    public static postConstraintsResult postConstraints (String filenameTokenRhythm, int nextTokenIdx, String sequencePrefixFile, Solver cp, String userConstraints, double minOracleWeight, int K){
        try {
            // create rhythmCMT and pitchCMT to avoid using scanner class
            Scanner scannerRhythmToList = new Scanner(new FileReader("minicpbp/examples/data/MusicCP/" + filenameTokenRhythm)).useLocale(Locale.US);
            Scanner scannerPitchToList = new Scanner(new FileReader("minicpbp/examples/data/MusicCP/" + sequencePrefixFile)).useLocale(Locale.US);

            int[] rhythmCMT = createTokenList(scannerRhythmToList, 128);
            int[] pitchCMT = createTokenList(scannerPitchToList, nextTokenIdx);

            Scanner scannerPitch = new Scanner(new FileReader("minicpbp/examples/data/MusicCP/" + sequencePrefixFile)).useLocale(Locale.US);
            Scanner scannerRhythm = new Scanner(new FileReader("minicpbp/examples/data/MusicCP/" + filenameTokenRhythm)).useLocale(Locale.US);
            redirectStdoutLogs(sequencePrefixFile);

            int pitchOccInRange = Math.floorDiv(nbVal - 2, nbPitchClass);
            int[][] pitchIdx = new int[nbPitchClass][pitchOccInRange];
            for (int i = 0; i < nbPitchClass; i++) {
                for (int j = 0; j < pitchOccInRange; j++) {
                    pitchIdx[i][j] = (j * nbPitchClass) + i;
                }
            }

            //###################################################
            //############## Initialize x_onsets ################
            //###################################################

            // Create a subset of x with only onset pitches
            int[] onsetCountsTotal = countOnsetTokens(nextTokenIdx, 0, 128, rhythmCMT);


            IntVar[] x_onsets = new IntVar[onsetCountsTotal[0]];
            for (int i = 0; i < onsetCountsTotal[0]; i++) {
                x_onsets[i] = makeIntVar(cp, 0, nbVal - 2);
                x_onsets[i].setName("x_onsets" + "[" + i + "]");
            }

            // initialize x_onsets with CMT values
            // Array onset_indices stores, for each index of the sequence, its index in the "onsets only" sequence
            int[] onset_indices = new int[nbVar];
            int onset_index = 0;
            for (int i = 0; i < nextTokenIdx; i++) {
                onset_indices[i] = onset_index;
                if (rhythmCMT[i] == rhythmOnsetToken){
                    // set value of previously fixed pitch vars
                    x_onsets[onset_index].assign(pitchCMT[i]);
                    onset_index ++;
                }
            }

            for (int i = nextTokenIdx; i<nbVar; i++){
                onset_indices[i] = onset_index;
                if (rhythmCMT[i] == rhythmOnsetToken){
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
                        int token = Integer.parseInt(split_constraint[3]);
                        constraintTokenValues[i] = token;
                        int[] pitches = new int[split_constraint.length - 4];
                    
                        for (int j = 4; j < split_constraint.length; j++) {
                            pitches[j - 4] = Integer.parseInt(split_constraint[j]);
                        }

                        constraintPitchValues.add(pitches); 
                    }
                    else {
                        // Single pitch
                        int token = Integer.parseInt(split_constraint[3]);
                        constraintTokenValues[i] = token;
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
                int[] onsetCounts = countOnsetTokens(nextTokenIdx, beginIdx, constraintBars[k][1]*nbVarPerBar, rhythmCMT);
               
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
        System.out.println();       // print logs
        scannerPitch.close();
        scannerRhythm.close();

        return new postConstraintsResult(x_onsets, onset_indices);
        }
        catch (IOException e) {
            System.err.println("Error 1: " + e.getMessage()) ;
            System.err.println("StackTrace : ");
            e.printStackTrace();
            System.exit(1) ;
            return null;
        }
        catch (InconsistencyException e) {
            System.err.println("Error 2: " + "Inconsistency Exception");
			System.err.println("StackTrace : ");
			e.printStackTrace();
            System.exit(2) ;
            return null;


        }
        catch (Exception  e) {
            System.err.println("Error 3: " + e.getMessage());
			System.err.println("StackTrace : ");
			e.printStackTrace();
            System.exit(3) ;
            return null;

}
    }

    public static void solveCP(String filenameTokenRhythm, int nextTokenIdx, String sequencePrefixFile, Solver cp, String userConstraints, double minOracleWeight, int K, IntVar[] x_onsets, int[] onset_indices){
    try {
            // create rhythmCMT and pitchCMT to avoid using scanner class
            Scanner scannerRhythmToList = new Scanner(new FileReader("minicpbp/examples/data/MusicCP/" + filenameTokenRhythm));
            Scanner scannerPitchToList = new Scanner(new FileReader("minicpbp/examples/data/MusicCP/" + sequencePrefixFile));
            redirectStdoutLogs(sequencePrefixFile);

            int[] rhythmCMT = createTokenList(scannerRhythmToList, 128);
            int[] pitchCMT = createTokenList(scannerPitchToList, nextTokenIdx);

            Scanner scannerPitch = new Scanner(new FileReader("minicpbp/examples/data/MusicCP/" + sequencePrefixFile)).useLocale(Locale.US);


            if(rhythmCMT[nextTokenIdx]==rhythmHoldToken){
                redirectStdout(sequencePrefixFile);
				// output the marginals for hold token
				for (int i = 0; i < nbVal; i++) {
			        if (i==pitchHoldToken){
			            System.out.print(1 + " ");
			        }
			        else{
					System.out.print(0 + " ");
			        }
				}
				System.out.println();
			}
			else if(rhythmCMT[nextTokenIdx]==rhythmRestToken){
                redirectStdout(sequencePrefixFile);
				// output the marginals for rest token
				for (int i = 0; i < nbVal; i++) {
			        if (i==pitchRestToken){
			            System.out.print(1 + " ");
			        }
			        else{
					System.out.print(0 + " ");
			        }
				}
				System.out.println();
			}
			else{
                int onset_index = 0;
			    for (int i = 0; i < nextTokenIdx; i++) {
                        if (rhythmCMT[i] == rhythmOnsetToken){
                            // set value of previously fixed pitch vars
                            x_onsets[onset_index].assign(pitchCMT[i]);
                            onset_index ++;
                        }
                    }
                // set initial scores (marginals) for variable being fixed (next token in the sequence) according to NN
                double[] scores = new double[nbVal];
                int[] vals = new int[nbVal];
                for (int i = 0; i < nbVal; i++) {
                    scores[i] = scannerPitch.nextDouble();
                    vals[i] = i;
                }
                scannerPitch.close();

                // set oracle constraint
                Constraint orac_new = Factory.oracle(x_onsets[onset_indices[nextTokenIdx]], vals, scores);
                double oracleWeight = 1.0;
                orac_new.setWeight(oracleWeight);
                cp.post(orac_new);


				// let the CP-BP solver compute the marginals
				cp.fixPoint();
				cp.beliefPropa();

                System.out.println();


                redirectStdout(sequencePrefixFile);

				// output the computed marginals (probability mass function to sample from) for the next token
				for (int i = 0; i < nbVal; i++) {
					System.out.print((x_onsets[onset_indices[nextTokenIdx]].contains(i) ? x_onsets[onset_indices[nextTokenIdx]].marginal(i) : 0) + " ");
				}

				System.out.println();

			}

        }
        catch (IOException e) {
            System.err.println("Error 1: " + e.getMessage()) ;
            System.err.println("StackTrace : ");
            e.printStackTrace();
            System.exit(1) ;
        }
        catch (InconsistencyException e) {
            System.err.println("Error 2: " + "Inconsistency Exception");
			System.err.println("StackTrace : ");
			e.printStackTrace();
            System.exit(2) ;
        }
        catch (Exception  e) {
            System.err.println("Error 3: " + e.getMessage());
			System.err.println("StackTrace : ");
			e.printStackTrace();
            System.exit(3) ;}
        }

    // write the results to a file with the same name but appended with "_results"
    public static void redirectStdout(String sequencePrefixFile) {
        try {
            PrintStream fileOut = new PrintStream("minicpbp/examples/data/MusicCP/" + sequencePrefixFile.substring(0, sequencePrefixFile.length() - 4) + "_results.dat");
            System.setOut(fileOut);
        }
        catch(FileNotFoundException e) {
            System.err.println("Error 1: " + e.getMessage()) ;
            System.exit(1) ;
        }
    }

    // write the logs to a file with the same name but appended with "_logs" to see logs directly in google Colab
	public static void redirectStdoutLogs(String sequencePrefixFile) {
		try {
			PrintStream fileOut = new PrintStream("minicpbp/examples/data/MusicCP/" + sequencePrefixFile.substring(0, sequencePrefixFile.length() - 4) + "_logs.dat");
			System.setOut(fileOut);
		}
		catch(FileNotFoundException e) {
			System.err.println("Error 1: " + e.getMessage()) ;
			System.exit(1) ;
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

	public static int[] createTokenList(Scanner scanner, int nbToken) {
	    int[] tokenList = new int[nbToken];
		for (int i=0; i < nbToken; i++){
		    int token = scanner.nextInt();
		    tokenList[i] = token;
		}
		return tokenList;
	}

	public static class postConstraintsResult {
        public final IntVar[] x_onsets;
        public final int[] indices;
        public postConstraintsResult(IntVar[] x_onsets, int[] indices) {
            this.x_onsets = x_onsets;
            this.indices = indices;
        }
    }
}
