import streamlit as st
from api_client import APIClient
import json

st.set_page_config(
    page_title="AI Dev Agent - Test UI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Development Agent - Testing Interface")

api_client = APIClient()

health = api_client.get_health()
if health.get("status") == "healthy":
    st.success("✅ API is healthy and running")
else:
    st.error(f"❌ API is not responding: {health.get('error', 'Unknown error')}")

st.markdown("---")

tabs = st.tabs([
    "🧠 LLM Testing",
    "🐙 GitHub",
    "📋 Jira",
    "📚 Confluence",
    "📊 Grafana",
    "🔄 Context Resolver",
    "🔍 Code Analysis",
    "✅ Test Generation",
    "📝 Doc Orchestrator",
    "🚀 Full Analysis"
])

with tabs[0]:
    st.header("🧠 LLM Provider Testing")
    
    # Settings row
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("**Thinking Mode:** See detailed backend operations in real-time")
    with col2:
        provider = st.selectbox("Provider", ["together", "azure"], index=0, label_visibility="collapsed")
    with col3:
        show_details = st.checkbox("Show Backend Details", value=False, help="Display detailed backend operations")
    
    # Input area
    prompt = st.text_area(
        "Enter your prompt:",
        value="What are some best practices for writing clean Python code?",
        height=100,
        placeholder="Type your message here..."
    )
    
    if st.button("Test LLM", key="test_llm", type="primary", use_container_width=True):
        import time
        
        # Chat-like container
        chat_container = st.container()
        
        with chat_container:
            # User message bubble
            st.markdown(f"""
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <strong>You</strong><br/>
                {prompt}
            </div>
            """, unsafe_allow_html=True)
            
            # Thinking process indicator
            if show_details:
                with st.status("🚀 **Starting LLM Test...**", expanded=True) as status:
                    # Step 1: Provider Selection
                    with st.expander("🔍 Step 1: Provider Selection"):
                        st.write(f"**Selected Provider:** `{provider}`")
                        if provider == "together":
                            st.write("- **Model:** Llama-3.3-70B-Instruct-Turbo")
                            st.write("- **API:** Together AI OpenAI-compatible")
                            st.write("- **Fallback:** Azure OpenAI (if configured)")
                        else:
                            st.write("- **Model:** GPT-4 (Azure deployment)")
                            st.write("- **API:** Azure OpenAI endpoint")
                            st.write("- **Fallback:** Together AI (if configured)")
                    
                    # Step 2: API Request
                    with st.expander("📤 Step 2: Sending API Request"):
                        st.code(f"""Provider: {provider}
Prompt Length: {len(prompt)} characters
Endpoint: /api/test/llm
Method: POST""", language="text")
                    
                    # Make API call
                    start_time = time.time()
                    result = api_client.test_llm(prompt, provider)
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Step 3: API Response
                    with st.expander("📥 Step 3: API Response Received"):
                        st.write(f"**Response Time:** `{duration:.2f}s`")
                        st.write(f"**Success:** `{result.get('success', False)}`")
                        if result.get("success"):
                            response_text = result.get("response", "")
                            st.write(f"**Response Length:** `{len(response_text)} characters`")
                            if result.get("provider_used"):
                                st.write(f"**Provider Used:** `{result.get('provider_used')}`")
                            if result.get('fallback_used'):
                                st.warning("⚠️ Fallback was used")
                            if result.get("tokens"):
                                st.write(f"**Token Usage:** `{result.get('tokens')} tokens`")
                    
                    status.update(label="✅ **Complete!**", state="complete")
            else:
                # Minimal spinner without details
                with st.spinner(f"⏳ Thinking..."):
                    start_time = time.time()
                    result = api_client.test_llm(prompt, provider)
                    end_time = time.time()
                    duration = end_time - start_time
            
            # AI response bubble
            if result.get("success"):
                st.markdown(f"""
                <div style="background-color: #e8f4f8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <strong>🤖 AI Assistant ({provider})</strong><br/>
                </div>
                """, unsafe_allow_html=True)
                
                # Response content
                st.markdown(result.get("response", "No response"))
                
                # Metrics footer
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.caption(f"**Provider:** {provider.upper()}")
                with col_b:
                    st.caption(f"**Response Time:** {duration:.2f}s")
                with col_c:
                    st.caption(f"**Status:** ✅ Success")
            else:
                # Error message
                st.markdown(f"""
                <div style="background-color: #ffe8e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <strong>❌ Error</strong><br/>
                    {result.get('error', 'Unknown error')}
                </div>
                """, unsafe_allow_html=True)
                
                if show_details:
                    with st.expander("🔍 Full Error Details"):
                        st.json(result)

