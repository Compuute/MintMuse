# crew_definition.py

from agents.root_agent import root_agent

# This function will be called from FastAPI to handle agent execution
def kickoff_crew(user_input: str) -> str:
    """
    Executes the root agent with the given user input and returns the result.
    """
    return root_agent.run(input=user_input)
