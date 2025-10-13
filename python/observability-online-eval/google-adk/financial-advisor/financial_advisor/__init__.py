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

# Load environment variables from .env file
load_dotenv()

# Use Gemini API instead of Vertex AI (simpler setup)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

# Import the agent first
from . import agent

# Try to set up Maxim instrumentation
try:
    from maxim import Maxim
    from maxim.logger.google_adk import instrument_google_adk

    print("🔌 Initializing Maxim instrumentation for Google ADK...")
    maxim = Maxim()
    maxim_logger = maxim.logger()

    # Apply instrumentation patches to Google ADK
    instrument_google_adk(maxim_logger, debug=True)

    print("✅ Maxim instrumentation complete!")
    
    # Export the agent (instrumentation will capture it automatically)
    root_agent = agent.root_agent
    
except ImportError as e:
    print(f"⚠️  Could not initialize Maxim instrumentation: {e}")
    print("💡 Running without Maxim logging")
    # Fall back to just using the agent without Maxim
    root_agent = agent.root_agent
