from sc_kpm import ScModule
from .WeatherAgent import WeatherAgent
from .AgentGetProblemText import AgentGetProblemText
from .AgentCheckProblemSolutionAnswer import AgentCheckProblemSolutionAnswer


class MessageProcessingModule(ScModule):
    def __init__(self):
        super().__init__(WeatherAgent(), AgentGetProblemText(), AgentCheckProblemSolutionAnswer())
