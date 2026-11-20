from agent.llm import llm

response = llm.invoke(
    "You are a senior software engineer. Explain what an implementation plan is."
)

print(response.content)