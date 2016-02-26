#!/usr/bin/env python3

import automata.automaton as automaton
import automata.dfa


class NFA(automaton.Automaton):
    """a nondeterministic finite automaton"""

    def __init__(self, obj=None, *, states=None, symbols=None,
                 transitions=None, initial_state=None, final_states=None):
        """initializes a complete NFA"""
        if isinstance(obj, automata.dfa.DFA):
            self._init_from_dfa(obj)
        elif isinstance(obj, NFA):
            self._init_from_nfa(obj)
        else:
            self.states = set(states)
            self.symbols = set(symbols)
            self.transitions = self.__class__._clone_transitions(transitions)
            self.initial_state = initial_state
            self.final_states = set(final_states)
            self.validate_automaton()

    def _init_from_nfa(self, nfa):
        """initializes this NFA as an exact clone of the given NFA"""
        self.__init__(
            states=nfa.states, symbols=nfa.symbols,
            transitions=nfa.transitions, initial_state=nfa.initial_state,
            final_states=nfa.final_states)

    def _init_from_dfa(self, dfa):
        """initializes this NFA as one equivalent to the given DFA"""

        nfa_transitions = {}
        for start_state, paths in dfa.transitions.items():
            nfa_transitions[start_state] = {}
            for symbol, end_state in paths.items():
                nfa_transitions[start_state][symbol] = {end_state}

        self.__init__(
            states=dfa.states, symbols=dfa.symbols,
            transitions=nfa_transitions, initial_state=dfa.initial_state,
            final_states=dfa.final_states)

    @staticmethod
    def _clone_transitions(transitions):
        """clones the given transitions dictionary"""

        cloned_transitions = {}
        for start_state, paths in transitions.items():

            cloned_transitions[start_state] = {}
            for symbol, end_states in paths.items():
                cloned_transitions[start_state][symbol] = set(
                    transitions[start_state][symbol])

        return cloned_transitions

    def _validate_transition_symbols(self, start_state, paths):
        """raises an error if the transition symbols are missing or invalid"""

        path_symbols = set(paths.keys())
        invalid_symbols = path_symbols - self.symbols.union({''})
        if invalid_symbols:
            raise automaton.InvalidSymbolError(
                'state {} has invalid transition symbols ({})'.format(
                    start_state, ', '.join(invalid_symbols)))

    def validate_automaton(self):
        """returns True if this NFA is internally consistent;
        raises the appropriate exception otherwise"""

        self._validate_transition_start_states()

        for start_state, paths in self.transitions.items():

            self._validate_transition_symbols(start_state, paths)

            path_states = set().union(*paths.values())
            self._validate_transition_end_states(path_states)

        self._validate_initial_state()
        self._validate_final_states()

        return True

    def _add_lambda_transition_states(self, states):
        """finds all end states for lambda transitions connected to the given
        set of states"""

        new_states = set()
        for state in states:

            if '' in self.transitions[state]:
                new_states.update(self.transitions[state][''])
                # Keep adding states as long as we keep finding contiguous
                # lambda transitions
                new_states.update(self._add_lambda_transition_states(
                    self.transitions[state]['']))

        return new_states

    def _get_next_current_states(self, current_states, symbol=None):
        """returns the next set of current states given the current set"""

        next_current_states = set()
        for current_state in current_states:

            symbol_end_states = self.transitions[current_state].get(symbol)
            if symbol_end_states:
                next_current_states.update(symbol_end_states)
                next_current_states.update(self._add_lambda_transition_states(
                    symbol_end_states))

        return next_current_states

    def validate_input(self, input_str):
        """returns True if the given string is accepted by this NFA;
        raises the appropriate exception otherwise"""

        current_states = {self.initial_state}

        for symbol in input_str:

            self._validate_input_symbol(symbol)
            current_states = self._get_next_current_states(
                current_states, symbol)

        if not (current_states & self.final_states):
            raise automaton.FinalStateError(
                'the automaton stopped at all non-final states ({})'.format(
                    current_states))

        return current_states
