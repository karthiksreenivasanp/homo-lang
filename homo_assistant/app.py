import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Define Tools
def create_file(filename: str, content: str) -> str:
    """Creates a new file with the given content."""
    try:
        with open(filename, "w") as f:
            f.write(content)
        return f"Success: created file {filename}"
    except Exception as e:
        return f"Error: {e}"

def read_file(filename: str) -> str:
    """Reads content from an existing file."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def edit_file(filename: str, search_string: str, replace_string: str) -> str:
    """Edits a file by replacing a specific search_string with replace_string."""
    try:
        with open(filename, "r") as f:
            content = f.read()
        if search_string not in content:
            return "Error: search_string not found in file."
        content = content.replace(search_string, replace_string)
        with open(filename, "w") as f:
            f.write(content)
        return f"Success: edited file {filename}"
    except Exception as e:
        return f"Error: {e}"

# Langchain Tools list
tools = [create_file, read_file, edit_file]

# Load Homo Knowledge
try:
    with open("homo_cheat_sheet.txt", "r") as f:
        homo_knowledge = f.read()
except FileNotFoundError:
    homo_knowledge = "You are an expert AI Assistant specialized in the Homo programming language."

st.set_page_config(page_title="Homo AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 Homo Language AI Assistant")
st.markdown("I know everything about the Homo language! Ask me to write scripts, explain concepts, or create files directly on your computer.")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    backend = st.radio("Choose Backend", ["Groq (Fast Cloud)", "Ollama (Local)"])
    
    if backend == "Groq (Fast Cloud)":
        groq_api_key = st.text_input("Groq API Key", type="password")
        st.markdown("[Get a free Groq API key](https://console.groq.com/)")
    else:
        ollama_model = st.text_input("Ollama Model Name", value="llama3")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Input
if prompt := st.chat_input("Ask me to write a Homo script..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Setup LLM
    llm = None
    if backend == "Groq (Fast Cloud)" and groq_api_key:
        llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile")
    elif backend == "Ollama (Local)":
        llm = ChatOllama(model=ollama_model)
    else:
        st.error("Please configure the backend in the sidebar!")
    
    if llm:
        try:
            # Bind tools
            llm_with_tools = llm.bind_tools(tools)
            
            # Prepare messages
            langchain_messages = [SystemMessage(content=f"{homo_knowledge}\n\nYou have access to tools to create, read, and edit files on the user's hard drive. ONLY use these tools if the user explicitly asks you to create, save, or edit a script. Otherwise, just converse normally and answer their questions.")]
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                else:
                    langchain_messages.append(AIMessage(content=msg["content"]))

            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                response = llm_with_tools.invoke(langchain_messages)
                
                # Handle tool calls
                if response.tool_calls:
                    tool_output = "I executed the following actions:\n"
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        args = tool_call["args"]
                        if tool_name == "create_file":
                            res = create_file(**args)
                        elif tool_name == "read_file":
                            res = read_file(**args)
                        elif tool_name == "edit_file":
                            res = edit_file(**args)
                        tool_output += f"- `{tool_name}`: {res}\n"
                    
                    st.markdown(tool_output)
                    st.session_state.messages.append({"role": "assistant", "content": tool_output})
                else:
                    st.markdown(response.content)
                    st.session_state.messages.append({"role": "assistant", "content": response.content})
                    
        except Exception as e:
            st.error(f"Error communicating with LLM: {e}")
