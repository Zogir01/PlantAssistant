
import time
from collections import deque

class StateMachine:
    '''Simple implementation of FSM pattern for embedded systems.'''

    def __init__(self):
        self._init = True
        self._states = {}
        self._current_state = None
        self._previous_state = None
        self._state_to_change = None
        self._state_index = 0
        self._state_start_ms = 0
        self._events = deque((), 10)            # normal events
        self._forced_events = deque((), 10)     # high-priority events

    def add_state(self, action, name = "", initial = False) -> int:
        """ Adds a new state to the state machine and returns its unique ID. """
        self._state_index += 1
        self._states[self._state_index] = {
            "action" : action,
            "name" : name
        }

        if initial: 
            self._current_state = self._state_index

        return self._state_index
    
    def add_timed_transition(self, from_state, to_state, delay_ms):
        pass
    
    def change_state(self, state):
        """ Change the state to the specified one, raise `ValueError` when the state is not found. """
        if state not in self._states:
            raise ValueError(f"Cannot find state = {state} in state dictionary.")
        
        self._state_to_change = state
    
    def state_elapsed_time(self):
        """ Returns how much time in miliseconds has passed in the current state. """
        return time.ticks_diff(time.ticks_ms(), self._state_start_ms)
    
    def in_state(self, *states):
        """ Returns whether the state machine is currently in the specified state. """
        for state in states:
            if self.current_state == state:
                return True
        return False
    
    def state_name(self, state = None) -> str:
        """ Returns current state name if `state` is not None, else returns `state` name.
        Raises `ValueError` when the state is not found. """
        if state is None: 
            return self._states[self._current_state]["name"]

        if state in self._states:
            return self._states[state]["name"]
        
        raise ValueError(f"Cannot find state = {state} in state dictionary.")
    
    def post_event(self, event, force=False):
        """ Post an event to the appropriate queue. 
        - If called with `force` = False, add event to normal queue
        and pass it to the state function in the next `do` cycle of this state, except `entry` and `exit` cycle.
        - If called with `force` = True, add event to higher-priority queue
        and pass it in the next cycle without regard to `entry` or `exit` action.
        """
        self._forced_events.append(event) if force else self._events.append(event)

    def get_status(self):
        """ Returns list of tuples with state machine status:

        (state name, state elapsed time, number of events, list of current events, number of forced events, list of forced events)
        """
        return self.state_name(), self.state_elapsed_time(), len(self._events), list(self._events), len(self._forced_events), list(self._forced_events)
    
    def set_initial_state(self, state):
        """ Sets the state bo the first of state machine. 
        Raise `ValueError` when the state is not found or after call to this function after first update cycle. 
        """
        if state not in self._states:
            raise ValueError(f"Cannot find state = {state} in state dictionary.")
        
        if not self._init:
            raise ValueError(f"Cannot set state to initial after first update cycle.") 

        self._current_state = state


    def _run_entry_action(self, event):
        self._states[self._current_state]["action"](event, phase="entry")
        
    def _run_do_action(self, event):
        self._states[self._current_state]["action"](event, phase="do")

    def _run_exit_action(self, event):
        self._states[self._current_state]["action"](event, phase="exit")
    
    def update(self):
        """ Executes current state's actions, this method should be called periodically. """

        if self._current_state is None:
            # Situtation where no state was added with initial = True
            return

        # Execute initial state entry action.
        if self._init:
            self._state_start_ms = time.ticks_ms()
            self._init = False
            self._run_entry_action(None)
            return # Run "do" action in next cycle.
        
        # Handle forced events first
        forced_event = self._forced_events.popleft() if self._forced_events else None
        
        # If there is state transition, run exit action of state and entry action of changed state.
        if self._state_to_change is not None:
            #self._state_start_ms = time.ticks_ms()

            self._run_exit_action(forced_event)
            forced_event = None
            
            self._previous_state = self._current_state
            self._current_state = self._state_to_change
            self._state_to_change = None
            
            self._state_start_ms = time.ticks_ms() # tu przenioslem 22.11.2025
            self._run_entry_action(None)
            return # Run "do" action in next cycle.
        
        event = (   forced_event if forced_event 
                    else self._events.popleft() if self._events 
                    else None )
        self._run_do_action(event)
            
    @property
    def current_state(self):
        """ Returns the current state of the state machine. """
        return self._current_state