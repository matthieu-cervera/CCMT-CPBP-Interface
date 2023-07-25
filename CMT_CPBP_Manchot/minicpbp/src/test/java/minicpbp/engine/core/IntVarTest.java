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

package minicpbp.engine.core;

import minicpbp.engine.SolverTest;
import minicpbp.util.NotImplementedExceptionAssume;
import minicpbp.util.exception.InconsistencyException;
import minicpbp.util.exception.NotImplementedException;
import org.junit.Test;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

import static minicpbp.cp.Factory.*;
import static org.junit.Assert.*;


public class IntVarTest extends SolverTest {

    public boolean propagateCalled = false;

    @Test
    public void testIntVar() {
        Solver cp = solverFactory.get();

        IntVar x = makeIntVar(cp, 10);
        IntVar y = makeIntVar(cp, 10);

        cp.getStateManager().saveState();


        try {

            assertFalse(x.isBound());
            x.remove(5);
            assertEquals(9, x.size());
            x.assign(7);
            assertEquals(1, x.size());
            assertTrue(x.isBound());
            assertEquals(7, x.min());
            assertEquals(7, x.max());

        } catch (InconsistencyException e) {
            fail("should not fail here");
        }

        try {
            x.assign(8);
            fail("should have failed");
        } catch (InconsistencyException expectedException) {
        }


        cp.getStateManager().restoreState();
        cp.getStateManager().saveState();

        assertFalse(x.isBound());
        assertEquals(10, x.size());

        for (int i = 0; i < 10; i++) {
            assertTrue(x.contains(i));
        }
        assertFalse(x.contains(-1));

    }

    @Test
    public void onDomainChangeOnBind() {
        propagateCalled = false;
        Solver cp = solverFactory.get();

        IntVar x = makeIntVar(cp, 10);
        IntVar y = makeIntVar(cp, 10);

        Constraint cons = new AbstractConstraint(cp, new IntVar[]{x,y}) {
            @Override
            public void post() {
                x.whenBind(() -> propagateCalled = true);
                y.whenDomainChange(() -> propagateCalled = true);
            }
        };

        try {
            cp.post(cons,true);
            x.remove(8);
            cp.fixPoint();
            assertFalse(propagateCalled);
            x.assign(4);
            cp.fixPoint();
            assertTrue(propagateCalled);
            propagateCalled = false;
            y.remove(10);
            cp.fixPoint();
            assertFalse(propagateCalled);
            y.remove(9);
            cp.fixPoint();
            assertTrue(propagateCalled);

        } catch (InconsistencyException inconsistency) {
            fail("should not fail");
        }
    }

