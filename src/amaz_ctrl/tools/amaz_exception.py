

class ExperimentIsRunning(Exception):
    """Exception raised when an experiment is running and parameters cannot be changed."""
    pass

class ExperimentIsPreparing(Exception):
    """Exception raised when an experiment is running and parameters cannot be changed."""
    pass

class NoScriptToRun(Exception):
    """Exception raised when no script is loaded."""
    pass