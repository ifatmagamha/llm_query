import streamlit as st
import json
import os
import sys
from streamlit_agraph import agraph, Node, Edge, Config

# Add project root to path
sys.path.append(os.getcwd())

from src.connectors.mongo import MongoConnector
from src.connectors.redis import RedisConnector
from src.connectors.neo4j import Neo4jConnector
from src.connectors.rdf import RdfConnector
from src.connectors.hbase import HBaseConnector
from src.llm.provider import LLMProvider
from src.rag.store import SimpleRAGStore
from src.pipeline.smart import SmartPipeline
from src.validation.policy import SafetyException

# --- CONFIG ---
st.set_page_config(
    page_title="NoSQL Research Prototype",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stChatInput {border-radius: 20px;}
    .status-box {padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #444;}
    .success {background-color: #1c4f2e; color: #a1eebb;}
    .error {background-color: #5a1e1e; color: #f29e9e;}
</style>
""", unsafe_allow_html=True)

# --- CACHE RESOURCES ---
@st.cache_resource
def get_pipeline(db_type: str):
    """Factory to create pipeline instances."""
    if db_type == "mongodb": connector = MongoConnector()
    elif db_type == "redis": connector = RedisConnector()
    elif db_type == "neo4j": connector = Neo4jConnector()
    elif db_type == "rdf": connector = RdfConnector("memory")
    elif db_type == "hbase": connector = HBaseConnector()
    else: return None
    
    llm = LLMProvider()
    rag = SimpleRAGStore()
    return SmartPipeline(connector, llm, rag)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Mode Selection
    mode = st.radio("Mode", ["Single Database", "Cross-DB Comparison"], 
                   help="Single: Interact with one DB. Cross-DB: Compare how valid NLQ translates to multiple DBs.")

    selected_db_list = []
    if mode == "Single Database":
        db = st.selectbox("Target Database", ["mongodb", "neo4j", "redis", "rdf", "hbase"])
        selected_db_list = [db]
    else:
        st.info("Comparing query generation across all paradigms.")
        selected_db_list = ["mongodb", "neo4j", "redis", "rdf", "hbase"]
    
    unsafe_mode = st.toggle("Allow Writes (Unsafe Mode)", value=False)
    
    st.divider()
    
    # Schema Explorer
    st.subheader("🔎 Schema Explorer")
    if len(selected_db_list) == 1:
        target = selected_db_list[0]
        if st.button(f"Fetch {target.upper()} Metadata"):
            try:
                p = get_pipeline(target)
                meta = p.connector.get_metadata()
                st.code(json.dumps(meta.schema_summary, indent=2, default=str), language="json")
                if "version" in str(meta):
                    st.caption(f"Connector Version: {meta.version}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")
    else:
        st.caption("Select Single Database mode to view specific schemas.")

# --- MAIN UI ---
st.title("🧠 Polyglot NoSQL Assistant")
st.markdown(f"**Objective**: {mode}")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ready. Enter a query to translate and execute."}]

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "comparisons" in msg:
            # Render Comparison Tabs
            tabs = st.tabs([c["db"].upper() for c in msg["comparisons"]])
            for i, tab in enumerate(tabs):
                comp = msg["comparisons"][i]
                with tab:
                    if comp["success"]:
                        st.success(f"Execution Success ({comp['latency']:.2f}ms)")
                        st.markdown(f"**Intent**: `{comp['intent']}`")
                        st.code(comp['query_str'], language="json" if "{" in comp['query_str'] else "sql")
                        with st.expander("Result Payload"):
                             st.json(comp['payload'])
                    else:
                        st.error(f"Failed: {comp['error']}")
        
        if "graph_data" in msg:
             config = Config(width=700, height=400, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6")
             agraph(nodes=msg["graph_data"]["nodes"], edges=msg["graph_data"]["edges"], config=config)


# Input
if prompt := st.chat_input("Enter your query (e.g., 'Who directed Inception? / Find movies with rating > 8')"):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 2. Assistant Processing
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        # Parallel Execution
        comparisons = [None] * len(selected_db_list)
        
        import concurrent.futures
        
        # Prepare pipelines in main thread to avoid Threading Context Warning
        prepared_pipes = []
        for db in selected_db_list:
            pipe = get_pipeline(db)
            if pipe: pipe.set_safety(unsafe_mode)
            prepared_pipes.append(pipe)

        def process_db(idx, db_type, pipe):
            if not pipe: return {"db": db_type, "success": False, "error": "Init Failed"}
            try:
                res = pipe.run(prompt)
                
                comp_result = {
                    "db": db_type,
                    "success": res["success"],
                    "query_str": "N/A", 
                    "payload": None,
                    "error": res.get("error"),
                    "intent": "UNKNOWN",
                    "latency": 0.0
                }
                
                if res["success"]:
                    comp_result["payload"] = res["final_result"]
                    steps = res["steps"]
                    if steps:
                        last = steps[-1]
                        comp_result["query_str"] = last.get("parsed_query", "")
                        comp_result["intent"] = last.get("parsed_ir", {}).get("intent", "UNKNOWN")
                        comp_result["latency"] = last.get("execution", {}).execution_time_ms
                return comp_result
            except Exception as e:
                return {"db": db_type, "success": False, "error": str(e)}

        with st.spinner(f"Running polyglot analysis on {len(selected_db_list)} paradigms simultaneously..."):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Pass the pre-initialized pipe
                futures = {executor.submit(process_db, i, selected_db_list[i], prepared_pipes[i]): i for i in range(len(selected_db_list))}
                for future in concurrent.futures.as_completed(futures):
                    idx = futures[future]
                    comparisons[idx] = future.result()
        
        # Graph Viz (Neo4j hook)
        graph_to_render = None
        for c in comparisons:
            if c["db"] == "neo4j" and c["success"] and isinstance(c["payload"], list) and mode == "Single Database":
                 nodes = []
                 for row in c["payload"]:
                     for k,v in row.items():
                         if isinstance(v, dict) and 'element_id' in v:
                             lbl = v.get('title') or v.get('name') or "Node"
                             nodes.append(Node(id=str(v['element_id']), label=lbl, size=20))
                 if nodes:
                     graph_to_render = {"nodes": nodes, "edges": []}
                     
        # Generate Cross-DB Insight (LLM Analysis)
        insight_text = ""
        if mode == "Cross-DB Comparison":
             success_dbs = [c for c in comparisons if c['success']]
             if len(success_dbs) > 1:
                 # Quick logic to describe differences
                 insight_text = "### 🧠 Polyglot Insight\n"
                 for c in success_dbs:
                     insight_text += f"- **{c['db'].upper()}**: Used `{c['intent']}` strategy ({c['latency']:.1f}ms).\n"
        
        # Render Output
        if mode == "Single Database":
            c = comparisons[0]
            # ... existing single db logic ...
            if c["success"]:
                content = f"✅ **{c['intent']}** generated for **{c['db'].upper()}**\n\n```\n{c['query_str']}\n```\n**Result:**"
                placeholder.markdown(content)
                st.json(c["payload"])
                msg_obj = {"role": "assistant", "content": content}
                if graph_to_render:
                    msg_obj["graph_data"] = graph_to_render
                    config = Config(width=600, height=300)
                    agraph(nodes=graph_to_render["nodes"], edges=[], config=config)
                st.session_state.messages.append(msg_obj)
            else:
                 content = f"❌ **Error** on {c['db']}: {c['error']}"
                 placeholder.error(content)
                 st.session_state.messages.append({"role": "assistant", "content": content})

        else:
            # Comparison Mode Output
            content = f"🔬 **Cross-Database Analysis Complete**\n\n{insight_text}"
            placeholder.markdown(content)
            
            # Render tabs dynamically
            tabs = st.tabs([c["db"].upper() for c in comparisons])
            for i, tab in enumerate(tabs):
                c = comparisons[i]
                with tab:
                    if c["success"]:
                        st.success(f"Success ({c['latency']:.2f}ms)")
                        st.code(c['query_str'], language="json" if c['db'] in ['mongodb', 'hbase'] else "sql")
                        st.json(c['payload'])
                    else:
                        st.error(f"Failed: {c['error']}")
            
            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": content,
                "comparisons": comparisons
            })
