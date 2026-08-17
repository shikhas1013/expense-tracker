import streamlit as st
from orchestration import coordinator_agent, run_with_reflection
from orchestration.coordinator import session
from agents import Runner

st.set_page_config(
    page_title="Expense AI Agent",
)

st.title("Expense AI Agent")

with st.sidebar:
    st.header("Settings")
    use_reflection = st.checkbox("Enable reflection loop", value=True)
    st.markdown("---")
    st.markdown("""
    **Multi-Agent System**
    - Query Agent: Data retrieval
    - Analyst Agent: Insights & trends
    - Budget Agent: Budget management
    - Coordinator: Routes requests
    """)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about your expenses")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..." if not use_reflection else "Thinking with reflection..."):
            try:
                if use_reflection:
                    response = run_with_reflection(question)
                else:
                    result = Runner.run_sync(
                        coordinator_agent,
                        question,
                        session=session
                    )
                    response = result.final_output
            except Exception as e:
                response = f"Sorry, something went wrong. Please try again. (Error: {type(e).__name__})"
                st.error(f"Error: {e}")
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})