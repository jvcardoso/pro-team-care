"""
Testes de Arquitetura - Verificação da Clean Architecture
Garantem que as regras de dependência sejam respeitadas
"""

import ast
import glob
import os
from pathlib import Path

import pytest


class DependencyChecker:
    """Analisador de dependências entre camadas"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_path = self.project_root / "app"

    def get_imports(self, file_path: Path) -> list:
        """Extrai imports de um arquivo Python"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            return imports
        except Exception:
            return []

    def get_layer_files(self, layer: str) -> list:
        """Obtém todos os arquivos Python de uma camada"""
        layer_path = self.app_path / layer
        if not layer_path.exists():
            return []

        pattern = str(layer_path / "**" / "*.py")
        return [Path(f) for f in glob.glob(pattern, recursive=True)]

    def check_layer_dependencies(
        self, source_layer: str, forbidden_layers: list
    ) -> list:
        """Verifica se uma camada não depende de camadas proibidas"""
        violations = []
        source_files = self.get_layer_files(source_layer)

        for file_path in source_files:
            imports = self.get_imports(file_path)

            for imp in imports:
                for forbidden_layer in forbidden_layers:
                    forbidden_pattern = f"app.{forbidden_layer}"
                    if forbidden_pattern in imp:
                        violations.append(
                            {
                                "file": str(file_path.relative_to(self.project_root)),
                                "import": imp,
                                "violates_rule": f"{source_layer} -> {forbidden_layer}",
                            }
                        )

        return violations


