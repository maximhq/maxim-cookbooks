# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Financial coordinator: provide reasonable investment strategies"""

import os
from dotenv import load_dotenv
import logging

# Configure root logger
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
#     force=True  # Force reconfiguration of the root logger
# )

# # Explicitly enable loggers for Google ADK and GenAI packages
# # These packages use their own logger instances that need explicit configuration
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

# # Enable debug logging for Google ADK components
# logging.getLogger('google.adk').setLevel(logging.DEBUG)
# logging.getLogger('google.genai').setLevel(logging.DEBUG)
# logging.getLogger('google.cloud').setLevel(logging.INFO)  # Less verbose for cloud APIs

# # Add a console handler if one doesn't exist
# if not logger.handlers:
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.DEBUG)
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)

# print("🔍 Logging enabled at DEBUG level for Google ADK components")

# Load environment variables from .env file
load_dotenv()

# Use Gemini API instead of Vertex AI (simpler setup)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

# Import the agent first
from . import agent

# Try to set up Maxim instrumentation with custom callbacks
try:
    import time
    from maxim import Maxim
    from maxim.logger.google_adk import instrument_google_adk

    # Define custom callbacks to demonstrate tweaking
    class MaximCallbacks:
        def __init__(self):
            self.generation_start_times = {}
        
        async def before_generation(self, callback_context, llm_request, model_info, messages):
            """Track generation start time and log model info"""
            gen_id = id(llm_request)
            self.generation_start_times[gen_id] = time.time()
            print(f"🔵 [CALLBACK] Calling {model_info['model']} with {len(messages)} messages")
        
        async def after_generation(self, callback_context, llm_response, generation, 
                                  generation_result, usage_info, content, tool_calls):
            """Add custom metrics and tags to generation"""
            gen_id = id(callback_context.llm_request) if hasattr(callback_context, 'llm_request') else None
            
            # Calculate latency
            if gen_id and gen_id in self.generation_start_times:
                latency = time.time() - self.generation_start_times[gen_id]
                generation.add_metric("latency_seconds", latency)
                
                # Add tokens per second metric
                total_tokens = usage_info.get('total_tokens', 0)
                if latency > 0:
                    generation.add_metric("tokens_per_second", total_tokens / latency)
                
                del self.generation_start_times[gen_id]
            
            # Add custom tags
            generation.add_tag("model_provider", "google")
            generation.add_tag("has_tool_calls", "yes" if tool_calls else "no")
            
            print(f"🟢 [CALLBACK] Generation complete: {usage_info.get('total_tokens', 0)} tokens, {len(tool_calls) if tool_calls else 0} tool calls")
        
        async def before_trace(self, invocation_context, user_input):
            """Log trace start"""
            print(f"📝 [CALLBACK] Starting trace for: {user_input[:50]}...")
        
        async def after_trace(self, invocation_context, trace, agent_output, trace_usage):
            """Add custom metadata to trace"""
            # Calculate estimated cost (example: $0.01 per 1000 tokens)
            total_tokens = trace_usage.get('total_tokens', 0)
            estimated_cost = (total_tokens / 1000) * 0.01
            
            # Add custom tags
            trace.add_tag("estimated_cost_usd", f"${estimated_cost:.4f}")
            trace.add_tag("token_efficiency", "high" if total_tokens < 2000 else "medium" if total_tokens < 5000 else "low")
            
            # Add custom metrics
            trace.add_metric("estimated_cost", estimated_cost)
            
            print(f"✅ [CALLBACK] Trace complete: {total_tokens} tokens, ~${estimated_cost:.4f}")
        
        async def before_span(self, invocation_context, parent_context):
            """Log span start"""
            agent_name = invocation_context.agent.name
            print(f"🔷 [CALLBACK] Creating span for agent: {agent_name}")
        
        async def after_span(self, invocation_context, agent_span, agent_output):
            """Add custom metadata to span"""
            agent_name = invocation_context.agent.name
            output_length = len(agent_output) if agent_output else 0
            
            # Add custom tags (Span only supports tags and metadata, not metrics)
            agent_span.add_tag("agent_name", agent_name)
            agent_span.add_tag("output_category", "long" if output_length > 500 else "short")
            agent_span.add_tag("output_length", str(output_length))
            
            # Add metadata for more complex data
            agent_span.add_metadata({
                "output_stats": {
                    "length": output_length,
                    "category": "long" if output_length > 500 else "short"
                }
            })
            
            print(f"🔶 [CALLBACK] Span complete for {agent_name}: {output_length} chars output")
    
    # Create callbacks instance
    callbacks = MaximCallbacks()
    
    # Initialize Maxim with callbacks
    maxim = Maxim()
    instrument_google_adk(
        maxim.logger(), 
        debug=True,
        before_generation_callback=callbacks.before_generation,
        after_generation_callback=callbacks.after_generation,
        before_trace_callback=callbacks.before_trace,
        after_trace_callback=callbacks.after_trace,
        before_span_callback=callbacks.before_span,
        after_span_callback=callbacks.after_span,
    )
    
    print("✅ Maxim instrumentation with custom callbacks enabled!")
    
    # Export the agent
    root_agent = agent.root_agent
    
except ImportError as e:
    print(f"⚠️  Could not initialize Maxim instrumentation: {e}")
    print("💡 Running without Maxim logging")
    # Fall back to just using the agent without Maxim
    root_agent = agent.root_agent
