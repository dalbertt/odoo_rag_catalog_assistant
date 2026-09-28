from odoo import models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_reindex_catalog(self):
        """Trigger embedding (re)generation for this product. Wired in a later step."""
        raise UserError("Reindexado de catálogo: disponible a fases posteriores.")
