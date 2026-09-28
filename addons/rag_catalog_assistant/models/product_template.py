import hashlib

from odoo import models

from ..services.embeddings import generate_placeholder_embedding

DIMENSIONS_PARAM = "rag_catalog_assistant.embedding_dimensions"
DEFAULT_DIMENSIONS = 384
PLACEHOLDER_MODEL_NAME = "placeholder-hash-v1"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_reindex_catalog(self):
        """(Re)compute and store the embedding for each product in self.

        Uses a deterministic placeholder vector, not a real embedding model -
        that comes in a later step. This only proves the pipeline (text in,
        vector stored in pgvector) works end to end.
        """
        dimensions = int(
            self.env["ir.config_parameter"].sudo().get_param(
                DIMENSIONS_PARAM, DEFAULT_DIMENSIONS
            )
        )
        embedding_model = self.env["rag.catalog.embedding"]
        for product in self:
            text = product._build_rag_content_text()
            checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
            record = embedding_model.search(
                [("product_template_id", "=", product.id)], limit=1
            )
            if (
                record
                and record.checksum == checksum
                and record.embedding_dimensions == dimensions
            ):
                continue  # content unchanged, skip recomputation

            values = {
                "content_text": text,
                "embedding_model": PLACEHOLDER_MODEL_NAME,
                "embedding_dimensions": dimensions,
                "checksum": checksum,
            }
            if record:
                record.write(values)
            else:
                record = embedding_model.create(
                    {**values, "product_template_id": product.id}
                )
            record._write_embedding(generate_placeholder_embedding(text, dimensions))

    def _build_rag_content_text(self):
        self.ensure_one()
        parts = [self.name or "", self.categ_id.display_name or "", self.description_sale or ""]
        return "\n".join(part for part in parts if part)
