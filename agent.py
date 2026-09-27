import os
from agno.agent import Agent
from agno.models.groq import Groq
from dotenv import load_dotenv

load_dotenv()

# We will implement a simplified Memory API to mimic Hindsight's behavior 
# as per the PRD requirements if the official module requires a Postgres/Pgvector backend.
class HindsightMemoryMock:
    def __init__(self):
        import sqlite3
        self.conn = sqlite3.connect("hindsight.db", check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                user_id TEXT,
                memory_text TEXT
            )
        ''')
        self.conn.commit()

    def retain(self, user_id, content):
        self.conn.execute("INSERT INTO memories (user_id, memory_text) VALUES (?, ?)", (user_id, content))
        self.conn.commit()

    def recall(self, user_id):
        cursor = self.conn.execute("SELECT memory_text FROM memories WHERE user_id = ?", (user_id,))
        return [row[0] for row in cursor.fetchall()]

hindsight = HindsightMemoryMock()

# Define the Sales Agent
agent = Agent(
    model=Groq(id="openai/gpt-oss-120b"),
    description="You are a highly capable AI Sales & Revenue Intelligence Agent. Your goal is to help sales representatives manage deals, prepare for meetings, handle objections, and track customer requirements.",
    instructions=[
        "Always check if relevant historical context (memories) is provided and use it to personalize your response.",
        "When the user mentions new important deal information (requirements, budgets, objections, stakeholders), explicitly note it in your response so the system can retain it.",
        "Be professional, concise, and highly relevant to a sales context."
    ],
    markdown=True
)

def get_agent_response(user_id, conv_id, message):
    # 1. Hindsight Recall (Long-term memory)
    past_memories = hindsight.recall(user_id)
    
    # Format memory context
    memory_context = ""
    if past_memories:
        memory_context = "\n\nRelevant Hindsight Memories for this User:\n" + "\n".join(f"- {m}" for m in past_memories)

    # 2. Combine Context
    full_prompt = f"User Request: {message}{memory_context}\n\nPlease respond to the user based on the context above."

    # 3. Generate Response
    # In a real scenario we'd use the model specified, updating the Groq initialization if needed.
    # We use agent.run() to get the response text.
    response = agent.run(full_prompt)
    response_text = response.content

    # 4. Hindsight Retention (Extract important info)
    # For MVP demonstration, we broadened the retention logic so it catches more demo inputs.
    # In a production version, we would use another LLM call to extract structured facts.
    msg_lower = message.lower()
    retention_keywords = [
        "concern", "budget", "reject", "require", "enterprise", "timeline", "cto", "cfo",
        "name is", "i am", "want to buy", "looking for", "ps5", "need", "interested in"
    ]
    # Retain if it has a keyword OR if it's a decent sized factual statement
    if any(kw in msg_lower for kw in retention_keywords) or len(message.split()) > 7:
        hindsight.retain(user_id, message)
        
    # Also attempt to extract from agent's own summary if it starts a sentence with "I will keep" or "I've noted"
    return response_text, past_memories
