#!/usr/bin/env python3
"""
Auditoria de Technical Debt - Pro Team Care
Identifica código duplicado e complexidade ciclomática
"""

import ast
import hashlib
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TechnicalDebtAuditor:
    """Auditor de dívida técnica"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.python_files: List[Path] = []
        self.complexity_report: Dict[str, Dict] = {}
        self.duplicate_report: Dict[str, Dict] = {}

    def find_python_files(self) -> None:
        """Encontra todos os arquivos Python no projeto"""
        exclude_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "coverage",
            "e2e",
            "venv",
        }

        for root, dirs, files in os.walk(self.project_root):
            # Remove diretórios excluídos
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(".py"):
                    self.python_files.append(Path(root) / file)

    def analyze_complexity(self) -> None:
        """Analisa complexidade ciclomática dos arquivos"""
        try:
            from radon.complexity import cc_visit
        except ImportError:
            print("❌ radon não instalado. Instale com: pip install radon")
            return

        for file_path in self.python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Analisar complexidade
                results = cc_visit(content)

                file_complexity = {
                    "file": str(file_path.relative_to(self.project_root)),
                    "functions": [],
                    "total_complexity": 0,
                    "high_complexity_count": 0,
                }

                for result in results:
                    complexity = result.complexity
                    file_complexity["functions"].append(
                        {
                            "name": result.name,
                            "complexity": complexity,
                            "line": result.lineno,
                            "type": getattr(
                                result, "type", "unknown"
                            ),  # Handle missing type attribute
                        }
                    )

                    file_complexity["total_complexity"] += complexity
                    if complexity > 10:  # Threshold para alta complexidade
                        file_complexity["high_complexity_count"] += 1

                if file_complexity["functions"]:
                    self.complexity_report[str(file_path)] = file_complexity

            except Exception as e:
                print(f"⚠️  Erro ao analisar {file_path}: {e}")

    def analyze_duplicates(self) -> None:
        """Analisa código duplicado"""
        # Coletar todas as linhas de código
        code_lines: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

        for file_path in self.python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    # Remover comentários e espaços
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith("#"):
                        # Remover strings e números para foco em estrutura
                        clean_line = re.sub(r'["\'].*?["\']', "STR", clean_line)
                        clean_line = re.sub(r"\d+", "NUM", clean_line)
                        code_lines[clean_line].append(
                            (str(file_path.relative_to(self.project_root)), i)
                        )

            except Exception as e:
                print(f"⚠️  Erro ao processar {file_path}: {e}")

        # Encontrar duplicatas (linhas que aparecem em múltiplos arquivos)
        duplicates = {}
        for line, locations in code_lines.items():
            if len(locations) > 1 and len(line) > 20:  # Ignorar linhas muito curtas
                # Agrupar por arquivo
                files_count = Counter(loc[0] for loc in locations)
                if len(files_count) > 1:  # Aparece em múltiplos arquivos
                    key = hashlib.md5(line.encode()).hexdigest()[:8]
                    if key not in duplicates:
                        duplicates[key] = {
                            "line": line[:100] + "..." if len(line) > 100 else line,
                            "occurrences": len(locations),
                            "files": list(files_count.keys())[:5],  # Top 5 arquivos
                            "locations": locations[:10],  # Top 10 ocorrências
                        }

        self.duplicate_report = duplicates

    def analyze_code_duplication_within_files(self) -> Dict[str, List[Dict]]:
        """Analisa duplicação dentro do mesmo arquivo"""
        internal_duplicates = {}

        for file_path in self.python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Dividir em blocos de código (funções, classes)
                tree = ast.parse(content)
                blocks = []

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        # Extrair código do bloco
                        start_line = node.lineno - 1
                        end_line = getattr(node, "end_lineno", start_line + 10)
                        block_lines = content.split("\n")[start_line:end_line]
                        block_code = "\n".join(block_lines)

                        if len(block_code) > 100:  # Blocos significativos
                            blocks.append(
                                {
                                    "name": node.name,
                                    "code": block_code,
                                    "start_line": start_line + 1,
                                    "hash": hashlib.md5(
                                        block_code.encode()
                                    ).hexdigest(),
                                }
                            )

                # Encontrar duplicatas dentro do arquivo
                hash_groups = defaultdict(list)
                for block in blocks:
                    hash_groups[block["hash"]].append(block)

                duplicates_in_file = []
                for hash_val, group in hash_groups.items():
                    if len(group) > 1:
                        duplicates_in_file.append(
                            {"hash": hash_val, "blocks": group, "count": len(group)}
                        )

                if duplicates_in_file:
                    internal_duplicates[
                        str(file_path.relative_to(self.project_root))
                    ] = duplicates_in_file

            except Exception as e:
                print(f"⚠️  Erro ao analisar duplicatas em {file_path}: {e}")

        return internal_duplicates

    def generate_report(self) -> str:
        """Gera relatório completo"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE DÍVIDA TÉCNICA - PRO TEAM CARE")
        report.append("=" * 80)
        report.append("")

        # Inicializar variáveis
        total_functions = 0
        total_complexity = 0
        high_complexity_functions = 0

        # Estatísticas gerais
        report.append("📊 ESTATÍSTICAS GERAIS")
        report.append("-" * 40)
        report.append(f"Arquivos Python analisados: {len(self.python_files)}")
        report.append(
            f"Arquivos com análise de complexidade: {len(self.complexity_report)}"
        )
        report.append(
            f"Duplicatas entre arquivos encontradas: {len(self.duplicate_report)}"
        )
        report.append("")

        # Análise de complexidade
        if self.complexity_report:
            report.append("🧠 ANÁLISE DE COMPLEXIDADE")
            report.append("-" * 40)

            for file_path, data in self.complexity_report.items():
                report.append(f"📁 {data['file']}")
                report.append(f"  Funções: {len(data['functions'])}")
                report.append(f"  Complexidade total: {data['total_complexity']}")
                report.append(
                    f"  Funções de alta complexidade (>10): {data['high_complexity_count']}"
                )

                total_functions += len(data["functions"])
                high_complexity_functions += data["high_complexity_count"]
                total_complexity += data["total_complexity"]

                # Listar funções de alta complexidade
                high_complexity = [f for f in data["functions"] if f["complexity"] > 10]
                if high_complexity:
                    report.append("  🔴 Funções críticas:")
                    for func in high_complexity[:5]:  # Top 5
                        report.append(
                            f"    - {func['name']} (complexidade: {func['complexity']}, linha: {func['line']})"
                        )
                report.append("")

            report.append("📈 RESUMO GERAL DE COMPLEXIDADE")
            report.append(f"Total de funções analisadas: {total_functions}")
            report.append(f"Funções de alta complexidade: {high_complexity_functions}")
            report.append(
                f"Complexidade média por função: {total_complexity / total_functions:.1f}"
                if total_functions > 0
                else "N/A"
            )
            report.append("")
        else:
            report.append(
                "⚠️  Análise de complexidade não disponível (radon não instalado)"
            )
            report.append("")

        # Análise de duplicatas entre arquivos
        if self.duplicate_report:
            report.append("📋 DUPLICATAS ENTRE ARQUIVOS")
            report.append("-" * 40)

            for key, data in list(self.duplicate_report.items())[:20]:  # Top 20
                report.append(
                    f"🔄 Linha duplicada ({data['occurrences']} ocorrências):"
                )
                report.append(f"  📝 {data['line']}")
                report.append(f"  📁 Arquivos: {', '.join(data['files'])}")
                report.append("")

            report.append(
                f"📊 Total de duplicatas encontradas: {len(self.duplicate_report)}"
            )
            report.append("")
        else:
            report.append(
                "✅ Nenhuma duplicata significativa encontrada entre arquivos"
            )
            report.append("")

        # Análise de duplicatas dentro de arquivos
        internal_duplicates = self.analyze_code_duplication_within_files()
        if internal_duplicates:
            report.append("🔄 DUPLICATAS DENTRO DE ARQUIVOS")
            report.append("-" * 40)

            for file_name, duplicates in internal_duplicates.items():
                report.append(f"📁 {file_name}")
                for dup in duplicates[:3]:  # Top 3 por arquivo
                    report.append(f"  🔄 {dup['count']} blocos duplicados:")
                    for block in dup["blocks"][:2]:  # Mostrar 2 exemplos
                        report.append(
                            f"    - {block['name']} (linha {block['start_line']})"
                        )
                report.append("")

        # Recomendações
        report.append("💡 RECOMENDAÇÕES PARA REDUÇÃO DE DÍVIDA TÉCNICA")
        report.append("-" * 40)

        recommendations = []

        if high_complexity_functions > 0:
            recommendations.append("🔴 REFACTORING CRÍTICO:")
            recommendations.append(
                "   - Quebrar funções com complexidade > 10 em funções menores"
            )
            recommendations.append(
                "   - Aplicar padrão Strategy para lógica condicional complexa"
            )
            recommendations.append(
                "   - Extrair métodos privados para reduzir complexidade"
            )

        if self.duplicate_report:
            recommendations.append("🟡 ELIMINAÇÃO DE DUPLICATAS:")
            recommendations.append("   - Criar funções utilitárias para código comum")
            recommendations.append("   - Implementar padrão Template Method")
            recommendations.append(
                "   - Usar herança ou composição para evitar duplicação"
            )

        if not recommendations:
            recommendations.append("✅ Código bem estruturado - manter boas práticas")

        report.extend(recommendations)
        report.append("")

        # Próximos passos
        report.append("🚀 PRÓXIMOS PASSOS")
        report.append("-" * 40)
        report.append("1. Instalar radon: pip install radon")
        report.append(
            "2. Executar análise completa: python scripts/audit_technical_debt.py"
        )
        report.append("3. Priorizar refactoring das funções mais complexas")
        report.append("4. Implementar testes antes de refatorar")
        report.append("5. Revisar código duplicado e extrair abstrações")
        report.append("")

        from datetime import datetime

        report.append(
            f"📅 Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Função principal"""
    project_root = "/home/juliano/Projetos/pro_team_care_16"

    auditor = TechnicalDebtAuditor(project_root)
    auditor.find_python_files()

    print(f"🔍 Analisando {len(auditor.python_files)} arquivos Python...")

    auditor.analyze_complexity()
    auditor.analyze_duplicates()

    report = auditor.generate_report()
    print(report)

    # Salvar relatório
    report_file = f"{project_root}/technical_debt_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Relatório salvo em: {report_file}")


if __name__ == "__main__":
    main()
