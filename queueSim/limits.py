MAX_QUEUE_LENGTH = 8 # Minimal queuee length to check oppening new cash desk.
MAX_QUEUE_DURATION = 5 # number of step before opening new cashdesk. During these steps MAX_queueE_LENGTH must be satisfied

MIN_QUEUE_LENGTH = 3 # queuee length at which close the 
MIN_QUEUE_DURATION = 10 # number of steps before closing the cashdesk. During these steps MIN_queueE must be satisfied 

MINIMAL_OPENING_SPAN = 30 # Minimal steps between opening cashdesks

MAXIMAL_LONGEST_QUEUE = 12 # maximal queuee length across all cashdesks. If this limit isn't satisfied, not any cashdesks can be closed
