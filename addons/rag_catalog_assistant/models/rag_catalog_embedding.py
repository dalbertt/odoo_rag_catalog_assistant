from odoo import fields, models


class RagCatalogEmbedding(models.Model):
    _name = "rag.catalog.embedding"
    _description = "Catalog embedding for the RAG assistant"
    _rec_name = "product_template_id"

    product_template_id = fields.Many2one(
        "product.template", required=True, ondelete="cascade", index=True
    )
    content_text = fields.Text(
        required=True, help="Source text that was embedded (name, category, description)."
    )
    embedding_model = fields.Char(
        required=True, help="Identifier of the model/provider that produced the vector."
    )
    embedding_dimensions = fields.Integer(required=True)
    checksum = fields.Char(
        required=True,
        index=True,
        help="SHA-256 of content_text, used to skip recomputation when nothing changed.",
    )
    embedding_preview = fields.Char(
        compute="_compute_embedding_preview",
        string="Embedding (preview)",
        help="First dimensions of the stored vector, for humans to eyeball in the UI.",
    )

    _sql_constraints = [
        (
            "product_template_uniq",
            "unique(product_template_id)",
            "There can only be one embedding row per product.",
        ),
    ]

    def init(self):
        """Enable pgvector and add the embedding column.

        Odoo's ORM has no native vector field type, so the column lives
        outside it and is only ever touched through raw SQL (see
        _write_embedding/_read_embedding_previews below). Unlike
        post_init_hook (install-only), init() runs on every schema sync -
        install AND upgrade - so this stays self-healing if the column is
        ever missing (e.g. it was added to the model after the module was
        first installed).
        """
        super().init()
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS vector")
        dimensions = int(
            self.env["ir.config_parameter"].sudo().get_param(
                "rag_catalog_assistant.embedding_dimensions", 384
            )
        )
        # `dimensions` is cast to int() above, so interpolating it here is
        # safe; vector(N) does not accept N as a bind parameter in DDL.
        self.env.cr.execute(
            f"ALTER TABLE {self._table} ADD COLUMN IF NOT EXISTS embedding vector({dimensions})"
        )

    def _compute_embedding_preview(self):
        previews = self._read_embedding_previews()
        for record in self:
            record.embedding_preview = previews.get(record.id, "")

    def _read_embedding_previews(self, head=6):
        """Read the first `head` dimensions of each vector via raw SQL.

        Odoo's ORM has no native pgvector field type, so the `embedding`
        column (added in init method above) is only ever touched through raw,
        parametrized SQL - never through env['rag.catalog.embedding'].write().
        """
        if not self.ids:
            return {}
        self.env.cr.execute(
            "SELECT id, (embedding::real[])[1:%s] FROM rag_catalog_embedding "
            "WHERE id = ANY(%s) AND embedding IS NOT NULL",
            (head, self.ids),
        )
        return {
            row[0]: "[" + ", ".join(f"{value:.4f}" for value in row[1]) + ", ...]"
            for row in self.env.cr.fetchall()
        }

    def _write_embedding(self, vector):
        self.ensure_one()
        # Built from floats we control (never raw user input) and still passed
        # as a bound parameter, so this stays injection-safe despite the
        # string assembly.
        vector_literal = "[" + ",".join(repr(float(value)) for value in vector) + "]"
        self.env.cr.execute(
            "UPDATE rag_catalog_embedding SET embedding = %s::vector WHERE id = %s",
            (vector_literal, self.id),
        )
