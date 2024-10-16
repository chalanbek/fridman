from sc_kpm import ScModule
from .WeatherAgent import WeatherAgent
from .AgentGetProblemText import AgentGetProblemText
from .AgentCheckProblemSolutionAnswer import AgentCheckProblemSolutionAnswer
from .AgentUpdateUserKnowledgeLevel import AgentUpdateUserKnowledgeLevel
from .AgentGetHint import AgentGetHint
from .AgentGetCompleteSolution import AgentGetCompleteSolution
from .AgentGetShortSolution import AgentGetShortSolution
from .AgentCreateUserProfile import AgentCreateUserProfile
from .AgentGetUserProfile import AgentGetUserProfile
from .AgentGetSolutionAnswer import AgentGetSolutionAnswer
from .AgentGetCatalog import AgentGetCatalog
class MessageProcessingModule(ScModule):
    def __init__(self):
        super().__init__(WeatherAgent(), AgentGetProblemText(), AgentCheckProblemSolutionAnswer(), 
                         AgentUpdateUserKnowledgeLevel(), AgentGetHint(), AgentGetCompleteSolution(), 
                         AgentGetShortSolution(), AgentCreateUserProfile(), AgentGetUserProfile(), 
                         AgentGetSolutionAnswer(), AgentGetCatalog())
