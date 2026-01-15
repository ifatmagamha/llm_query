import streamlit as st
import json
import ast
from streamlit_agraph import agraph, Node, Edge, Config
import os
from dotenv import load_dotenv

# SERVICE IMPORTS
from services.db import db_manager
from services.llm import llm_service

# PAGE CONFIG
st.set_page_config(
    page_title="NoSQL GenAI Query",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stChatInput {border-radius: 20px;}
    .reportview-container {background: #0E1117;}
    .sidebar .sidebar-content {background: #262730;}
    div.stButton > button {width: 100%; border-radius: 8px;}
    .status-box {padding: 10px; border-radius: 8px; margin-bottom: 10px;}
    .success {background-color: #1c4f2e; color: #a1eebb;}
    .warning {background-color: #5e4b1c; color: #f2d89e;}
    .error {background-color: #5a1e1e; color: #f29e9e;}
</style>
""", unsafe_allow_html=True)

# --- GET DB CONNECTIONS (GLOBAL) ---
db = db_manager.get_mongo_db()
neo4j_driver = db_manager.get_neo4j_driver()
r = db_manager.get_redis_client()
# HBase is handled via context manager on demand

# --- FUNCTIONS ---
def draw_movie_graph(records):
    nodes = []
    edges = []
    node_ids = set()
    edge_ids = set()

    for record in records:
        for item in record.values():
            # Node
            if hasattr(item, 'labels'): 
                n_id = item.element_id
                if n_id not in node_ids:
                    lbl = item.get('title') or item.get('name')
                    # Colors
                    color = "#FF4B4B" if "Movie" in item.labels else "#1C83E1" # Red for Movie, Blue for Actor
                    if "Director" in item.labels: color = "#FFD700" # Gold for Director
                    nodes.append(Node(id=n_id, label=lbl, color=color, size=25))
                    node_ids.add(n_id)
            # Relationship
            elif hasattr(item, 'start_node'): 
                e_id = item.element_id
                if e_id not in edge_ids:
                    edges.append(Edge(
                        source=item.start_node.element_id, 
                        target=item.end_node.element_id, 
                        label=item.type,
                        color="#ffffff"
                    ))
                    edge_ids.add(e_id)

    if not nodes:
        return None

    config = Config(
        width=800, 
        height=500, 
        directed=True, 
        physics=True, 
        hierarchical=False,
        nodeHighlightBehavior=True, 
        highlightColor="#F7A7A6",
        collapsible=True
    )
    return agraph(nodes=nodes, edges=edges, config=config)

# --- SIDEBAR: SYSTEM STATUS ---
with st.sidebar:
    st.header("🔌 System Status")
    
    # 1. Redis
    if r:
        try:
            r.ping()
            keys = r.keys("query:*")
            st.markdown(f'<div class="status-box success">✅ Redis Active<br><small>{len(keys)} Cached Queries</small></div>', unsafe_allow_html=True)
            if st.button("🧹 Clear Cache"):
                for k in keys: r.delete(k)
                st.rerun()
        except:
             st.markdown('<div class="status-box error">❌ Redis Unreachable</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box warning">⚠️ Redis Not Configured</div>', unsafe_allow_html=True)

    # 2. HBase
    hbase_pool_ctx = db_manager.get_hbase_connection()
    if hbase_pool_ctx:
        try:
            with hbase_pool_ctx as conn:
                tables = conn.tables()
                t_names = [t.decode() for t in tables]
            st.markdown(f'<div class="status-box success">✅ HBase Active<br><small>Tables: {t_names}</small></div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="status-box error">❌ HBase Error<br><small>{str(e)[:50]}...</small></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box warning">⚠️ HBase Disconnected</div>', unsafe_allow_html=True)
        
    st.divider()
    st.markdown("### 📚 Supported Models")
    st.markdown("- **Mongo**: Document Store")
    st.markdown("- **Neo4j**: Graph Knowledge")
    st.markdown("- **HBase**: Big Data Column")

# --- MAIN UI ---
st.title("🤖 Intelligent Data Query")
st.caption("Ask questions about movies using natural language. We'll query MongoDB, Neo4j, and HBase for you.")

# Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis prêt à analyser vos demandes sur la base de films."}]

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- USER INPUT & LOGIC ---
if prompt := st.chat_input("Ex: 'Find movies by Nolan' or 'Add a movie named Inception'"):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Process
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🧠 **Analysing schema & generating queries...**")
        
        # Call LLM (Skipping Redis Cache for now to force new JSON format)
        llm_res = llm_service.generate_query(prompt)
        
        if "error" in llm_res:
            message_placeholder.error(f"Generate Error: {llm_res['error']}")
            if "raw" in llm_res:
                 with st.expander("Debug Raw"):
                     st.code(llm_res['raw'])
            st.stop()
        else:
            result = llm_res
            # Update Session State
            st.session_state.last_result = result
            
            # Display Strategy
            strategy = result.get('strategy', {})
            final_response = f"""
**Stratégie:** {strategy.get('analysis', 'N/A')}
**Optimisation:** {strategy.get('optimization', 'N/A')}
"""
            message_placeholder.markdown(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})

# --- RESULTS DASHBOARD ---
if st.session_state.last_result:
    res = st.session_state.last_result
    st.divider()
    st.subheader("🔍 Query Execution Dashboard")
    
    # Debug Raw JSON
    with st.expander("🛠️ View Raw JSON Response"):
        st.json(res)

    t1, t2, t3, t4 = st.tabs(["🍃 **MongoDB**", "🕸️ **Neo4j**", "🐘 **HBase**", "🔴 **Redis**"])
    
    # GLOBAL TYPE
    q_type = res.get('sql_type', 'READ')
    
    # 1. MongoDB
    with t1:
        mongo_data = res.get('mongo', {})
        st.info(f"Explanation: {mongo_data.get('explanation', '')}")
        st.code(json.dumps(mongo_data.get('query', {}), indent=2), language="json")
        
        if q_type == "READ":
            if st.button("🚀 Run Mongo Find", key="btn_mongo_read"):
                try:
                    items = list(db.movies.find(mongo_data.get('query', {})).limit(5))
                    st.dataframe(items)
                except Exception as e:
                    st.error(f"Error: {e}")
        elif q_type == "WRITE":
            if st.button("⚠️ Confirm INSERT", key="btn_mongo_write", type="primary"):
                st.warning("Write logic to be implemented based on 'query' payload")
                # db.movies.insert_one(mongo_data.get('query'))
    
    # 2. Neo4j
    with t2:
        neo_data = res.get('neo4j', {})
        st.info(f"Explanation: {neo_data.get('explanation', '')}")
        st.code(neo_data.get('query', ''), language="cypher")
        
        if st.button("🚀 Run Cypher", key="btn_neo"):
            if neo4j_driver:
                with neo4j_driver.session() as session:
                    try:
                        g_res = session.run(neo_data.get('query', ''))
                        records = list(g_res)
                        if records:
                            st.success(f"Graph nodes found: {len(records)}")
                            draw_movie_graph(records)
                        else:
                            st.info("Query executed. No visual results.")
                    except Exception as e:
                        st.error(f"Cypher Error: {e}")

    # 3. HBase
    with t3:
        hbase_data = res.get('hbase', {})
        st.info(f"Explanation: {hbase_data.get('explanation', '')}")
        
        method = hbase_data.get('method', 'scan')
        params = hbase_data.get('params', {})
        st.write(f"**Method:** `{method}`")
        st.json(params)
        
        if st.button(f"🚀 Execute HBase {method.upper()}", key="btn_hbase"):
            hbase_pool_ctx = db_manager.get_hbase_connection()
            if hbase_pool_ctx:
                try:
                    with hbase_pool_ctx as conn:
                        table = conn.table('movies')
                        
                        if method == 'get':
                            rk = params.get('row_key')
                            if rk:
                                row = table.row(rk.encode())
                                st.write(row)
                            else:
                                st.error("Missing RowKey for GET")
                        
                        elif method == 'put':
                            # Safe Write
                            rk = params.get('row_key')
                            data = params.get('data')
                            if rk and data:
                                # warning: data values must be bytes
                                b_data = {k.encode(): v.encode() for k,v in data.items()}
                                table.put(rk.encode(), b_data)
                                st.success(f"Row {rk} inserted!")
                            else:
                                st.error("Invalid PUT params")

                        elif method == 'scan':
                            # Helper for filter strings would go here
                            scanner = table.scan(limit=5)
                            rows = [{k.decode(): v.decode() for k,v in data.items()} for key, data in scanner]
                            st.dataframe(rows)
                except Exception as e:
                    st.error(f"HBase Error: {e}")
            else:
                st.error("HBase Disconnected")

    # 4. Redis
    with t4:
        redis_data = res.get('redis', {})
        st.info(f"Explanation: {redis_data.get('explanation', '')}")
        cmd = redis_data.get('command', '')
        st.code(cmd, language="bash")
        
        if st.button("🚀 Execute Redis", key="btn_redis"):
            if r:
                try:
                    parts = cmd.split()
                    if not parts:
                         st.warning("Empty command")
                    else:
                        op = parts[0].upper()
                        if op == "GET" and len(parts) > 1:
                            val = r.get(parts[1])
                            st.write(f"**Value:** {val}")
                        elif op == "SET" and len(parts) > 2:
                             # Basic set implementation
                             val = " ".join(parts[2:])
                             r.set(parts[1], val)
                             st.success(f"Set {parts[1]} = {val}")
                        else:
                            st.info("Complex command not fully implemented in UI demo")
                except Exception as e:
                    st.error(f"Redis Error: {e}")

