from langgraph.graph import Graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from typing import Dict, Any
import os

# Load API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Define agent roles and their system prompts
AGENT_ROLES = {
    "generalist": "You are a helpful AI assistant. Provide general information and assistance.",
    "technical": "You are a technical expert. Provide detailed, accurate technical information. "
                "Include code examples when relevant and explain concepts clearly.",
    "creative": "You are a creative writer. Provide imaginative, engaging responses. "
               "Use vivid language and storytelling techniques.",
    "analytical": "You are an analytical thinker. Break down problems logically. "
                 "Provide structured comparisons, pros/cons, and evidence-based reasoning."
}

class MultiAgentChat:
    def __init__(self):
        # Single LLM instance with consistent configuration
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama3-8b-8192",
            temperature=0.5  # Balanced temperature for all agents
        )
        
    def route_input(self, user_input: str) -> str:
        """Determine which agent should handle the input based on content"""
        user_input = user_input.lower()
        
        # Technical queries
        if any(word in user_input for word in ["code", "algorithm", "technical", 
                                             "programming", "how to implement"]):
            return "technical"
        
        # Creative requests
        elif any(word in user_input for word in ["story", "poem", "creative", 
                                               "imagine", "write me a"]):
            return "creative"
        
        # Analytical questions
        elif any(word in user_input for word in ["analyze", "compare", "why", 
                                               "pros and cons", "explain the difference"]):
            return "analytical"
        
        # Default to generalist
        return "generalist"
    
    def generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using the appropriate agent"""
        messages = state["messages"]
        last_message = messages[-1].content
        
        # Determine which agent to use
        agent_role = self.route_input(last_message)
        print(f"\n[Using {agent_role} agent]")  # Debug info
        
        # Create conversation context with system prompt
        conversation_context = [
            SystemMessage(content=AGENT_ROLES[agent_role]),
            *messages
        ]
        
        # Get response from LLM
        response = self.llm.invoke(conversation_context)
        return {"messages": messages + [response]}

def create_chat_workflow() -> Graph:
    """Create and configure the LangGraph workflow"""
    workflow = Graph()
    chat_system = MultiAgentChat()
    
    # Define nodes
    workflow.add_node("user_input", lambda state: {
        "messages": state["messages"] + [HumanMessage(content=input("You: "))]
    })
    
    workflow.add_node("generate_response", chat_system.generate_response)
    
    workflow.add_node("display_output", lambda state: {
        "messages": state["messages"],
        **({"output": print(f"AI: {state['messages'][-1].content}\n{'-'*40}")} 
          if state["messages"] else {})
    })
    
    # Define edges
    workflow.add_edge("user_input", "generate_response")
    workflow.add_edge("generate_response", "display_output")
    workflow.add_edge("display_output", "user_input")  # Loop back
    
    workflow.set_entry_point("user_input")
    return workflow.compile()

def main():
    """Main execution function"""
    print("Multi-Agent Chatbot initialized. Type 'quit' to exit.\n")
    
    # Initialize the app
    app = create_chat_workflow()
    
    # Initial state with welcome message
    initial_state = {"messages": [
        AIMessage(content="Hello! I'm an advanced AI assistant with multiple specialized agents. "
                        "How can I help you today?")
    ]}
    
    # Chat loop
    while True:
        try:
            result = app.invoke(initial_state)
            initial_state = result
            
            # Check for exit condition
            if (len(result["messages"]) > 0 and 
                result["messages"][-1].content.lower() == "quit"):
                print("Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            break

if __name__ == "__main__":
    # Verify API key is set
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY environment variable not set!")
        print("Please set it before running the chatbot.")
    else:
        main()
