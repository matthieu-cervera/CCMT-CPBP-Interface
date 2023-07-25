package xcsp;

import java.io.File;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import launch.SolveXCSPFZN.BranchingHeuristic;
import launch.SolveXCSPFZN.TreeSearchType;

public class SolveXCSP {

	private static Map<String, BranchingHeuristic> branchingMap = new HashMap<String, BranchingHeuristic>() {
		private static final long serialVersionUID = 4936849715939593675L;
		{
			put("first-fail-random-value", BranchingHeuristic.FFRV);
			put("max-marginal-strength", BranchingHeuristic.MXMS);
			put("min-marginal-strength", BranchingHeuristic.MNMS);
			put("max-marginal", BranchingHeuristic.MXM);
			put("min-marginal", BranchingHeuristic.MNM);
		}
	};
	

	private static Map<String, TreeSearchType> searchTypeMap = new HashMap<String, TreeSearchType>() {
		private static final long serialVersionUID = 8428231233538651558L;

		{
			put("dfs", TreeSearchType.DFS);
			put("lds", TreeSearchType.LDS);
		}
	};

	public static void main(String[] args) {

		String quotedValidBranchings = branchingMap.keySet().stream().sorted().map(x -> "\"" + x + "\"")
				.collect(Collectors.joining(",\n"));

		String quotedValidSearchTypes = searchTypeMap.keySet().stream().sorted().map(x -> "\"" + x + "\"")
				.collect(Collectors.joining(",\n"));
		

		Option xcspFileOpt = Option.builder().longOpt("input").argName("FILE").required().hasArg()
				.desc("input FZN file").build();

		Option branchingOpt = Option.builder().longOpt("branching").argName("STRATEGY").required().hasArg()
				.desc("branching strategy.\nValid branching strategies are:\n" + quotedValidBranchings).build();

		Option searchOpt = Option.builder().longOpt("search-type").argName("SEARCH").required().hasArg()
				.desc("search type.\nValid search types are:\n" + quotedValidSearchTypes).build();

		Option timeoutOpt = Option.builder().longOpt("timeout").argName("SECONDS").required().hasArg()
				.desc("timeout in seconds").build();

		Option statsFileOpt = Option.builder().longOpt("stats").argName("FILE").hasArg()
				.desc("file for storing the statistics").build();

		Option solFileOpt = Option.builder().longOpt("solution").argName("FILE").hasArg()
				.desc("file for storing the solution").build();

		Option maxIterOpt = Option.builder().longOpt("max-iter").argName("ITERATIONS").hasArg()
				.desc("maximum number of belief propagation iterations").build();

		Option dFactorOpt = Option.builder().longOpt("damping-factor").argName("LAMBDA").hasArg()
				.desc("the damping factor used for damping the messages").build();

		Option checkOpt = Option.builder().longOpt("verify").hasArg(false)
				.desc("check the correctness of obtained solution").build();

		Option dampOpt = Option.builder().longOpt("damp-messages").hasArg(false).desc("damp messages").build();

		Option traceBPOpt = Option.builder().longOpt("trace-bp").hasArg(false)
				.desc("trace the belief propagation progress").build();

		Option traceSearchOpt = Option.builder().longOpt("trace-search").hasArg(false).desc("trace the search progress")
				.build();


		Options options = new Options();
		options.addOption(xcspFileOpt);
		options.addOption(branchingOpt);
		options.addOption(searchOpt);
		options.addOption(timeoutOpt);
		options.addOption(statsFileOpt);
		options.addOption(solFileOpt);
		options.addOption(maxIterOpt);
		options.addOption(checkOpt);
		options.addOption(traceBPOpt);
		options.addOption(traceSearchOpt);
		options.addOption(dampOpt);
		options.addOption(dFactorOpt);

		CommandLineParser parser = new DefaultParser();
		CommandLine cmd = null;
		try {
			cmd = parser.parse(options, args);
		} catch (ParseException exp) {
			System.err.println(exp.getMessage());
			new HelpFormatter().printHelp("solve-XCSP", options);
			System.exit(1);
		}

		String branchingStr = cmd.getOptionValue("branching");
		checkBranchingOption(branchingStr);
		BranchingHeuristic heuristic = branchingMap.get(branchingStr);

		String searchTypeStr = cmd.getOptionValue("search-type");
		checkSearchTypeOption(searchTypeStr);
		TreeSearchType searchType = searchTypeMap.get(searchTypeStr);


		String inputStr = cmd.getOptionValue("input");
		checkInputOption(inputStr);

		String timeoutStr = cmd.getOptionValue("timeout");
		int timeout = checkTimeoutOption(timeoutStr);

		String statsFileStr = "";
		if (cmd.hasOption("stats")) {
			statsFileStr = cmd.getOptionValue("stats");
			checkCreateFile(statsFileStr);
		}

		String solFileStr = "";
		if (cmd.hasOption("solution")) {
			solFileStr = cmd.getOptionValue("solution");
			checkCreateFile(solFileStr);
		}

		int maxIter = 5;
		if (cmd.hasOption("max-iter"))
			maxIter = Integer.parseInt(cmd.getOptionValue("max-iter"));

		double dampingFactor = 0.5;
		if (cmd.hasOption("damping-factor"))
			dampingFactor = Double.parseDouble(cmd.getOptionValue("damping-factor"));


		boolean checkSolution = (cmd.hasOption("verify"));
		boolean traceBP = (cmd.hasOption("trace-bp"));
		boolean traceSearch = (cmd.hasOption("trace-search"));
		boolean damp = (cmd.hasOption("damp-messages"));

		try {
			XCSP xcsp = new XCSP(inputStr);
			xcsp.searchType(searchType);
			xcsp.checkSolution(checkSolution);
			xcsp.traceBP(traceBP);
			xcsp.traceSearch(traceSearch);
			xcsp.maxIter(maxIter);
			xcsp.damp(damp);
			xcsp.dampingFactor(dampingFactor);

			xcsp.solve(heuristic, timeout, statsFileStr, solFileStr);
		} catch (Exception e) {
			e.printStackTrace();
		}

	}

