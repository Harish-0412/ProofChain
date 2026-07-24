"""Package scope specialist module."""

from __future__ import annotations

from proofchain.schemas.packages import AuditPackageInput


class PackageScopeSpecialist:
    specialist_name = "package_scope"

    def run(self, input_data: AuditPackageInput) -> dict:
        return {
            "requirement_ids": input_data.workflow.requirement_scope,
            "departments": input_data.workflow.department_scope,
            "academic_year": input_data.workflow.academic_year,
        }
