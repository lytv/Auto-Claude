"""
Pattern Inference Engine
========================

Deduces development protocols and requirements from raw project analysis data.
Used to make the Spec Writer "smarter" about implicit project rules.
"""

from typing import Any


class PatternInferenceEngine:
    """Infers implied patterns from project analysis data."""

    def __init__(self, project_index: dict[str, Any]):
        self.index = project_index
        self.patterns: list[dict[str, str]] = []

    def infer(self) -> list[dict[str, str]]:
        """Run all inference rules and return list of patterns."""
        self.patterns = []

        self._infer_localization()
        self._infer_database_migrations()
        self._infer_strict_typing()
        self._infer_testing_protocol()
        self._infer_frontend_component_structure()

        return self.patterns

    def _infer_localization(self) -> None:
        """Rule: Localization libraries => Enforce translation keys."""
        triggers = []
        is_localized = False

        # Check dependencies in all services
        services = self.index.get("services", {})
        for svc_name, svc_info in services.items():
            deps = svc_info.get("dependencies", [])
            
            # Common i18n libraries
            i18n_libs = ["i18next", "react-intl", "vue-i18n", "gatsby-plugin-i18n", "next-intl", "linguijs"]
            found_libs = [lib for lib in i18n_libs if any(lib in d for d in deps)]
            
            if found_libs:
                is_localized = True
                triggers.append(f"Service '{svc_name}' uses {', '.join(found_libs)}")

            # Check for locales directory in key directories
            key_dirs = svc_info.get("key_directories", {})
            if "locales" in key_dirs or "i18n" in key_dirs:
                 is_localized = True
                 triggers.append(f"Service '{svc_name}' has locales directory")

        if is_localized:
            self.patterns.append({
                "name": "Localization Enforced",
                "description": "Project uses localization. ALL new UI text must use translation keys (e.g., t('key')). Do not hardcode strings.",
                "trigger": "; ".join(triggers)
            })

    def _infer_database_migrations(self) -> None:
        """Rule: ORM/Migration tools => Enforce migration files."""
        triggers = []
        has_migrations = False

        services = self.index.get("services", {})
        for svc_name, svc_info in services.items():
            deps = svc_info.get("dependencies", [])
            
            migration_tools = ["prisma", "typeorm", "sequelize", "alembic", "knex", "django", "flask-migrate"]
            found_tools = [tool for tool in migration_tools if any(tool in d for d in deps)]

            if found_tools:
                has_migrations = True
                triggers.append(f"Service '{svc_name}' uses {', '.join(found_tools)}")

        if has_migrations:
             self.patterns.append({
                "name": "Database Migration Protocol",
                "description": "Database schema changes MUST be accompanied by a migration file. Do not edit schema manually.",
                "trigger": "; ".join(triggers)
            })

    def _infer_strict_typing(self) -> None:
        """Rule: Strict TS config => Enforce no 'any'."""
        conventions = self.index.get("conventions", {})
        if conventions.get("typescript"):
            # We assume if it's TS, we prefer strict. 
            # Ideally we'd parse tsconfig but 'typescript' presence is a strong enough hint for the agent.
            self.patterns.append({
                "name": "Strict Typing",
                "description": "TypeScript project. Use strict typing. Avoid 'any'. Define interfaces for all data structures.",
                "trigger": "TypeScript detected"
            })

    def _infer_testing_protocol(self) -> None:
        """Rule: Test framework present => Enforce unit tests."""
        triggers = []
        has_tests = False
        
        services = self.index.get("services", {})
        for svc_name, svc_info in services.items():
            if svc_info.get("testing") or svc_info.get("e2e_testing"):
                has_tests = True
                frameworks = []
                if svc_info.get("testing"): frameworks.append(svc_info.get("testing"))
                if svc_info.get("e2e_testing"): frameworks.append(svc_info.get("e2e_testing"))
                triggers.append(f"Service '{svc_name}' uses {', '.join(frameworks)}")

        if has_tests:
             self.patterns.append({
                "name": "Testing Protocol",
                "description": "Test verification is active. New logic MUST include unit tests. Update existing tests if logic changes.",
                "trigger": "; ".join(triggers)
            })

    def _infer_frontend_component_structure(self) -> None:
        """Rule: React/Vue => Component reusability."""
        triggers = []
        is_frontend = False

        services = self.index.get("services", {})
        for svc_name, svc_info in services.items():
             deps = svc_info.get("dependencies", [])
             if any("react" in d for d in deps) or any("vue" in d for d in deps):
                 is_frontend = True
                 triggers.append(f"Service '{svc_name}' is a frontend app")

        if is_frontend:
             self.patterns.append({
                "name": "Component Reusability",
                "description": "Frontend framework detected. Break UI into small, reusable components. Use existing UI library components where possible.",
                "trigger": "; ".join(triggers)
            })
