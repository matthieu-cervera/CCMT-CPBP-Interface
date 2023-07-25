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
import minicpbp.util.exception.InconsistencyException;
import minicpbp.util.exception.IntOverFlowException;
import org.junit.Test;

import static minicpbp.cp.Factory.makeIntVar;
import static minicpbp.cp.Factory.mul;
import static org.junit.Assert.*;


public class IntVarViewMulTest extends SolverTest {

    public boolean propagateCalled = false;

    @Test
    public void testIntVar() {
        Solver cp = solverFactory.get();

        IntVar x = mul(mul(makeIntVar(cp, -3, 4), -3), -1); // domain is {-9,-6,-3,0,3,6,9,12}

        assertEquals(-9, x.min());
        assertEquals(12, x.max());
        assertEquals(8, x.size());

        cp.getStateManager().saveState();


        try {

            assertFalse(x.isBound());

            x.remove(-6);
            assertFalse(x.contains(-6));
            x.remove(2);
            assertTrue(x.contains(0));
            assertTrue(x.contains(3));
            assertEquals(7, x.size());
            x.removeAbove(7);
            assertEquals(6, x.max());
            x.removeBelow(-8);
            assertEquals(-3, x.min());
            x.assign(3);
            assertTrue(x.isBound());
            assertEquals(3, x.max());


        } catch (InconsistencyException e) {
            e.printStackTrace();
            fail("should not fail here");
        }

        try {
            x.assign(8);
            fail("should have failed");
        } catch (InconsistencyException expectedException) {
        }

        cp.getStateManager().restoreState();

        assertEquals(8, x.size());
        assertFalse(x.contains(-1));

    }


    @Test
    public void onDomainChangeOnBind() {
        propagateCalled = false;
        Solver cp = solverFactory.get();

        IntVar x = mul(makeIntVar(cp, 10), 1);
        IntVar y = mul(makeIntVar(cp, 10), 1);

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
    public void onBoundChange() {

        Solver cp = solverFactory.get();

        IntVar x = mul(makeIntVar(cp, 10), 1);
        IntVar y = mul(makeIntVar(cp, 10), 1);

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


    @Test(expected = IntOverFlowException.class)
    public void testOverFlow() {
        Solver cp = solverFactory.get();
        IntVar x = mul(makeIntVar(cp, 1000000, 1000000), 10000000);
        System.out.println(x);
    }


}