with tabs[1]:
    st.header("🐙 GitHub Integration Testing")
    
    repository = st.text_input("Repository (owner/repo)", value="", key="github_repo")
    
    if st.button("Test GitHub", key="test_github"):
        if repository:
            with st.spinner("Fetching GitHub issues..."):
                result = api_client.test_github(repository)
                
                if result.get("success"):
                    st.success(f"✅ Found {result.get('issues_count', 0)} open bug issues")
                    if result.get("issues"):
                        st.json(result["issues"])
                else:
                    st.error(f"❌ Error: {result.get('error')}")
        else:
            st.warning("Please enter a repository")

with tabs[2]:
    st.header("📋 Jira Integration Testing")
    
    project_key = st.text_input("Project Key", value="", key="jira_project")
    
    if st.button("Test Jira", key="test_jira"):
        if project_key:
            with st.spinner("Fetching Jira issues..."):
                result = api_client.test_jira(project_key)
                
                if result.get("success"):
                    st.success(f"✅ Found {result.get('issues_count', 0)} open issues")
                    if result.get("issues"):
                        st.json(result["issues"])
                else:
                    st.error(f"❌ Error: {result.get('error')}")
        else:
            st.warning("Please enter a project key")

with tabs[3]:
    st.header("📚 Confluence Integration Testing")
    
    space_key = st.text_input("Space Key", value="", key="confluence_space")
    
    if st.button("Test Confluence", key="test_confluence"):
        if space_key:
            with st.spinner("Fetching Confluence pages..."):
                result = api_client.test_confluence(space_key)
                
                if result.get("success"):
                    st.success(f"✅ Found {result.get('pages_count', 0)} pages")
                    if result.get("pages"):
                        st.json(result["pages"])
                else:
                    st.error(f"❌ Error: {result.get('error')}")
        else:
            st.warning("Please enter a space key")

with tabs[4]:
    st.header("📊 Grafana Integration Testing")
    
    if st.button("Test Grafana", key="test_grafana"):
        with st.spinner("Fetching Grafana alerts..."):
            result = api_client.test_grafana()
            
            if result.get("success"):
                st.success(f"✅ Found {result.get('alerts_count', 0)} alerts")
                if result.get("alerts"):
                    st.json(result["alerts"])
            else:
                st.error(f"❌ Error: {result.get('error')}")

with tabs[5]:
    st.header("🔄 Context Resolver Testing")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        issue_id = st.text_input("Issue ID", value="", key="context_issue_id")
    with col2:
        source = st.selectbox("Source", ["github", "jira", "grafana"], key="context_source")
    with col3:
        repository = st.text_input("Repository (if GitHub)", value="", key="context_repo")
    
    if st.button("Test Context Resolver", key="test_context"):
        if issue_id:
            with st.spinner("Resolving context..."):
                result = api_client.test_context_resolver(issue_id, source, repository)
                
                if result.get("success"):
                    st.success("✅ Context resolved successfully")
                    st.json(result.get("data", {}))
                else:
                    st.error(f"❌ Error: {result.get('error')}")
        else:
            st.warning("Please enter an issue ID")