    @Test
    public void arbitraryRangeDomains() {

        try {

            Solver cp = solverFactory.get();

            IntVar x = makeIntVar(cp, -10, 10);

            cp.getStateManager().saveState();


            try {

                assertFalse(x.isBound());
                x.remove(-9);
                x.remove(-10);


                assertEquals(19, x.size());
                x.assign(-4);
                assertEquals(1, x.size());
                assertTrue(x.isBound());
                assertEquals(-4, x.min());

            } catch (InconsistencyException e) {
                fail("should not fail here");
            }

            try {
                x.assign(8);
                fail("should have failed");
            } catch (InconsistencyException expectedException) {
            }


            cp.getStateManager().restoreState();

            assertEquals(21, x.size());

            for (int i = -10; i < 10; i++) {
                assertTrue(x.contains(i));
            }
            assertFalse(x.contains(-11));


        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


    @Test
    public void arbitrarySetDomains() {

        try {

            Solver cp = solverFactory.get();

            Set<Integer> dom = new HashSet<>(Arrays.asList(-7, -10, 6, 9, 10, 12));

            IntVar x = makeIntVar(cp, dom);

            cp.getStateManager().saveState();

            try {

                for (int i = -15; i < 15; i++) {
                    if (dom.contains(i))
                        assertTrue(x.contains(i));
                    else assertFalse(x.contains(i));
                }

                x.assign(-7);
            } catch (InconsistencyException e) {
                fail("should not fail here");
            }

            try {
                x.assign(-10);
                fail("should have failed");
            } catch (InconsistencyException expectedException) {
            }


            cp.getStateManager().restoreState();

            for (int i = -15; i < 15; i++) {
                if (dom.contains(i)) assertTrue(x.contains(i));
                else assertFalse(x.contains(i));
            }
            assertEquals(6, x.size());


        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


    @Test
    public void onBoundChange() {

        Solver cp = solverFactory.get();

        IntVar x = makeIntVar(cp, 10);
        IntVar y = makeIntVar(cp, 10);
        System.out.println("here");
        Constraint cons = new AbstractConstraint(cp, new IntVar[]{x,y}) {

            @Override
            public void post() {
                System.out.println("here4");
                x.whenBind(() -> propagateCalled = true);
                System.out.println("here4.5");
                y.whenDomainChange(() -> propagateCalled = true);

                System.out.println("here5");
            }
        };
        System.out.println("here2");

        try {
            cp.post(cons,true);
            System.out.println("here3");
            x.remove(8);
            cp.fixPoint();
            assertFalse(propagateCalled);
            x.remove(9);
            cp.fixPoint();
            assertFalse(propagateCalled);
            x.assign(4);
            cp.fixPoint();
            assertTrue(propagateCalled);
            propagateCalled = false;
            assertFalse(y.contains(10));
            y.remove(10);
            cp.fixPoint();
            assertFalse(propagateCalled);
            propagateCalled = false;
            y.remove(2);
            cp.fixPoint();
            assertTrue(propagateCalled);

        } catch (InconsistencyException inconsistency) {
            fail("should not fail");
        }
    }


    @Test
    public void removeAbove() {

        try {

            Solver cp = solverFactory.get();

            IntVar x = makeIntVar(cp, 10);

            Constraint cons = new AbstractConstraint(cp, new IntVar[]{x}) {
                @Override
                public void post() {
                    x.propagateOnBoundChange(this);
                }

                @Override
                public void propagate() {
                    propagateCalled = true;
                }
            };

            try {
                cp.post(cons,true);
                x.remove(8);
                cp.fixPoint();
                assertFalse(propagateCalled);
                x.removeAbove(8);
                assertEquals(7, x.max());
                cp.fixPoint();
                assertTrue(propagateCalled);

            } catch (InconsistencyException inconsistency) {
                fail("should not fail");
            }

        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }

    @Test
    public void removeBelow() {

        try {

            Solver cp = solverFactory.get();
            IntVar x = makeIntVar(cp, 10);

            Constraint cons = new AbstractConstraint(cp, new IntVar[]{x}) {
                @Override
                public void post() {
                    x.propagateOnBoundChange(this);
                }

                @Override
                public void propagate() {
                    propagateCalled = true;
                }
            };

            try {
                cp.post(cons,true);
                x.remove(3);
                cp.fixPoint();
                assertFalse(propagateCalled);
                x.removeBelow(3);
                assertEquals(4, x.min());
                cp.fixPoint();
                assertTrue(propagateCalled);
                propagateCalled = false;

                x.removeBelow(5);
                assertEquals(5, x.min());
                cp.fixPoint();
                assertTrue(propagateCalled);
                propagateCalled = false;


            } catch (InconsistencyException inconsistency) {
                fail("should not fail");
            }

        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


    @Test
    public void fillArray() {
        try {
            Solver cp = solverFactory.get();

            IntVar x = makeIntVar(cp, 2, 9);
            x.remove(3);
            x.remove(5);
            x.remove(2);
            x.remove(9);

            int[] values = new int[10];
            int s = x.fillArray(values);
            HashSet<Integer> dom = new HashSet<Integer>();
            for (int i = 0; i < s; i++) {
                dom.add(values[i]);
            }
            HashSet<Integer> expectedDom = new HashSet<Integer>();
            Collections.addAll(expectedDom, 4, 6, 7, 8);
            assertEquals(expectedDom, dom);

        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }

    @Test
    public void arbitrarySetDomainsMaxInt() {

        try {

            Solver cp = solverFactory.get();
            Set<Integer> dom = new HashSet<>(Arrays.asList(2147483645));
            IntVar var1 = makeIntVar(cp, dom);
            assertEquals(2147483645, var1.max());

        } catch (NotImplementedException e) {
            NotImplementedExceptionAssume.fail(e);
        }
    }


}
