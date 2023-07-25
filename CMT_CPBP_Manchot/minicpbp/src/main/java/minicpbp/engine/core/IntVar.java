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

package minicpbp.engine.core;

import minicpbp.util.Procedure;
import minicpbp.util.exception.InconsistencyException;

import java.util.Set;

public interface IntVar {

    /**
     * Returns the solver in which this variable was created.
     *
     * @return the solver in which this variable was created
     */
    Solver getSolver();

    /**
     * Asks that the closure is called whenever the domain
     * of this variable is reduced to a single setValue
     *
     * @param f the closure
     */
    void whenBind(Procedure f);

    /**
     * Asks that the closure is called whenever
     * the max or min setValue of the domain of this variable changes
     *
     * @param f the closure
     */
    void whenBoundsChange(Procedure f);

    /**
     * Asks that the closure is called whenever the domain change
     * of this variable changes
     *
     * @param f the closure
     */
    void whenDomainChange(Procedure f);

    /**
     * Asks that {@link Constraint#propagate()} is called whenever the domain
     * of this variable changes.
     * We say that a <i>change</i> event occurs.
     *
     * @param c the constraint for which the {@link Constraint#propagate()}
     *          method should be called on change events of this variable.
     */
    void propagateOnDomainChange(Constraint c);

    /**
     * Asks that {@link Constraint#propagate()} is called whenever the domain
     * of this variable is reduced to a singleton.
     * In such a state the variable is bind and we say that a <i>bind</i> event occurs.
     *
     * @param c the constraint for which the {@link Constraint#propagate()}
     *          method should be called on bind events of this variable.
     */
    void propagateOnBind(Constraint c);

    /**
     * Asks that {@link Constraint#propagate()} is called whenever the
     * bound (maximum or minimum values) of the domain
     * of this variable is changes.
     * We say that a <i>bound change</i> event occurs in this case.
     *
     * @param c the constraint for which the {@link Constraint#propagate()}
     *          method should be called on bound change events of this variable.
     */
    void propagateOnBoundChange(Constraint c);


    /**
     * Returns the minimum of the domain of the variable
     *
     * @return the minimum of the domain of the variable
     */
    int min();

    /**
     * Returns the maximum of the domain of the variable
     *
     * @return the maximum of the domain of the variable
     */
    int max();

    /**
     * Returns the size of the domain of the variable
     *
     * @return the size of the domain of the variable
     */
    int size();

    /**
     * Copies the values of the domain into an array.
     *
     * @param dest an array large enough {@code dest.length >= size()}
     * @return the size of the domain and {@code dest[0,...,size-1]} contains
     *         the values in the domain in an arbitrary order
     */
    int fillArray(int[] dest);

    /**
     * Returns true if the domain of the variable has a single value.
     *
     * @return true if the domain of the variable is a singleton.
     */
    boolean isBound();

    /**
     * Returns true if the domain contains the specified value.
     * @param v the value whose presence in the domain is to be tested
     * @return true if the domain contains the specified value
     */
    boolean contains(int v);

    /**
     * Removes the specified value.
     * @param v the value to remove
     * @exception InconsistencyException
     *            is thrown if the domain becomes empty
     */
    void remove(int v);

    /**
     * Assigns the specified value
     *
     * @param v the value to assign.
     * @exception InconsistencyException
     *            is thrown if the value is not in the domain
     */
    void assign(int v);

    /**
     * Remove all the values less than a given value
     *
     * @param v the value such that all the values less than v are removed
     * @exception InconsistencyException
     *            is thrown if the domain becomes empty
     */
    void removeBelow(int v);

    /**
     * Remove all the values above a given value
     *
     * @param v the value such that all the values larger than v are removed
     * @exception InconsistencyException
     *            is thrown if the domain becomes empty
     */
    void removeAbove(int v);

    /**
     * Remove all the values outside of S
     *
     * @param S the set of allowed values
     * @exception InconsistencyException
     *            is thrown if the domain becomes empty
     */
    void removeOutside(Set<Integer> S);

    /**
     * Returns a value in the domain chosen uniformly at random.
     *
     * @return random value in the domain
     */
    int randomValue();

    /**
     * Returns a value in the domain chosen randomly according to the marginal distribution.
     * Based on the stochastic acceptance algorithm described in http://arxiv.org/abs/1109.3627
     *
     * @return random value in the domain according to marginal distribution
     */
    int biasedWheelValue();

    /**
     * Returns the marginal of the specified value.
     *
     * @param v the value whose marginal is to be returned
     * @exception InconsistencyException
     *            is thrown if the value is not in the domain
     * @return the marginal
     */
    double marginal(int v);

    /**
     * Sets the marginal of the specified value.
     *
     * @param v the value whose marginal is to be set to m
     * @exception InconsistencyException
     *            is thrown if the value is not in the domain
     */
    void setMarginal(int v, double m);

    /**
     * Sets the marginals to 1.
     *
     */
    void resetMarginals();

    /**
     * Normalizes the marginals.
     *
     */
    void normalizeMarginals();

    /**
     * Returns the largest marginal for a value in the domain.
     *
     * @return the largest marginal
     */
    double maxMarginal();

    /**
     * Returns the value in the domain that has the largest marginal.
     *
     * @return the value with the largest marginal
     */
    int valueWithMaxMarginal();

    /**
     * Returns the smallest marginal for a value in the domain.
     *
     * @return the smallest marginal
     */
    double minMarginal();

    /**
     * Returns the value in the domain that has the smallest marginal.
     *
     * @return the value with the smallest marginal
     */
    int valueWithMinMarginal();

    /**
     * Returns the largest marginal regret for the domain.
     *
     * @return the largest marginal regret
     */
    double maxMarginalRegret();

    /**
     * Returns the entropy of the marginal distribution
     *
     * @return the entropy
     */
    double entropy();

    /**
     * Returns the expected impact of variable
     * @return the impact
     */
    public double impact();
    
    /**
     * Returns the value of the domain with the smaller impact
     * @return the value
     */
    public int valueWithMinImpact();

    /**
     * Returns the value of the domain with the maximal impact
     * @return the value
     */
    public int valueWithMaxImpact();

    /**
     * Register an observed impact of assigning a value
     * @param value the value
     * @param impact the impact
     */
    public void registerImpact(int value, double impact);

    /**
     * Returns the marginal of the specified value after cancelling 
     * out the local belief of a constraint.
     *
     * @param v the value, b the local belief
     * @return the corrected marginal
     * @exception InconsistencyException
     *            is thrown if the value is not in the domain
     */
    double sendMessage(int v, double b);

    /**
     * Accumulates in the marginal of the specified value 
     * the local belief of a constraint.
     *
     * @param v the value, b the local belief
     * @exception InconsistencyException
     *            is thrown if the value is not in the domain
     */
    void receiveMessage(int v, double b);

    /**
     * @param b is True if the variable is a variable that can be branched on
     * is False if the variable is an auxiliary variable
     */
    public void setForBranching(boolean b);

    /**
     * 
     * @return True if the variable is a branch variable, False if not
     */
    public boolean isForBranching();

    public int wDeg();

    public String getName();
    public void setName(String name);
    public void registerConstraint(Constraint c);
}