@pytest.fixture
def dependency_checker():
    """Fixture para o analisador de dependências"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return DependencyChecker(project_root)


class TestCleanArchitectureRules:
    """Testes das regras da Clean Architecture"""

    def test_domain_layer_purity(self, dependency_checker):
        """
        REGRA: Domain Layer não pode depender de nenhuma outra camada
        Domain deve ser puro - sem dependências externas
        """
        violations = dependency_checker.check_layer_dependencies(
            source_layer="domain",
            forbidden_layers=["infrastructure", "presentation", "application"],
        )

        assert violations == [], (
            f"❌ DOMAIN LAYER VIOLATION: Domain não pode depender de outras camadas.\n"
            f"Violações encontradas: {violations}"
        )

    def test_application_layer_dependencies(self, dependency_checker):
        """
        REGRA: Application Layer só pode depender de Domain
        Application não pode depender de Infrastructure ou Presentation
        """
        violations = dependency_checker.check_layer_dependencies(
            source_layer="application",
            forbidden_layers=["infrastructure", "presentation"],
        )

        assert violations == [], (
            f"❌ APPLICATION LAYER VIOLATION: Application só pode depender de Domain.\n"
            f"Violações encontradas: {violations}"
        )

    def test_no_framework_dependencies_in_domain(self, dependency_checker):
        """
        REGRA: Domain não pode ter dependências de frameworks
        Pydantic, SQLAlchemy, FastAPI, etc. são proibidos no Domain
        """
        domain_files = dependency_checker.get_layer_files("domain")
        forbidden_frameworks = [
            "pydantic",
            "sqlalchemy",
            "fastapi",
            "starlette",
            "flask",
            "django",
            "celery",
            "redis",
        ]

        violations = []
        for file_path in domain_files:
            imports = dependency_checker.get_imports(file_path)

            for imp in imports:
                for framework in forbidden_frameworks:
                    if framework in imp.lower():
                        violations.append(
                            {
                                "file": str(
                                    file_path.relative_to(
                                        dependency_checker.project_root
                                    )
                                ),
                                "import": imp,
                                "framework": framework,
                            }
                        )

        assert violations == [], (
            f"❌ FRAMEWORK DEPENDENCY VIOLATION: Domain deve ser livre de frameworks.\n"
            f"Violações encontradas: {violations}"
        )

    def test_infrastructure_can_depend_on_domain_and_application(
        self, dependency_checker
    ):
        """
        REGRA: Infrastructure pode depender de Domain e Application
        Mas não pode depender de Presentation
        """
        violations = dependency_checker.check_layer_dependencies(
            source_layer="infrastructure", forbidden_layers=["presentation"]
        )

        # Filtrar apenas violações reais (não testes ou utilitários)
        real_violations = [
            v
            for v in violations
            if not any(
                ignore in v["file"] for ignore in ["test_", "__pycache__", ".pyc"]
            )
        ]

        assert real_violations == [], (
            f"❌ INFRASTRUCTURE LAYER VIOLATION: Infrastructure não pode depender de Presentation.\n"
            f"Violações encontradas: {real_violations}"
        )

    def test_sqlalchemy_models_in_correct_location(self, dependency_checker):
        """
        REGRA: Modelos SQLAlchemy devem estar em infrastructure/orm
        """
        project_files = []
        for pattern in ["**/*.py"]:
            project_files.extend(
                glob.glob(str(dependency_checker.app_path / pattern), recursive=True)
            )

        sqlalchemy_imports = []
        for file_path in project_files:
            path_obj = Path(file_path)
            imports = dependency_checker.get_imports(path_obj)

            for imp in imports:
                if "declarative_base" in imp or "DeclarativeBase" in imp:
                    # Verificar se não está no local correto
                    if "infrastructure/orm" not in str(path_obj):
                        sqlalchemy_imports.append(
                            {
                                "file": str(
                                    path_obj.relative_to(
                                        dependency_checker.project_root
                                    )
                                ),
                                "import": imp,
                            }
                        )

        assert sqlalchemy_imports == [], (
            f"❌ SQLALCHEMY MODELS LOCATION: Modelos SQLAlchemy devem estar em infrastructure/orm/.\n"
            f"Arquivos incorretos: {sqlalchemy_imports}"
        )

    def test_entities_are_dataclasses(self, dependency_checker):
        """
        REGRA: Entidades de domínio devem usar dataclasses, não Pydantic
        """
        domain_entity_files = glob.glob(
            str(dependency_checker.app_path / "domain" / "entities" / "*.py"),
            recursive=True,
        )

        pydantic_violations = []
        for file_path in domain_entity_files:
            if file_path.endswith("__init__.py"):
                continue

            path_obj = Path(file_path)
            imports = dependency_checker.get_imports(path_obj)

            for imp in imports:
                if "pydantic" in imp.lower():
                    pydantic_violations.append(
                        {
                            "file": str(
                                path_obj.relative_to(dependency_checker.project_root)
                            ),
                            "import": imp,
                        }
                    )

        assert pydantic_violations == [], (
            f"❌ DOMAIN ENTITIES PURITY: Entidades de domínio devem usar dataclasses, não Pydantic.\n"
            f"Violações encontradas: {pydantic_violations}"
        )


class TestLayerStructure:
    """Testes da estrutura das camadas"""

    def test_required_directories_exist(self, dependency_checker):
        """
        REGRA: Estrutura de diretórios da Clean Architecture deve existir
        """
        required_dirs = [
            "domain/entities",
            "application/use_cases",
            "application/interfaces",
            "infrastructure/repositories",
            "infrastructure/orm",
            "presentation/api",
            "presentation/schemas",
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            full_path = dependency_checker.app_path / dir_path
            if not full_path.exists():
                missing_dirs.append(str(full_path))

        assert missing_dirs == [], (
            f"❌ DIRECTORY STRUCTURE: Diretórios obrigatórios não encontrados.\n"
            f"Faltando: {missing_dirs}"
        )

    def test_interfaces_are_abstract(self, dependency_checker):
        """
        REGRA: Interfaces devem ser classes abstratas (ABC)
        """
        interface_files = glob.glob(
            str(dependency_checker.app_path / "application" / "interfaces" / "*.py"),
            recursive=True,
        )

        non_abstract_interfaces = []
        for file_path in interface_files:
            if file_path.endswith("__init__.py"):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Verificar se contém ABC e @abstractmethod
                if "class" in content and "Interface" in content:
                    if "ABC" not in content or "@abstractmethod" not in content:
                        non_abstract_interfaces.append(file_path)
            except Exception:
                continue

        assert non_abstract_interfaces == [], (
            f"❌ INTERFACE ABSTRACTION: Interfaces devem herdar de ABC e usar @abstractmethod.\n"
            f"Interfaces não abstratas: {non_abstract_interfaces}"
        )


if __name__ == "__main__":
    # Para executar diretamente
    pytest.main([__file__, "-v"])
