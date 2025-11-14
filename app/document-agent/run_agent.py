from document_agent import DocumentAgent, MockDriveAdapter, VectorDBAdapter

# Helper to print document info
def print_doc(doc):
    print(f"ID       : {doc.id}")
    print(f"Name     : {doc.name}")
    print(f"Type     : {doc.mime_type}")
    print(f"Created  : {doc.created_time}")
    print(f"Modified : {doc.modified_time}")
    print(f"Size     : {doc.size}")
    print(f"URL      : {doc.drive_url}")
    print("-" * 40)

# Initialize components
drive = MockDriveAdapter()
vector_db = VectorDBAdapter()
agent = DocumentAgent(drive, vector_db)

# 1. Upload a file 
print("\n=== UPLOAD ===")
doc = agent.upload_file("example.pdf")
print("Uploaded Document:")
print_doc(doc)

# 2. Keyword search
print("\n=== KEYWORD SEARCH ===")
results = agent.keyword_search("example")
if results:
    print(f"Found {len(results)} document(s) by keyword:")
    for r in results:
        print_doc(r)
else:
    print("No documents found.")

# 3. Semantic search
print("\n=== SEMANTIC SEARCH ===")
semantic_results = agent.semantic_search([0.1, 0.2, 0.3])
if semantic_results:
    print(f"Found {len(semantic_results)} document(s) by semantic similarity:")
    for r in semantic_results:
        metadata = r['metadata']
        print(f"- ID: {metadata.id}, Name: {metadata.name}, Embedding: {r['embedding']}")
else:
    print("No documents found.")

# 4. Download a file 
print("\n=== DOWNLOAD ===")
destination_file = "downloaded_example.pdf"
agent.download_file(doc.id, destination_file)
print(f"Downloaded document to: {destination_file}")
