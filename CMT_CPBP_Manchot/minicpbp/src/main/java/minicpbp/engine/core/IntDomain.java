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

/**
 * Interface for integer domain implementation.
 * A domain is encapsulated in an {@link IntVar} implementation.
 * A domain is like a set of integers.
 */
public interface IntDomain {

    /**
     * Returns the minimum value of the domain.
     *
     * @return the minimum value of the domain
     */
    int min();

    /**
     * Returns the maximum value of the domain.
     *
     * @return the maximum value of the domain
     */
    int max();

    /**
     * Returns the cardinality of the domain.
     *
     * @return the cardinality value of the domain
     */
    int size();

    /**
     * Checks if the specified value belongs to the domain.
     *
     * @param v the value to be tested
     * @return true if v belongs to the domain, false otherwise
     */
    boolean contains(int v);

    /**
     * Checks if the domain contains a single element.
     *
     * @return true if the domain contains a single element,
     *         false otherwise
     */
    boolean isBound();

    /**
     * Removes a value from the domain and notifies appropriately the listener.
     *
     * @param v the value to be removed
     * @param l the methods of the listener are notified as follows:
     *          <ul>
     *              <li> {@link DomainListener#change()} is called
     *              if v belongs to the domain</li>
     *              <li> {@link DomainListener#changeMax()} is called
     *              if v is equal to the maximum value</li>
     *              <li> {@link DomainListener#changeMin()} is called
     *              if v is equal to the minimum value</li>
     *              <li> {@link DomainListener#bind()} is called
     *              if v belongs to the domain and after its removal
     *                      the domain has a single value</li>
     *              <li> {@link DomainListener#empty()}  is called
     *              if v is the last value in the domain i.e.
     *              the domain is empty after this operation</li>
     *         </ul>
     */
    void remove(int v, DomainListener l);

    /**
     * Removes every value from the domain except the specified one.
     *
     * @param v the value to be kept
     * @param l the methods of the listener are notified as follows:
     *          <ul>
     *              <li> {@link DomainListener#change()} is called
     *              if some value is removed during the operation</li>
     *              <li> {@link DomainListener#changeMax()} is called
     *              if v is not equal to the maximum value</li>
     *              <li> {@link DomainListener#changeMin()} is called
     *              if v is not equal to the minimum value</li>
     *              <li> {@link DomainListener#bind()} is called
     *              if v belongs to the domain and after its removal
     *                      the domain has a single value</li>
     *              <li> {@link DomainListener#empty()}  is called
     *              if v is not in the domain i.e.
     *              the domain is empty after this operation</li>
     *         </ul>
     */
    void removeAllBut(int v, DomainListener l);

    /**
     * Removes every value less than the specified value from the domain.
     *
     * @param v the value such that all the values less than v are removed
     * @param l the methods of the listener are notified as follows:
     *          <ul>
     *              <li> {@link DomainListener#change()} is called
     *              if some value is removed during the operation</li>
     *              <li> {@link DomainListener#changeMax()} is called
     *              if v is is larger than the minimum value</li>
     *              <li> {@link DomainListener#bind()} is called
     *              if v is equal to the maximum value</li>
     *              <li> {@link DomainListener#empty()} is called
     *              if v is larger than the maximum value i.e.
     *              the domain is empty after this operation</li>
     *         </ul>
     */
    void removeBelow(int v, DomainListener l);

    /**
     * Removes every value larger than the specified value from the domain.
     *
     * @param v the value such that all the values larger than v are removed
     * @param l the methods of the listener are notified as follows:
     *          <ul>
     *              <li> {@link DomainListener#change()} is called
     *              if some value is removed during the operation</li>
     *              <li> {@link DomainListener#changeMax()} is called
     *              if v is is less than the maximum value</li>
     *              <li> {@link DomainListener#bind()} is called
     *              if v is equal to the minimum value</li>
     *              <li> {@link DomainListener#empty()} is called
     *              if v is less than the minimum value i.e.
     *              the domain is empty after this operation</li>
     *         </ul>
     */
    void removeAbove(int v, DomainListener l);

    /**
     * Returns a value in the domain chosen uniformly at random
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
     * Returns the marginal of an element from the domain.
     *
     * @param v is an element in the domain
     */
    double marginal(int v);

    /**
     * Sets the marginal of an element from the domain.
     *
     * @param v is an element in the domain, m is the marginal
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
     * Copies the values of the domain into an array.
     *
     * @param dest an array large enough {@code dest.length >= size()}
     * @return the size of the domain and {@code dest[0,...,size-1]} contains
     *         the values in the domain in an arbitrary order
     */
    int fillArray(int[] dest);

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
     * Return the impact associated with @param value
     * @return the impact
     */
    double impactOfValue(int value);

    /**
     * Return expected impact computed 
     * from registerd impact of all value in the domain
     * @return
     */
    double impact();

    /**
     * Returns the value of the domain with the smallest impact
     * @return the value
     */
    int valueWithMinImpact();

    /**
     * Returns the value of the domain with the strongest impact
     * @return the value
     */
    int valueWithMaxImpact();

    /**
     * Register a new observed impact
     * @param value the value associated with the impact
     * @param impact the observed impact
     */
    void registerImpact(int value, double impact);

    @Override
    String toString();
}
