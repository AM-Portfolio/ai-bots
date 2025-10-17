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
    "🚀 Full Analysis"
])

with tabs[0]:
    st.header("🧠 LLM Provider Testing")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.text_area(
            "Enter your prompt:",
            value="What are some best practices for writing clean Python code?",
            height=100
        )
    with col2:
        provider = st.selectbox("Provider", ["together", "azure"], index=0)
    
    if st.button("Test LLM", key="test_llm"):
        with st.spinner("Testing LLM provider..."):
            result = api_client.test_llm(prompt, provider)
            
            if result.get("success"):
                st.success("✅ LLM Response")
                st.markdown(result.get("response", "No response"))
            else:
                st.error(f"❌ Error: {result.get('error')}")

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
