from odoo import models, _
from odoo.exceptions import ValidationError
import math


class ValidationMixin(models.AbstractModel):
    _name = 'common.validation.mixin'
    _description = 'Reusable validation utilities'

    def _validate_positive(self, value, field_label="Value"):
        """
        Validate value > 0
        """
        if value <= 0:
            raise ValidationError(
                _("%s must be greater than 0.") % field_label
            )

    def _validate_decimal_places(self, value, max_digits=1, field_label="Value"):
        multiplier = 10 ** max_digits
        if not math.isclose(value * multiplier, round(value * multiplier)):
            raise ValidationError(
                _("%s cannot have more than %s decimal place(s).")
                % (field_label, max_digits)
            )

    def _validate_positive_with_decimal_limit(self, field_name, max_digits=1):
        field = self._fields[field_name]
        field_label = field.string
        for record in self:
            value = record[field_name]
            record._validate_positive(value, field_label)
            record._validate_decimal_places(value, max_digits, field_label)