with tabs[6]:
    st.header("🔍 Code Analysis Testing")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        code = st.text_area(
            "Enter code to analyze:",
            value="""def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total""",
            height=200,
            key="analysis_code"
        )
    with col2:
        context = st.text_area(
            "Context:",
            value="E-commerce checkout system",
            height=200,
            key="analysis_context"
        )
    
    if st.button("Analyze Code", key="test_analysis"):
        with st.spinner("Analyzing code..."):
            result = api_client.test_code_analysis(code, context)
            
            if result.get("success"):
                st.success("✅ Analysis complete")
                st.json(result.get("analysis", {}))
            else:
                st.error(f"❌ Error: {result.get('error')}")

with tabs[7]:
    st.header("✅ Test Generation Testing")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        test_code = st.text_area(
            "Enter code to generate tests for:",
            value="""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b""",
            height=200,
            key="test_code"
        )
    with col2:
        language = st.selectbox("Language", ["python", "javascript", "java"], key="test_language")
    
    if st.button("Generate Tests", key="test_generation"):
        with st.spinner("Generating tests..."):
            result = api_client.test_generate_tests(test_code, language)
            
            if result.get("success"):
                st.success("✅ Tests generated")
                st.code(result.get("tests", ""), language=language)
            else:
                st.error(f"❌ Error: {result.get('error')}")

