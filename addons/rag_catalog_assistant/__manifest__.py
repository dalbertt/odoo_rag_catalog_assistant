{
    "name": "RAG Catalog Assistant",
    "summary": "Conversational catalog assistant (RAG + LangChain) over pgvector.",
    "description": """
Adds a retrieval-augmented conversational assistant to answer questions about
the product catalog, using embeddings stored in pgvector on the same Odoo
PostgreSQL database.
""",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "license": "LGPL-3",
    "author": "Daniel Tamayo - danielalbertotamayo@gmail.com",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "application": False,
}
