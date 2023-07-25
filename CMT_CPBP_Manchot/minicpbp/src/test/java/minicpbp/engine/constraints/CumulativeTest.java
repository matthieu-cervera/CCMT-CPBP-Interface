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
import minicpbp.engine.constraints.Profile.Rectangle;
import minicpbp.engine.core.IntVar;
import minicpbp.engine.core.Solver;
import minicpbp.search.DFSearch;
import minicpbp.search.SearchStatistics;
import minicpbp.util.exception.InconsistencyException;
import minicpbp.util.exception.NotImplementedException;
import minicpbp.util.NotImplementedExceptionAssume;
import org.junit.Test;

import java.util.Arrays;
import java.util.stream.IntStream;

import static minicpbp.cp.BranchingScheme.firstFail;
import static minicpbp.cp.Factory.*;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

public class CumulativeTest extends SolverTest {


    @Test
    public void testAllDiffWithCumulative() {

        try {

            Solver cp = solverFactory.get();

            IntVar[] s = makeIntVarArray(cp, 5, 5);
            int[] d = new int[5];
            Arrays.fill(d, 1);
            int[] r = new int[5];
            Arrays.fill(r, 100);

            cp.post(new Cumulative(s, d, r, 100),true);

            SearchStatistics stats = makeDfs(cp, firstFail(s)).solve();
            assertEquals("cumulative alldiff expect makeIntVarArray permutations", 120, stats.numberOfSolutions());

        } catch (InconsistencyException e) {
            assert (false);
        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }

    }

    @Test
    public void testBasic1() {

        try {

            Solver cp = solverFactory.get();

            IntVar[] s = makeIntVarArray(cp, 2, 10);
            int[] d = new int[]{5, 5};
            int[] r = new int[]{1, 1};

            cp.post(new Cumulative(s, d, r, 1),true);
            s[0].assign(0);
            cp.fixPoint();

            assertEquals(5, s[1].min());

        } catch (InconsistencyException e) {
            assert (false);
        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


    @Test
    public void testBasic2() {

        try {

            Solver cp = solverFactory.get();

            IntVar[] s = makeIntVarArray(cp, 2, 10);
            int[] d = new int[]{5, 5};
            int[] r = new int[]{1, 1};

            cp.post(new Cumulative(s, d, r, 1),true);

            s[0].assign(5);
            cp.fixPoint();

            assertEquals(0, s[1].max());

        } catch (InconsistencyException e) {
            assert (false);
        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


    @Test
    public void testCapaOk() {

        try {

            Solver cp = solverFactory.get();

            IntVar[] s = makeIntVarArray(cp, 5, 10);
            int[] d = new int[]{5, 10, 3, 6, 1};
            int[] r = new int[]{3, 7, 1, 4, 8};

            cp.post(new Cumulative(s, d, r, 12),true);

            DFSearch search = makeDfs(cp, firstFail(s));

            SearchStatistics stats = search.solve();

            search.onSolution(() -> {
                Rectangle[] rects = IntStream.range(0, s.length).mapToObj(i -> {
                    int start = s[i].min();
                    int end = start + d[i];
                    int height = r[i];
                    return new Rectangle(start, end, height);
                }).toArray(Rectangle[]::new);
                int[] discreteProfile = discreteProfile(rects);
                for (int h : discreteProfile) {
                    assertTrue("capa exceeded in cumulative constraint", h <= 12);
                }
            });


        } catch (InconsistencyException e) {
            assert (false);
        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


    @Test
    public void testSameNumberOfSolutionsAsDecomp() {

        try {

            Solver cp = solverFactory.get();

            IntVar[] s = makeIntVarArray(cp, 5, 7);
            int[] d = new int[]{5, 10, 3, 6, 1};
            int[] r = new int[]{3, 7, 1, 4, 8};

            DFSearch search = makeDfs(cp, firstFail(s));

            cp.getStateManager().saveState();

            cp.post(new Cumulative(s, d, r, 12),true);
            SearchStatistics stats1 = search.solve();

            cp.getStateManager().restoreState();

            cp.post(new CumulativeDecomposition(s, d, r, 12),true);
            SearchStatistics stats2 = search.solve();


            assertEquals(stats1.numberOfSolutions(), stats2.numberOfSolutions());
            assertEquals(stats1.numberOfFailures(), stats2.numberOfFailures());


        } catch (InconsistencyException e) {
            assert (false);
        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


    private static int[] discreteProfile(Rectangle... rectangles) {
        int min = Arrays.stream(rectangles).filter(r -> r.height() > 0).map(r -> r.start()).min(Integer::compare).get();
        int max = Arrays.stream(rectangles).filter(r -> r.height() > 0).map(r -> r.end()).max(Integer::compare).get();
        int[] heights = new int[max - min];
        // discrete profileRectangles of rectangles
        for (Rectangle r : rectangles) {
            if (r.height() > 0) {
                for (int i = r.start(); i < r.end(); i++) {
                    heights[i - min] += r.height();
                }
            }
        }
        return heights;
    }


}
