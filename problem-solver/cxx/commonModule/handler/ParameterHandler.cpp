#include "ParameterHandler.hpp"

#include "sc-agents-common/utils/CommonUtils.hpp"

#include "utils//RelationUtils.hpp"
#include "utils//ScTemplateUtils.hpp"

using namespace commonModule;

ScAddr ParameterHandler::updateMeasurableParameter(
    const ScAddr & entity,
    const ScAddr & parameterClass,
    const ScAddr & measurementRel,
    const double & number)
{
  ScAddr numberNode = this->numberHandler->getNumberNode(number);
  ScAddr parameterNode = getParameterNode(parameterClass, measurementRel, numberNode);
  if (!this->context->HelperCheckEdge(parameterNode, entity, ScType::EdgeAccessConstPosPerm))
  {
    ScAddr currentParameterNode = this->findParameterNodeByEntity(parameterClass, entity);
    if (currentParameterNode.IsValid())
    {
      RelationUtils::eraseAllEdges(this->context, currentParameterNode, entity, ScType::EdgeAccessConstPosPerm);
    }
    this->context->CreateEdge(ScType::EdgeAccessConstPosPerm, parameterNode, entity);
  }
  return parameterNode;
}

ScAddr ParameterHandler::getParameterNode(
    const ScAddr & parameterClass,
    const ScAddr & measurementRel,
    const ScAddr & numberNode)
{
  ScAddr parameterNode = findParameterNodeByNumber(parameterClass, measurementRel, numberNode);
  if (!parameterNode.IsValid())
  {
    parameterNode = this->generateParameterNode(parameterClass, measurementRel, numberNode);
  }

  return parameterNode;
};

ScAddr ParameterHandler::findParameterNodeByNumber(
    const ScAddr & parameterClass,
    const ScAddr & measurementRel,
    const ScAddr & numberNode)
{
  ScAddr parameterNode = ScAddr();
  ScTemplate scTemplate;
  scTemplate.Triple(parameterClass, ScType::EdgeAccessVarPosPerm, ScType::NodeVar >> "_parameter_node");
  scTemplate.TripleWithRelation(
      "_parameter_node", ScType::EdgeDCommonVar, numberNode, ScType::EdgeAccessVarPosPerm, measurementRel);
  ScAddrVector parameterNodes = ScTemplateUtils::getAllWithKey(this->context, scTemplate, "_parameter_node");
  if (parameterNodes.size() == 1)
    parameterNode = parameterNodes[0];
  else if (parameterNodes.size() > 1)
  {
    SC_LOG_DEBUG(
        "ParameterHandler More then 1 parameter node of " + this->context->HelperGetSystemIdtf(parameterClass) +
        " by number " + this->context->HelperGetSystemIdtf(numberNode));
  }
  else
  {
    SC_LOG_DEBUG(
        "ParameterHandler found no parameter node of " + this->context->HelperGetSystemIdtf(parameterClass) +
        " by number " + this->context->HelperGetSystemIdtf(numberNode));
  }

  return parameterNode;
};

ScAddr ParameterHandler::findParameterNodeByEntity(const ScAddr & parameterClass, const ScAddr & entity)
{
  ScAddr parameterNode = ScAddr();
  ScTemplate scTemplate;
  scTemplate.Triple(parameterClass, ScType::EdgeAccessVarPosPerm, ScType::NodeVar >> "_parameter_node");
  scTemplate.Triple("_parameter_node", ScType::EdgeAccessVarPosPerm, entity);
  ScAddrVector parameterNodes = ScTemplateUtils::getAllWithKey(this->context, scTemplate, "_parameter_node");
  if (parameterNodes.size() == 1)
    parameterNode = parameterNodes[0];
  else if (parameterNodes.size() > 1)
  {
    SC_LOG_DEBUG(
        "ParameterHandler More then 1 parameter node of " + this->context->HelperGetSystemIdtf(parameterClass) +
        " for entity " + this->context->HelperGetSystemIdtf(entity));
  }
  else
  {
    SC_LOG_DEBUG(
        "ParameterHandler found no parameter node of " + this->context->HelperGetSystemIdtf(parameterClass) +
        " for entity " + this->context->HelperGetSystemIdtf(entity));
  }

  return parameterNode;
};

ScAddr ParameterHandler::generateParameterNode(
    const ScAddr & parameterClass,
    const ScAddr & measurementRel,
    const ScAddr & numberNode)
{
  ScTemplate scTemplate;
  scTemplate.Triple(parameterClass, ScType::EdgeAccessVarPosPerm, ScType::NodeVar >> "_parameter_node");
  scTemplate.TripleWithRelation(
      "_parameter_node", ScType::EdgeDCommonVar, numberNode, ScType::EdgeAccessVarPosPerm, measurementRel);

  ScTemplateGenResult genResult;
  this->context->HelperGenTemplate(scTemplate, genResult);
  return genResult["_parameter_node"];
};

ParameterHandler::ParameterHandler(ScMemoryContext * ms_context)
{
  this->context = ms_context;
  this->numberHandler = new NumberHandler(ms_context);
}

ParameterHandler::~ParameterHandler()
{
  delete this->numberHandler;
}
