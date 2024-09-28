from sc_kpm import ScModule
from .WeatherAgent import WeatherAgent
from .AgentGetProblemText import AgentGetProblemText
from .AgentCheckProblemSolutionAnswer import AgentCheckProblemSolutionAnswer
from .AgentUpdateUserKnowledgeLevel import AgentUpdateUserKnowledgeLevel
from .AgentGetHint import AgentGetHint
from .AgentGetCompleteSolution import AgentGetCompleteSolution
from .AgentGetShortSolution import AgentGetShortSolution

class MessageProcessingModule(ScModule):
    def __init__(self):
        super().__init__(WeatherAgent(), AgentGetProblemText(), AgentCheckProblemSolutionAnswer(), AgentUpdateUserKnowledgeLevel(), AgentGetHint(), AgentGetCompleteSolution(), AgentGetShortSolution())
