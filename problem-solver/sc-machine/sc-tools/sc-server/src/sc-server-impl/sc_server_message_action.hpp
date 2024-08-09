/*
 * This source file is part of an OSTIS project. For the latest info, see http://ostis.net
 * Distributed under the MIT License
 * (See accompanying file COPYING.MIT or copy at http://opensource.org/licenses/MIT)
 */

#pragma once

#include <utility>

#include "sc_server_action.hpp"
#include "sc_server.hpp"
#include "sc-memory-json/sc_memory_json_payload.hpp"
#include "sc-memory-json/sc_memory_json_handler.hpp"
#include "sc-memory-json/sc-memory-json-action/sc_memory_json_actions_handler.hpp"
#include "sc-memory-json/sc-memory-json-event/sc_memory_json_events_handler.hpp"

class ScServerMessageAction : public ScServerAction
{
public:
  ScServerMessageAction(ScServer * server, ScServerConnectionHandle hdl, ScServerMessage msg)
    : ScServerAction(std::move(hdl))
    , m_server(server)
    , m_msg(std::move(msg))
  {
    m_actionsHandler = new ScMemoryJsonActionsHandler(server);
    m_eventsHandler = new ScMemoryJsonEventsHandler(server);
  }

  void Emit() override
  {
    try
    {
      std::string messageType = GetMessageType(m_msg);

      if (IsHealthCheck(messageType))
        OnHealthCheck(m_hdl, m_msg);
      else if (IsEvent(messageType))
        OnEvent(m_hdl, m_msg);
      else
        OnAction(m_hdl, m_msg);
    }
    catch (ScServerException const & e)
    {
      m_server->LogMessage(ScServerErrorLevel::error, e.m_msg);
    }
    catch (utils::ScException const & e)
    {
      m_server->LogMessage(ScServerErrorLevel::error, e.Description());
    }
  }

  void OnAction(ScServerConnectionHandle const & hdl, ScServerMessage const & msg)
  {
    m_server->LogMessage(ScServerErrorLevel::debug, "[request] " + msg->get_payload());
    auto const & responseText = m_actionsHandler->Handle(hdl, msg->get_payload());

    m_server->LogMessage(ScServerErrorLevel::debug, "[response] " + responseText);
    m_server->Send(hdl, responseText, ScServerMessageType::text);
  }

  void OnEvent(ScServerConnectionHandle const & hdl, ScServerMessage const & msg)
  {
    m_server->LogMessage(ScServerErrorLevel::debug, "[event] " + msg->get_payload());
    auto const & responseText = m_eventsHandler->Handle(hdl, msg->get_payload());

    m_server->LogMessage(ScServerErrorLevel::debug, "[event response] " + responseText);
    m_server->Send(hdl, responseText, ScServerMessageType::text);
  }

  void OnHealthCheck(ScServerConnectionHandle const & hdl, ScServerMessage const & msg)
  {
    ScMemoryJsonPayload response;
    try
    {
      auto * context = new ScMemoryContext(sc_access_lvl_make_max);

      ScAddr const & tempAddr = context->CreateNode(ScType::NodeConst);
      context->EraseElement(tempAddr);

      delete context;

      response = "OK";
      m_server->LogMessage(ScServerErrorLevel::info, "I'm alive...");
    }
    catch (utils::ScException const & e)
    {
      SC_LOG_ERROR(e.Description());
      response = "NO";
      m_server->LogMessage(ScServerErrorLevel::info, "I've died...");
    }

    m_server->Send(hdl, response.dump(), ScServerMessageType::text);
    m_server->CloseConnection(hdl, websocketpp::close::status::normal, "Status checked");
  }

  ~ScServerMessageAction() override
  {
    delete m_actionsHandler;
    delete m_eventsHandler;
  };

protected:
  ScServer * m_server;
  ScServerMessage m_msg;

  ScMemoryJsonHandler * m_actionsHandler;
  ScMemoryJsonHandler * m_eventsHandler;

  static std::string GetMessageType(ScServerMessage const & msg)
  {
    if (ScMemoryJsonPayload::accept(msg->get_payload()))
    {
      ScMemoryJsonPayload const & payload = ScMemoryJsonPayload::parse(msg->get_payload());
      return payload["type"].get<std::string>();
    }

    return "";
  }

  static sc_bool IsEvent(std::string const & messageType)
  {
    return messageType == "events";
  }

  static sc_bool IsHealthCheck(std::string const & messageType)
  {
    return messageType == "healthcheck";
  }
};
