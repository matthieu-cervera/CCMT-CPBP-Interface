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
 *
 * mini-cpbp, replacing classic propagation by belief propagation
 * Copyright (c)  2019. by Gilles Pesant
 */

package minicpbp.engine.constraints;

import minicpbp.engine.core.AbstractConstraint;
import minicpbp.engine.core.BoolVar;
import minicpbp.engine.core.IntVar;
import minicpbp.state.StateInt;
import minicpbp.util.ArrayUtil;
import minicpbp.util.exception.NotImplementedException;

/**
 * Reified logical or constraint
 */
public class IsOr extends AbstractConstraint { // b <=> x1 or x2 or ... xn

    private final BoolVar b;
    private final BoolVar[] x;
    private final int n;

    private int[] unBounds;
    private StateInt nUnBounds;

    private final Or or;

    /**
     * Creates a constraint such that
     * the boolean b is true if and only if
     * at least one variable in x is true.
     *
     * @param b the boolean that is true if at least one variable in x is true
     * @param x a non empty array of variables
     */
    public IsOr(BoolVar b, BoolVar[] x) {
        super(b.getSolver(), ArrayUtil.append(b,x));
        setName("IsOr");
        this.b = b;
        this.x = x;
        this.n = x.length;
        or = new Or(x);

        nUnBounds = getSolver().getStateManager().makeStateInt(n);
        unBounds = new int[n];
        for (int i = 0; i < n; i++) {
            unBounds[i] = i;
        }
	    setExactWCounting(true);

    }

    @Override
    public void post() {
	    propagate();
	    switch (getSolver().getMode()) {
	    case BP:
	        break;
	    case SP:
	    case SBP:
	        if (isActive()) {
		        b.propagateOnBind(this);
		        for (BoolVar xi : x) {
		            xi.propagateOnBind(this);
		        }
	        }
	    }
    }

    @Override
    public void propagate() {
        if (b.isTrue()) {
            setActive(false);
            getSolver().post(or, false);
        } else if (b.isFalse()) {
            for (BoolVar xi : x) {
                xi.assign(false);
            }
            setActive(false);
        } else {
            int nU = nUnBounds.value();
            for (int i = nU - 1; i >= 0; i--) {
                int idx = unBounds[i];
                BoolVar y = x[idx];
                if (y.isBound()) {
                    if (y.isTrue()) {
                        b.assign(true);
                        setActive(false);
                        return;
                    }
                    // Swap the variable
                    unBounds[i] = unBounds[nU - 1];
                    unBounds[nU - 1] = idx;
                    nU--;
                }
            }
            if (nU == 0) {
                b.assign(false);
                setActive(false);
            }
            nUnBounds.setValue(nU);
        }
    }

    @Override
    public void updateBelief() {
	    double beliefAllFalse = beliefRep.one();
	    for (int i = nUnBounds.value() - 1; i >= 0; i--) {
	        beliefAllFalse = beliefRep.multiply(beliefAllFalse, outsideBelief(1+unBounds[i],0));
	    }
        // Treatment of x
	    for (int i = nUnBounds.value() - 1; i >= 0; i--) {
	        int idx = unBounds[i];
	        if (!x[idx].isBound()) { // in case of BP mode
		        assert(!beliefRep.isZero(outsideBelief(1+idx,0)));
		        // will be normalized
                setLocalBelief(1+idx, 1, outsideBelief(0,1));
                setLocalBelief(1+idx, 0, beliefRep.add( beliefRep.multiply( beliefRep.complement( beliefRep.divide(beliefAllFalse,outsideBelief(1+idx,0)) ), outsideBelief(0,1) ), outsideBelief(0,0) ) );
	        }
	    }
        // Treatment of b
	    setLocalBelief(0, 1, beliefRep.complement(beliefAllFalse));
	    setLocalBelief(0, 0, beliefAllFalse);
    }

}
