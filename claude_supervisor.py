#!/usr/bin/env python3
"""
Claude Supervisor - Pilnuje i poprawia Cursor AI
Automatyczny nadzorca jakości kodu
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ClaudeSupervisor:
    """
    Claude jako nadzorca Cursor AI
    - Zleca zadania
    - Sprawdza wyniki
    - Poprawia błędy
    - Zapewnia jakość
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.max_iterations = 3  # Max 3 próby poprawek
        
    async def supervise_task(
        self,
        task_description: str,
        acceptance_criteria: List[str],
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Nadzoruje wykonanie zadania przez Cursor AI
        
        Args:
            task_description: Co ma być zrobione
            acceptance_criteria: Lista warunków akceptacji
            context: Dodatkowy kontekst
            
        Returns:
            Raport z wykonania i wszystkich iteracji
        """
        print(f"\n{'='*60}")
        print(f"🎯 CLAUDE SUPERVISOR - Nowe zadanie")
        print(f"{'='*60}\n")
        print(f"📝 Zadanie: {task_description}")
        print(f"✅ Kryteria akceptacji ({len(acceptance_criteria)}):")
        for i, criterion in enumerate(acceptance_criteria, 1):
            print(f"   {i}. {criterion}")
        print()
        
        iterations = []
        current_iteration = 0
        
        while current_iteration < self.max_iterations:
            current_iteration += 1
            
            print(f"\n🔄 ITERACJA {current_iteration}/{self.max_iterations}")
            print("-" * 60)
            
            # Krok 1: Zlecenie zadania Cursorowi
            print(f"\n1️⃣  Claude → Cursor: Zlecam zadanie...")
            cursor_task = await self.delegate_to_cursor(
                task_description,
                context,
                iteration=current_iteration
            )
            
            # Krok 2: Czekanie na wykonanie
            print(f"2️⃣  Oczekiwanie na wykonanie przez Cursor AI...")
            await asyncio.sleep(5)  # Symulacja czasu wykonania
            
            # Krok 3: Sprawdzenie wyniku
            print(f"3️⃣  Claude: Sprawdzam wynik...")
            validation = await self.validate_result(
                self.project_path,
                acceptance_criteria
            )
            
            # Krok 4: Analiza
            iteration_result = {
                "iteration": current_iteration,
                "task": cursor_task,
                "validation": validation,
                "timestamp": datetime.now().isoformat()
            }
            iterations.append(iteration_result)
            
            if validation["passed"]:
                print(f"\n✅ Wszystkie kryteria spełnione!")
                print(f"🎉 Zadanie zakończone pomyślnie w iteracji {current_iteration}")
                
                return {
                    "status": "success",
                    "iterations": iterations,
                    "total_iterations": current_iteration,
                    "final_validation": validation
                }
            else:
                print(f"\n❌ Znaleziono problemy:")
                for issue in validation["issues"]:
                    print(f"   • {issue}")
                
                if current_iteration < self.max_iterations:
                    # Przygotuj poprawki dla następnej iteracji
                    print(f"\n🔧 Przygotowuję poprawki dla Cursor AI...")
                    context = {
                        "previous_attempt": cursor_task,
                        "issues_found": validation["issues"],
                        "iteration": current_iteration
                    }
                    task_description = self.create_correction_task(
                        task_description,
                        validation["issues"]
                    )
                else:
                    print(f"\n⚠️  Osiągnięto maksymalną liczbę iteracji")
        
        return {
            "status": "partial_success",
            "iterations": iterations,
            "total_iterations": current_iteration,
            "final_validation": validation,
            "remaining_issues": validation["issues"]
        }
    
    async def delegate_to_cursor(
        self,
        task: str,
        context: Optional[Dict],
        iteration: int
    ) -> Dict:
        """Zleca zadanie Cursorowi"""
        
        # Tutaj byłaby integracja z orchestratorem
        # execute_cursor_task(...)
        
        task_details = {
            "description": task,
            "context": context,
            "iteration": iteration,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"   📤 Wysłano do Cursor: {task[:60]}...")
        
        return task_details
    
    async def validate_result(
        self,
        project_path: Path,
        criteria: List[str]
    ) -> Dict:
        """
        Sprawdza czy wynik spełnia kryteria
        
        W prawdziwej implementacji:
        - Analizuje utworzone pliki
        - Sprawdza jakość kodu
        - Weryfikuje testy
        - Szuka błędów
        """
        
        print(f"   🔍 Analizuję kod w: {project_path}")
        
        # Symulacja walidacji
        passed_criteria = []
        failed_criteria = []
        issues = []
        
        # Przykładowa walidacja
        for criterion in criteria:
            # W prawdziwej implementacji tutaj byłaby faktyczna analiza
            # np. sprawdzanie czy plik istnieje, czy ma testy, itp.
            
            # Symulacja: pierwsze 2 iteracje mają problemy
            import random
            if random.random() > 0.3:  # 70% szans na sukces
                passed_criteria.append(criterion)
                print(f"      ✅ {criterion}")
            else:
                failed_criteria.append(criterion)
                issues.append(f"Problem z: {criterion}")
                print(f"      ❌ {criterion}")
        
        return {
            "passed": len(failed_criteria) == 0,
            "passed_criteria": passed_criteria,
            "failed_criteria": failed_criteria,
            "issues": issues,
            "score": len(passed_criteria) / len(criteria) * 100
        }
    
    def create_correction_task(
        self,
        original_task: str,
        issues: List[str]
    ) -> str:
        """Tworzy zadanie z poprawkami"""
        
        corrections = "\n".join([f"- {issue}" for issue in issues])
        
        return f"""
{original_task}

⚠️ POPRAWKI DO WPROWADZENIA:
{corrections}

Skoncentruj się na naprawieniu powyższych problemów.
"""

# Przykład użycia
async def example_supervised_task():
    """Przykład nadzorowanego zadania"""
    
    supervisor = ClaudeSupervisor("/Users/mariusz/amgsquant")
    
    result = await supervisor.supervise_task(
        task_description="Stwórz formularz logowania w React z walidacją",
        acceptance_criteria=[
            "Formularz ma pola email i password",
            "Jest walidacja formatu email",
            "Hasło ma minimum 8 znaków",
            "Jest obsługa błędów API",
            "Są testy jednostkowe",
            "Kod jest w TypeScript"
        ]
    )
    
    print(f"\n{'='*60}")
    print(f"📊 RAPORT KOŃCOWY")
    print(f"{'='*60}")
    print(f"Status: {result['status']}")
    print(f"Liczba iteracji: {result['total_iterations']}")
    print(f"Wynik walidacji: {result['final_validation']['score']:.1f}%")
    
    if result['status'] == 'success':
        print(f"\n🎉 SUKCES! Wszystkie kryteria spełnione!")
    else:
        print(f"\n⚠️  CZĘŚCIOWY SUKCES. Pozostałe problemy:")
        for issue in result.get('remaining_issues', []):
            print(f"   • {issue}")

if __name__ == "__main__":
    asyncio.run(example_supervised_task())

