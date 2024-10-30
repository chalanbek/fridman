from sc_kpm import ScModule
from .WeatherAgent import WeatherAgent
from .AgentGetProblemText import AgentGetProblemText
from .AgentCheckProblemSolutionAnswer import AgentCheckProblemSolutionAnswer
from .AgentUpdateUserKnowledgeLevel import AgentUpdateUserKnowledgeLevel
from .AgentUpdateStatistics import AgentUpdateStatistics
from .AgentGetHint import AgentGetHint
from .AgentGetCompleteSolution import AgentGetCompleteSolution
from .AgentGetShortSolution import AgentGetShortSolution
from .AgentCreateUserProfile import AgentCreateUserProfile
from .AgentGetUserProfile import AgentGetUserProfile
from .AgentGetSolutionAnswer import AgentGetSolutionAnswer
from .AgentGetCatalog import AgentGetCatalog
from .AgentGetCatalogProblems import AgentGetCatalogProblems
from .AgentGetCatalogTheorems import AgentGetCatalogTheorems
from .AgentProblemMatchingForUser import AgentProblemMatchingForUser
from .AgentGetTheoremText import AgentGetTheoremText
class MessageProcessingModule(ScModule):
    def __init__(self):
        super().__init__(WeatherAgent(), AgentGetProblemText(), AgentCheckProblemSolutionAnswer(), 
                         AgentUpdateUserKnowledgeLevel(), AgentGetHint(), AgentGetCompleteSolution(), 
                         AgentGetShortSolution(), AgentCreateUserProfile(), AgentGetUserProfile(), 
                         AgentGetSolutionAnswer(), AgentGetCatalog(), AgentUpdateStatistics(), AgentGetCatalogProblems(), 
                         AgentGetCatalogTheorems(), AgentProblemMatchingForUser(), AgentGetTheoremText())
