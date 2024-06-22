import os
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import streamlit as st
import json

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv('MONGO_URI')

# Function to connect to MongoDB
def get_mongo_client(uri):
    try:
        client = MongoClient(uri)
        return client
    except errors.ConnectionError as e:
        st.error(f"Could not connect to MongoDB: {e}")
        return None

# Connect to MongoDB
client = get_mongo_client(MONGO_URI)

if client:
    # Initialize session state to store database and collection names and query results
    if 'databases' not in st.session_state:
        st.session_state['databases'] = []
    if 'collections' not in st.session_state:
        st.session_state['collections'] = []
    if 'query_results' not in st.session_state:
        st.session_state['query_results'] = []
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 0
    if 'total_docs' not in st.session_state:
        st.session_state['total_docs'] = 0

    # Sidebar for inputting database, collection, query, and filters
    st.sidebar.title("MongoDB Configuration")

    # Button to display all database names
    if st.sidebar.button("Show All Databases"):
        try:
            st.session_state['databases'] = client.list_database_names()
            st.sidebar.success("Databases loaded successfully")
        except errors.PyMongoError as e:
            st.sidebar.error(f"Error fetching database names: {e}")

    # Dropdown for database names
    db_name = st.sidebar.selectbox("Database Name", st.session_state['databases'])

    # Function to update collection names based on selected database
    def update_collections(database_name):
        try:
            st.session_state['collections'] = client[database_name].list_collection_names()
        except errors.PyMongoError as e:
            st.sidebar.error(f"Error fetching collections: {e}")
            st.session_state['collections'] = []

    # Update collections when database name changes
    if db_name:
        update_collections(db_name)

    # Dropdown for collection names
    collection_name = st.sidebar.selectbox("Collection Name", st.session_state['collections'])

    # Sidebar for filtering
    st.sidebar.title("Filters")
    filter_field = st.sidebar.text_input("Field")
    filter_value = st.sidebar.text_input("Value")

    # Function to generate query content based on user inputs
    def generate_query(db_name, collection_name, filter_field, filter_value):
        if filter_field and filter_value:
            return json.dumps({filter_field: filter_value})
        else:
            return "{}"

    # Generate the query based on the inputs
    query_content = generate_query(db_name, collection_name, filter_field, filter_value)
    query_input = st.sidebar.text_area("Query", query_content)  # Use the generated query as the default value

    # Convert the query input string to a dictionary
    try:
        query = json.loads(query_input)
    except json.JSONDecodeError:
        st.sidebar.error("Invalid query format. Please provide a valid JSON.")
        query = {}

    # Run Query Button
    if st.sidebar.button("Run Query"):
        # Clear previous database display
        st.session_state['databases'] = []

        # Connect to the specified database and collection
        db = client[db_name]
        collection = db[collection_name]

        try:
            documents = list(collection.find(query))
            st.session_state['query_results'] = documents
            st.session_state['current_page'] = 0
            st.session_state['total_docs'] = len(documents)
        except errors.PyMongoError as e:
            st.error(f"Error fetching data: {e}")

    # Display count of documents and pagination controls in the sidebar
    if 'total_docs' in st.session_state:
        st.sidebar.write(f"Total documents: {st.session_state['total_docs']}")

        if st.session_state['total_docs'] > 0:
            total_docs = st.session_state['total_docs']
            total_pages = (total_docs + 19) // 20

            col1, col2, col3 = st.sidebar.columns([1, 2, 1])
            with col1:
                if st.sidebar.button("Previous", key="prev_btn", disabled=st.session_state['current_page'] == 0):
                    st.session_state['current_page'] -= 1
            with col3:
                if st.sidebar.button("Next", key="next_btn", disabled=st.session_state['current_page'] >= total_pages - 1):
                    st.session_state['current_page'] += 1

            page_number = st.sidebar.number_input("Page", min_value=1, max_value=total_pages, value=st.session_state['current_page'] + 1, step=1)
            if st.sidebar.button("Go to Page"):
                st.session_state['current_page'] = page_number - 1

    # Streamlit app
    st.subheader("MongoDB Data Display with Streamlit")  # Changed to smaller header

    # Pagination
    def display_documents(documents, page, page_size=20):
        start = page * page_size
        end = start + page_size
        for doc in documents[start:end]:
            st.write(doc)

    if st.session_state['query_results']:
        display_documents(st.session_state['query_results'], st.session_state['current_page'])
else:
    st.error("Could not connect to MongoDB. Please check your connection settings.")
