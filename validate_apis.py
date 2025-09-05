#!/usr/bin/env python3
"""
Script de validação das APIs do Pro Team Care
Verifica duplicatas por nome de rota e funcionalidade
"""

import os
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class APIEndpoint:
    """Representa um endpoint de API"""
    file: str
    method: str
    path: str
    summary: str
    description: str
    line_number: int

class APIValidator:
    """Validador de APIs"""

    def __init__(self, api_dir: str):
        self.api_dir = Path(api_dir)
        self.endpoints: List[APIEndpoint] = []

    def extract_endpoints(self) -> None:
        """Extrai todos os endpoints dos arquivos de API"""
        for py_file in self.api_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text(encoding='utf-8')
            self._parse_file(py_file.name, content)

    def _parse_file(self, filename: str, content: str) -> None:
        """Parse um arquivo de API para extrair endpoints"""
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Procurar por decoradores @router
            if line.strip().startswith('@router.'):
                # Capturar método e path, mesmo com quebras de linha
                method_match = re.match(r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line)
                if method_match:
                    method = method_match.group(1).upper()
                    path = method_match.group(2)
                else:
                    # Verificar se continua na próxima linha
                    full_line = line.strip()
                    j = i + 1
                    while j < len(lines) and not full_line.endswith(')'):
                        full_line += ' ' + lines[j].strip()
                        j += 1

                    method_match = re.search(r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', full_line)
                    if method_match:
                        method = method_match.group(1).upper()
                        path = method_match.group(2)
                    else:
                        i = j
                        continue

                # Procurar summary e description nas próximas linhas
                summary = ""
                description = ""

                # Procurar summary
                for j in range(i+1, min(i+30, len(lines))):
                    if 'summary=' in lines[j]:
                        summary_match = re.search(r'summary\s*=\s*["\']([^"\']+)["\']', lines[j])
                        if summary_match:
                            summary = summary_match.group(1)
                            break
                    elif 'summary=' in lines[j] and j+1 < len(lines):
                        # Summary pode estar na próxima linha
                        next_line = lines[j+1].strip()
                        if next_line.startswith('"') or next_line.startswith("'"):
                            summary_match = re.match(r'["\']([^"\']+)["\']', next_line)
                            if summary_match:
                                summary = summary_match.group(1)
                                break

                # Procurar description
                for j in range(i+1, min(i+50, len(lines))):
                    if 'description=' in lines[j]:
                        desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', lines[j])
                        if desc_match:
                            description = desc_match.group(1)
                            break
                    elif 'description=' in lines[j] and j+1 < len(lines):
                        # Description pode estar na próxima linha
                        next_line = lines[j+1].strip()
                        if next_line.startswith('"') or next_line.startswith("'"):
                            desc_match = re.match(r'["\']([^"\']+)["\']', next_line)
                            if desc_match:
                                description = desc_match.group(1)
                                break

                endpoint = APIEndpoint(
                    file=filename,
                    method=method,
                    path=path,
                    summary=summary,
                    description=description,
                    line_number=i+1
                )

                self.endpoints.append(endpoint)

            i += 1

    def find_duplicate_paths(self) -> Dict[str, List[APIEndpoint]]:
        """Encontra rotas duplicadas (mesmo método + path)"""
        route_groups: Dict[str, List[APIEndpoint]] = {}

        for endpoint in self.endpoints:
            # Chave é método + path
            route_key = f"{endpoint.method} {endpoint.path}"
            if route_key not in route_groups:
                route_groups[route_key] = []
            route_groups[route_key].append(endpoint)

        # Retornar apenas os duplicados
        return {route: endpoints for route, endpoints in route_groups.items() if len(endpoints) > 1}

    def find_similar_functionality(self) -> Dict[str, List[APIEndpoint]]:
        """Encontra endpoints com funcionalidades similares"""
        functionality_groups: Dict[str, List[APIEndpoint]] = {}

        for endpoint in self.endpoints:
            # Criar chave baseada em palavras-chave da funcionalidade
            summary_lower = endpoint.summary.lower()
            desc_lower = endpoint.description.lower()

            # Extrair palavras-chave
            keywords = []
            if 'cnpj' in summary_lower or 'cnpj' in desc_lower:
                keywords.append('cnpj')
            if 'empresa' in summary_lower or 'company' in desc_lower:
                keywords.append('empresa')
            if 'health' in summary_lower or 'saude' in desc_lower:
                keywords.append('health')
            if 'login' in summary_lower or 'autentic' in desc_lower:
                keywords.append('auth')
            if 'menu' in summary_lower or 'menu' in desc_lower:
                keywords.append('menu')
            if 'metric' in summary_lower or 'monitor' in desc_lower:
                keywords.append('metrics')
            if 'geocode' in summary_lower or 'geolocal' in desc_lower:
                keywords.append('geocoding')

            if keywords:
                key = '|'.join(sorted(keywords))
            else:
                key = f"{endpoint.summary.lower()}|{endpoint.description.lower()[:50]}"

            if key not in functionality_groups:
                functionality_groups[key] = []
            functionality_groups[key].append(endpoint)

        # Retornar apenas grupos com múltiplos endpoints
        return {key: endpoints for key, endpoints in functionality_groups.items() if len(endpoints) > 1}

    def generate_report(self) -> str:
        """Gera relatório completo de validação"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE VALIDAÇÃO DAS APIS - PRO TEAM CARE")
        report.append("=" * 80)
        report.append("")

        # Estatísticas gerais
        report.append("📊 ESTATÍSTICAS GERAIS")
        report.append("-" * 40)
        report.append(f"Total de endpoints encontrados: {len(self.endpoints)}")
        report.append(f"Arquivos de API analisados: {len(set(ep.file for ep in self.endpoints))}")
        report.append("")

        # Lista completa de endpoints
        report.append("📋 LISTA COMPLETA DE ENDPOINTS")
        report.append("-" * 40)

        for endpoint in sorted(self.endpoints, key=lambda x: (x.file, x.path)):
            report.append(f"📁 {endpoint.file}")
            report.append(f"  {endpoint.method} {endpoint.path}")
            if endpoint.summary:
                report.append(f"  📝 {endpoint.summary}")
            if endpoint.description:
                report.append(f"  📖 {endpoint.description[:100]}{'...' if len(endpoint.description) > 100 else ''}")
            report.append("")

        # Verificar duplicatas por rota
        duplicate_paths = self.find_duplicate_paths()
        if duplicate_paths:
            report.append("🚨 DUPLICATAS POR ROTA (CRÍTICO)")
            report.append("-" * 40)
            for path, endpoints in duplicate_paths.items():
                report.append(f"🔴 Rota duplicada: {path}")
                for endpoint in endpoints:
                    report.append(f"  📁 {endpoint.file}:{endpoint.line_number}")
                    report.append(f"  {endpoint.method} - {endpoint.summary}")
                report.append("")
        else:
            report.append("✅ NENHUMA DUPLICATA POR ROTA ENCONTRADA")
            report.append("")

        # Verificar funcionalidades similares
        similar_functionality = self.find_similar_functionality()
        if similar_functionality:
            report.append("⚠️  FUNCIONALIDADES SIMILARES (ATENÇÃO)")
            report.append("-" * 40)
            for key, endpoints in similar_functionality.items():
                summary = key.split('|')[0]
                report.append(f"🟡 Funcionalidade similar: {summary}")
                for endpoint in endpoints:
                    report.append(f"  📁 {endpoint.file}:{endpoint.line_number}")
                    report.append(f"  {endpoint.method} {endpoint.path}")
                report.append("")
        else:
            report.append("✅ NENHUMA FUNCIONALIDADE SIMILAR ENCONTRADA")
            report.append("")

        # Recomendações
        report.append("💡 RECOMENDAÇÕES")
        report.append("-" * 40)

        if duplicate_paths:
            report.append("🚨 CRÍTICO: Remover ou renomear rotas duplicadas imediatamente")
            report.append("   - Duplicatas podem causar conflitos de roteamento")
            report.append("   - Escolher uma implementação principal")
            report.append("   - Documentar justificativa para manter múltiplas")
        else:
            report.append("✅ Estrutura de rotas está limpa")

        if similar_functionality:
            report.append("⚠️  ATENÇÃO: Revisar funcionalidades similares")
            report.append("   - Verificar se são realmente necessárias")
            report.append("   - Considerar unificar em um endpoint único")
            report.append("   - Melhorar documentação para diferenciar")
        else:
            report.append("✅ Funcionalidades estão bem diferenciadas")

        report.append("")
        report.append("📅 Data da análise: " + str(__import__('datetime').datetime.now()))
        report.append("=" * 80)

        return "\n".join(report)

def main():
    """Função principal"""
    api_dir = "/home/juliano/Projetos/pro_team_care_16/app/presentation/api/v1"

    if not os.path.exists(api_dir):
        print(f"❌ Diretório não encontrado: {api_dir}")
        return

    validator = APIValidator(api_dir)
    validator.extract_endpoints()

    report = validator.generate_report()
    print(report)

    # Salvar relatório em arquivo
    report_file = "/home/juliano/Projetos/pro_team_care_16/api_validation_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📄 Relatório salvo em: {report_file}")

if __name__ == "__main__":
    main()