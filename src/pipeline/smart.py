import json
import time
from typing import Dict, Any, Optional

from src.connectors.base import BaseConnector
from src.llm.provider import LLMProvider
from src.rag.store import SimpleRAGStore
from src.validation.policy import PolicyValidator, SafetyException
from src.ir.models import QueryIR

class SmartPipeline:
    def __init__(self, connector: BaseConnector, llm: LLMProvider, rag: SimpleRAGStore):
        self.connector = connector
        self.llm = llm
        self.rag = rag
        self.validator = PolicyValidator(allow_writes=False) # Default safe
        self.max_retries = 2

    def set_safety(self, allow_writes: bool):
        self.validator.allow_writes = allow_writes

    def _construct_prompt(self, nlq: str, schema: Any, examples: list, error_history: list = None) -> str:
        db_type = self.connector.get_metadata().db_type
        
        prompt = f"""You are an expert NoSQL developer for {db_type}.
Your task is to translate a Natural Language Query (NLQ) into:
1. An abstract Intermediate Representation (IR) in JSON.
2. A concrete, executable query string for {db_type}.

### Database Schema
{json.dumps(schema, default=str, indent=2)}

### Similar Examples (Few-Shot)
"""
        for ex in examples:
            prompt += f"- NLQ: {ex['nlq']}\n  Query: {ex['query']}\n"
            
        if error_history:
            prompt += "\n### Previous Execution Errors (Fix these!)\n"
            for err in error_history:
                prompt += f"- Attempt: {err['query']}\n  Error: {err['error']}\n"
        
        prompt += f"""
### User Request
"{nlq}"

### Output Format
You must output ONLY a valid JSON object. Do not wrap in markdown code blocks.
Structure:
{{
  "ir": {{
    "intent": "FIND" | "AGGREGATE" | "TRAVERSAL",
    "target_collection": "...",
    "filters": [ ... ],
    "is_safe": true/false
  }},
  "query": "The actual executable string"
}}

For MongoDB: Query should be a JSON string like {{"collection": "...", "operation": "...", "args": ...}}
For Neo4j: Query is Cypher string.
For Redis: Query is command string "GET key".
For RDF: Query is SPARQL.
For HBase: Query is JSON instruction.
"""
        return prompt

    def run(self, nlq: str) -> Dict[str, Any]:
        result_log = {"steps": [], "final_result": None, "success": False}
        
        # 1. Get Metadata
        meta = self.connector.get_metadata()
        db_type = meta.db_type
        
        # 2. RAG
        examples = self.rag.retrieve(nlq, db_type)
        
        # 3. Execution Loop
        error_history = []
        
        for attempt in range(self.max_retries + 1):
            step_info = {"attempt": attempt}
            
            # Generate
            prompt = self._construct_prompt(nlq, meta.schema_summary, examples, error_history)
            llm_response = self.llm.generate(prompt)
            step_info["llm_raw"] = llm_response
            
            try:
                # Cleaning markdown if present
                clean_resp = llm_response.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_resp)
                
                ir_data = parsed.get("ir", {})
                query_str = parsed.get("query", "")
                
                step_info["parsed_ir"] = ir_data
                step_info["parsed_query"] = query_str
                
                # Validation
                self.validator.check_ir_safety(ir_data.get("intent", "UNKNOWN"))
                self.validator.check_raw_safety(query_str, db_type)
                
                # Execute
                exec_result = self.connector.execute(query_str, operation_type="write" if not ir_data.get("is_safe") else "read")
                step_info["execution"] = exec_result
                
                if exec_result.status == "success":
                    result_log["success"] = True
                    result_log["final_result"] = exec_result.payload
                    result_log["steps"].append(step_info)
                    return result_log
                else:
                    # Execution failed
                    error_history.append({"query": query_str, "error": exec_result.error_message})
            
            except json.JSONDecodeError:
                error_history.append({"query": "JSON_PARSE_ERROR", "error": "LLM output was not valid JSON"})
            except SafetyException as e:
                result_log["steps"].append(step_info)
                result_log["error"] = f"Safety Blocked: {e}"
                return result_log # Stop on safety violation
            except Exception as e:
                error_history.append({"query": "UNKNOWN", "error": str(e)})
            
            result_log["steps"].append(step_info)
            
        result_log["error"] = "Max retries exceeded"
        return result_log