with tabs[8]:
    st.header("📝 AI Documentation Orchestrator")
    st.markdown("""
    **Complete documentation workflow:** Provide a natural language prompt, and the system will:
    1. 🔍 Analyze GitHub repository code
    2. 🤖 Generate comprehensive documentation using AI
    3. 💾 Commit docs to GitHub repository
    4. 📚 Publish to Confluence (optional)
    5. 📋 Create Jira tracking ticket (optional)
    """)
    
    prompt = st.text_area(
        "📝 What documentation do you need?",
        value="Generate API documentation for the authentication module in owner/repo",
        height=100,
        help="Examples:\n- 'Document the API for owner/repo'\n- 'Create architecture docs for myorg/myapp'\n- 'Document authentication module in owner/repo'"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("GitHub Settings")
        repository = st.text_input("Repository (owner/repo)", value="", key="doc_repo")
        max_files = st.number_input("Max files to analyze", min_value=1, max_value=50, value=10)
        commit_path = st.text_input("Commit path in repo", value="docs/AI_GENERATED_DOCS.md")
        commit_message = st.text_input("Commit message (optional)", value="", placeholder="Auto-generated docs")
    
    with col2:
        st.subheader("Publishing Options")
        publish_confluence = st.checkbox("📚 Publish to Confluence", value=False)
        confluence_space_key = st.text_input(
            "Confluence Space Key",
            value="",
            disabled=not publish_confluence,
            help="The key of the Confluence space to publish to"
        )
        confluence_parent = st.text_input(
            "Parent Page ID (optional)",
            value="",
            disabled=not publish_confluence
        )
        
        create_jira = st.checkbox("📋 Create Jira Ticket", value=False)
        jira_project = st.text_input(
            "Jira Project Key",
            value="",
            disabled=not create_jira,
            help="The key of the Jira project for the ticket"
        )
    
    if st.button("🚀 Generate & Orchestrate Docs", key="orchestrate_docs", type="primary"):
        if not prompt:
            st.warning("Please enter a documentation prompt")
        elif not repository:
            st.warning("Please enter a repository (owner/repo)")
        elif publish_confluence and not confluence_space_key:
            st.warning("Please enter a Confluence space key")
        elif create_jira and not jira_project:
            st.warning("Please enter a Jira project key")
        else:
            with st.spinner("🔄 Running documentation orchestration workflow..."):
                result = api_client.orchestrate_docs(
                    prompt=prompt,
                    repository=repository,
                    max_files=max_files,
                    commit_path=commit_path,
                    commit_message=commit_message if commit_message else None,
                    publish_to_confluence=publish_confluence,
                    confluence_space_key=confluence_space_key if publish_confluence else None,
                    confluence_parent_id=confluence_parent if confluence_parent else None,
                    create_jira_ticket=create_jira,
                    jira_project_key=jira_project if create_jira else None
                )
                
                if result.get("success"):
                    st.success("✅ Documentation orchestration completed!")
                    
                    workflow = result.get("workflow_summary", {})
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.metric("Step 1", "Generated" if "completed" in workflow.get("step_1_generate", "") else "Failed")
                    with col_b:
                        st.metric("Step 2", "Committed" if "committed" in workflow.get("step_2_github", "") else "Skipped")
                    with col_c:
                        st.metric("Step 3", "Published" if "published" in workflow.get("step_3_confluence", "") else "Skipped")
                    with col_d:
                        st.metric("Step 4", "Created" if "created" in workflow.get("step_4_jira", "") else "Skipped")
                    
                    with st.expander("📄 Generated Documentation", expanded=True):
                        st.markdown(result.get("documentation", "No documentation generated"))
                    
                    with st.expander("📊 Analysis Details"):
                        st.write(f"**Files Analyzed:** {len(result.get('files_analyzed', []))}")
                        st.write(f"**Repository:** {result.get('repository', 'N/A')}")
                        if result.get("files_analyzed"):
                            st.json(result["files_analyzed"])
                    
                    if result.get("github_commit"):
                        with st.expander("💾 GitHub Commit"):
                            commit = result["github_commit"]
                            st.success(f"✅ Committed to: {commit.get('commit_url', 'N/A')}")
                            st.json(commit)
                    
                    if result.get("confluence_page"):
                        with st.expander("📚 Confluence Page"):
                            page = result["confluence_page"]
                            st.success(f"✅ Published: [{page.get('title')}]({page.get('url')})")
                            st.json(page)
                    
                    if result.get("jira_ticket"):
                        with st.expander("📋 Jira Ticket"):
                            ticket = result["jira_ticket"]
                            st.success(f"✅ Created: [{ticket.get('key')}]({ticket.get('url')})")
                            st.json(ticket)
                    
                    with st.expander("🔍 Workflow Summary"):
                        st.json(workflow)
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    if result.get("workflow_summary"):
                        with st.expander("Workflow Details"):
                            st.json(result["workflow_summary"])

with tabs[9]:
    st.header("🚀 Full Issue Analysis Workflow")
    
    col1, col2 = st.columns(2)
    with col1:
        full_issue_id = st.text_input("Issue ID", value="", key="full_issue_id")
        full_source = st.selectbox("Source", ["github", "jira", "grafana"], key="full_source")
        full_repository = st.text_input("Repository", value="", key="full_repository")
    
    with col2:
        create_pr = st.checkbox("Create Pull Request", value=False, key="create_pr")
        publish_docs = st.checkbox("Publish Documentation", value=False, key="publish_docs")
        confluence_space = st.text_input(
            "Confluence Space (if publishing docs)",
            value="",
            key="full_confluence_space",
            disabled=not publish_docs
        )
    
    if st.button("Run Full Analysis", key="full_analysis", type="primary"):
        if full_issue_id:
            with st.spinner("Running full analysis workflow..."):
                result = api_client.analyze_issue(
                    issue_id=full_issue_id,
                    source=full_source,
                    repository=full_repository,
                    create_pr=create_pr,
                    publish_docs=publish_docs,
                    confluence_space=confluence_space if publish_docs else None
                )
                
                if "analysis" in result:
                    st.success("✅ Analysis complete!")
                    
                    with st.expander("📊 Analysis Results", expanded=True):
                        st.json(result.get("analysis", {}))
                    
                    with st.expander("🔧 Fixes Generated"):
                        st.write(f"Generated {result.get('fixes_count', 0)} fixes")
                    
                    if result.get("pr_url"):
                        st.success(f"✅ Pull Request created: {result['pr_url']}")
                    
                    if result.get("documentation_page"):
                        st.success(f"✅ Documentation published: {result['documentation_page']}")
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter an issue ID")

st.markdown("---")
st.caption("AI Development Agent - Automated Bug Fixing & Analysis Platform")
