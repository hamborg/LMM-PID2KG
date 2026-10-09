# utils/default_settings.py

class Default:
    """ Default settings for the entire project """
    PROVIDER = "gemini"
    OUTPUT_FORMAT = "csv"
    LEVEL = 1  # Default experiment level [1-4]
    # EXPERIMENT = "01"  # Default experiment number (e.g. "3", "12" or "03")
    NOTE = [""]  # Default note/comment for output filename
    TIMESTAMP_FORMAT = "%m.%d_%H.%M"  # Default timestamp format for output filenames
    

    """ Default settings for experiments """
    PROMPT = [""]  # Default prompt (if not specified, will use 'prompt.md' in the experiment folder)
    RUNS = 1  # Default number of runs/tests for each experiment
    

    """ Default settings for SPARQL queries """
    QUERIES = ["A_00"]  # Default query is A_00 (Components classification)


    """ Default settings for HITL experiments """
    HITL_EXPERIMENT = "04"  # Default HITL experiment
    HITL_QUERIES = ["A_01", "V_01", "Z_02", "V_12", "Z_01"]  # Default HITL queries
    HITL_MODE = "B"  # Default HITL mode: A = conversational memory, B = stateless iterative refinement
    
    INITIAL_PROMPT = "initial_prompt.md"  # Default initial prompt for HITL sessions (should be in the same folder as hitl_prompting.py)
    SESSION_CONFIG = "session_config.json"  # Default session config filename (saved in each HITL session folder)
    WORKBOOK_NAME = "Evaluation scheme.xlsx"  # Default Excel workbook name for manual evaluation scheme (found in the evaluations folder)