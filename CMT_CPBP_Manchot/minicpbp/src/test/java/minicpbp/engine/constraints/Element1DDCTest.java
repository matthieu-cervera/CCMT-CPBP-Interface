/*
 * mini-cp is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License  v3
 * as published by the Free Software Foundation.
 *
 * mini-cp is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY.
 * See the GNU Lesser General Public License  for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with mini-cp. If not, see http://www.gnu.org/licenses/lgpl-3.0.en.html
 *
 * Copyright (c)  2018. by Laurent Michel, Pierre Schaus, Pascal Van Hentenryck
 */

package minicpbp.engine.constraints;

import minicpbp.engine.SolverTest;
import minicpbp.util.NotImplementedExceptionAssume;
import minicpbp.util.exception.NotImplementedException;
import org.junit.Test;
import minicpbp.engine.core.IntVar;
import minicpbp.engine.core.Solver;
import minicpbp.search.DFSearch;
import minicpbp.search.SearchStatistics;
import minicpbp.util.Procedure;

import java.util.HashSet;
import java.util.Random;
import java.util.function.Supplier;

import static minicpbp.cp.BranchingScheme.EMPTY;
import static minicpbp.cp.BranchingScheme.branch;
import static minicpbp.cp.Factory.*;
import static minicpbp.cp.Factory.notEqual;
import static org.junit.Assert.*;

public class Element1DDCTest extends SolverTest {

    @Test
    public void element1dTest1() {
        try {
            Solver cp = solverFactory.get();

            Random rand = new Random(678);
            IntVar y = makeIntVar(cp, 0, 100);
            IntVar z = makeIntVar(cp, 0, 100);


            int[] T = new int[70];
            HashSet<Integer> uniqueValues = new HashSet<>(T.length);
            for (int i = 0; i < T.length; i++) {
                T[i] = rand.nextInt(100);
                uniqueValues.add(T[i]);
            }

            cp.post(new Element1DDomainConsistent(T, y, z),true);

            assertEquals(y.size(), T.length);
            assertEquals(z.size(), uniqueValues.size());

            assertTrue(y.max() < T.length);

            Supplier<Procedure[]> branching = () -> {
                if (y.isBound() && z.isBound()) {
                    assertEquals(T[y.min()], z.min());
                    return EMPTY;
                }
                int[] possibleY = new int[y.size()];
                y.fillArray(possibleY);

                int[] possibleZ = new int[z.size()];
                z.fillArray(possibleZ);

                HashSet<Integer> possibleValues = new HashSet<>();
                HashSet<Integer> possibleValues2 = new HashSet<>();
                for (int i = 0; i < possibleZ.length; i++)
                    possibleValues.add(possibleZ[i]);

                for (int i = 0; i < possibleY.length; i++) {
                    assertTrue(possibleValues.contains(T[possibleY[i]]));
                    possibleValues2.add(T[possibleY[i]]);
                }
                assertEquals(possibleValues.size(), possibleValues2.size());

                if (!y.isBound() && (z.isBound() || rand.nextBoolean())) {
                    //select a random y
                    int val = possibleY[rand.nextInt(possibleY.length)];
                    return branch(() -> branchEqual(y, val),
                            () -> branchNotEqual(y, val));
                } else {
                    int val = possibleZ[rand.nextInt(possibleZ.length)];
                    return branch(() -> branchEqual(z, val),
                            () -> branchNotEqual(z, val));
                }
            };

            DFSearch dfs = makeDfs(cp, branching);

            SearchStatistics stats = dfs.solve();
            assertTrue(stats.numberOfSolutions() >= uniqueValues.size());
            assertTrue(stats.numberOfSolutions() <= T.length);
        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }
}
