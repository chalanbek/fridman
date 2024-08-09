/*
 * This source file is part of an OSTIS project. For the latest info, see http://ostis.net
 * Distributed under the MIT License
 * (See accompanying file COPYING.MIT or copy at http://opensource.org/licenses/MIT)
 */

#include "InferenceKeynodes.hpp"

#include <sc-memory/sc_memory.hpp>

namespace inference
{
ScAddr InferenceKeynodes::action_direct_inference;
ScAddr InferenceKeynodes::concept_solution;
ScAddr InferenceKeynodes::concept_success_solution;
ScAddr InferenceKeynodes::concept_template_with_links;
ScAddr InferenceKeynodes::concept_template_for_generation;
ScAddr InferenceKeynodes::atomic_logical_formula;
ScAddr InferenceKeynodes::nrel_disjunction;
ScAddr InferenceKeynodes::nrel_conjunction;
ScAddr InferenceKeynodes::nrel_negation;
ScAddr InferenceKeynodes::nrel_implication;
ScAddr InferenceKeynodes::nrel_equivalence;
ScAddr InferenceKeynodes::rrel_if;
ScAddr InferenceKeynodes::rrel_then;
ScAddr InferenceKeynodes::nrel_output_structure;

}  // namespace inference