	private static void checkBranchingOption(String branchingStr) {

		if (!branchingMap.containsKey(branchingStr)) {
			System.out.println("invalid branching strategy " + branchingStr);
			System.out.println("Branching strategy should be one of the following: ");
			for (String branching : branchingMap.keySet())
				System.out.println(branching);
			System.exit(1);
		}
	}

	private static void checkSearchTypeOption(String searchTypeStr) {

		if (!searchTypeMap.containsKey(searchTypeStr)) {
			System.out.println("invalid search type " + searchTypeStr);
			System.out.println("Search type should be one of the following: ");
			for (String branching : searchTypeMap.keySet())
				System.out.println(branching);
			System.exit(1);
		}
	}

	private static void checkInputOption(String inputStr) {
		File inputFile = new File(inputStr);
		if (!inputFile.exists()) {
			System.out.println("input file " + inputStr + " does not exist!");
			System.exit(1);
		}
	}

	private static int checkTimeoutOption(String timeoutStr) {
		Integer timeout = null;
		try {
			timeout = Integer.valueOf(timeoutStr);
		} catch (NumberFormatException e) {
			e.printStackTrace();
			System.out.println("invalid timeout string " + timeoutStr);
			System.exit(1);
		}

		if (timeout < 0 || timeout > Integer.MAX_VALUE) {
			System.out.println("invalid timeout " + timeout);
			System.exit(1);
		}

		return timeout.intValue();
	}

	private static void checkCreateFile(String filename) {
		File f = new File(filename);
		if (f.exists())
			f.delete();
		try {
			if (!f.createNewFile()) {
				System.out.println("can not create file " + filename);
				System.exit(1);
			}
		} catch (Exception e) {
			e.printStackTrace();
			System.out.println("can not create file " + filename);
			System.exit(1);
		}
	}

}
