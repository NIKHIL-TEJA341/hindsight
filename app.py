import streamlit as st
import database
from agent import get_agent_response

st.set_page_config(page_title="AI Sales Agent with Persistent Memory", layout="wide")

def main():
    # Initialize DB
    database.init_db()
    
    st.sidebar.title("Sales & Revenue Agent")
    st.sidebar.markdown("---")
    
    # User mock
    user_id = st.sidebar.text_input("User ID", value="user_123")
    
    st.sidebar.subheader("Conversations")
    
    # Get user conversations
    convs = database.get_conversations(user_id)
    
    # Setup conversation selection
    if st.sidebar.button("➕ New Chat"):
        st.session_state.current_conv_id = database.create_conversation(user_id, "New Chat")
        st.session_state.messages = []
        st.rerun()

    if "current_conv_id" not in st.session_state:
        if convs:
            st.session_state.current_conv_id = convs[0]['conversation_id']
        else:
            st.session_state.current_conv_id = database.create_conversation(user_id, "New Chat")

    # Display conversation list
    for c in convs:
        col1, col2 = st.sidebar.columns([4, 1], gap="small")
        if col1.button(f"💬 {c['title']}", key=f"btn_{c['conversation_id']}", use_container_width=True):
            st.session_state.current_conv_id = c['conversation_id']
            st.rerun()
        if col2.button("❌", key=f"del_{c['conversation_id']}", use_container_width=True):
            database.delete_conversation(c['conversation_id'])
            if st.session_state.current_conv_id == c['conversation_id']:
                del st.session_state.current_conv_id
            st.rerun()

    # Main Chat Area
    st.title("AI Sales Agent with Persistent Memory")
    st.markdown("An AI Sales Agent That Remembers Every Deal")
    st.markdown("---")
    
    # Load messages
    messages = database.get_messages(st.session_state.current_conv_id)
    
    # Display messages
    for msg in messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Save user message
        database.add_message(st.session_state.current_conv_id, "user", prompt)
        
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_text, memories = get_agent_response(
                    user_id=user_id,
                    conv_id=st.session_state.current_conv_id,
                    message=prompt
                )
                st.markdown(response_text)
                database.add_message(st.session_state.current_conv_id, "assistant", response_text)
                
                # Display optional memory panel
                if memories:
                    with st.expander("Relevant Memories (Hindsight)"):
                        for mem in memories:
                            st.write(f"- {mem}")
        
        st.rerun()

if __name__ == "__main__":
    main()
