"""AI-powered editorial generation using OpenAI's API."""

import os
from typing import Dict, Any

from openai import OpenAI
from dotenv import load_dotenv

from .logger import logger


class AIGenerator:
    """Generates editorials using OpenAI's API."""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.info(" Using mock editorial generation (no OpenAI API key)")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate_editorial(self, problem_data: Dict[str, Any]) -> str:
        """Generate an editorial for the given problem."""
        # Extract key information
        title = problem_data.get('title', 'Unknown Problem')
        alias = problem_data.get('alias', 'unknown')
        
        logger.info(f" Generating editorial for: {title}")
        
        # Log problem details once
        self._log_problem_details(problem_data)
        
        if self.client is None:
            return self._generate_mock_editorial(title, alias)
        else:
            return self._generate_openai_editorial(problem_data)

    def _log_problem_details(self, problem_data: Dict[str, Any]) -> None:
        """Log problem details once for reference."""
        logger.info("=" * 60)
        logger.info(" PROBLEM DETAILS")
        logger.info("=" * 60)
        
        title = problem_data.get('title', 'Unknown')
        alias = problem_data.get('alias', 'unknown')
        
        logger.info(f"Title: {title}")
        logger.info(f"Alias: {alias}")
        
        # Log statement
        statement = problem_data.get('statement', {})
        markdown = statement.get('markdown', '')
        if markdown:
            logger.info(f"Problem Statement ({len(markdown)} chars):")
            logger.info(markdown)
        
        # Log settings
        settings = problem_data.get('settings', {})
        limits = settings.get('limits', {})
        if limits:
            logger.info(f"Time Limit: {limits.get('TimeLimit', 'Unknown')}")
            logger.info(f"Memory Limit: {limits.get('MemoryLimit', 'Unknown')}")
        
        logger.info("=" * 60)

    def _generate_mock_editorial(self, title: str, alias: str) -> str:
        """Generate a mock editorial for demonstration purposes."""
        editorial = f"""# Editorial: {title}

## Resumen del Problema
Este problema requiere resolver el desafío "{title}" (alias: {alias}).

## Enfoque de Solución
Para resolver este problema, necesitamos:

1. **Analizar la entrada**: Leer y procesar los datos de entrada correctamente
2. **Aplicar el algoritmo**: Implementar la lógica necesaria
3. **Manejar casos especiales**: Considerar casos borde y restricciones
4. **Optimizar si es necesario**: Asegurar que la solución cumple con los límites de tiempo

## Código de Solución

```python
# Solución generada por IA para {alias}
def solve():
    # Leer entrada
    data = input().strip()

    # Procesar datos
    result = process_data(data)

    # Imprimir resultado
    print(result)

def process_data(data):
    # Implementar lógica específica del problema
    # Esta es una solución mock para demostración
    return "Resultado procesado"

if __name__ == "__main__":
    solve()
```

## Complejidad
- **Tiempo**: O(n) donde n es el tamaño de la entrada
- **Espacio**: O(1) espacio adicional

## Notas Importantes
- Este es un editorial generado automáticamente para demostración
- La solución específica depende de los detalles exactos del problema
- Asegúrate de manejar todos los casos de entrada correctamente

*Editorial generado por IA - Versión Demo*
"""
        
        # Log the generated mock editorial
        logger.info(" Mock Editorial Generated:")
        logger.info("=" * 60)
        logger.info(editorial)
        logger.info("=" * 60)
        logger.info(f" Generated mock editorial ({len(editorial)} chars)")
        return editorial

    def _generate_openai_editorial(self, problem_data: Dict[str, Any]) -> str:
        """Generate editorial using OpenAI API."""
        try:
            # Extract problem information
            info = self._extract_problem_info(problem_data)
            
            # Create prompt
            prompt = self._create_prompt(info)
            
            # Log the prompt being sent
            logger.info(" OpenAI Prompt:")
            logger.info("=" * 60)
            logger.info(prompt)
            logger.info("=" * 60)
            
            logger.info(" Generating editorial with OpenAI...")
            
            # Generate editorial
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert programming contest problem solver and editorial writer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            editorial = response.choices[0].message.content.strip()
            
            # Log the generated editorial
            logger.info(" OpenAI Response:")
            logger.info("=" * 60)
            logger.info(editorial)
            logger.info("=" * 60)
            logger.info(f" Generated OpenAI editorial ({len(editorial)} chars)")
            
            return editorial
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            # Fallback to mock editorial
            return self._generate_mock_editorial(
                problem_data.get('title', 'Unknown'),
                problem_data.get('alias', 'unknown')
            )

    def _extract_problem_info(self, problem_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract key information from problem data."""
        statement = problem_data.get('statement', {})
        settings = problem_data.get('settings', {})
        limits = settings.get('limits', {})
        
        return {
            'title': problem_data.get('title', 'Unknown Problem'),
            'alias': problem_data.get('alias', 'unknown'),
            'statement': statement.get('markdown', 'No statement available'),
            'time_limit': limits.get('TimeLimit', 'Unknown'),
            'memory_limit': str(limits.get('MemoryLimit', 'Unknown')),
            'language': statement.get('language', 'es')
        }

    def _create_prompt(self, info: Dict[str, str]) -> str:
        """Create a prompt for editorial generation."""
        return f"""Generate a comprehensive editorial for this programming contest problem:

**Problem Title:** {info['title']}
**Problem Alias:** {info['alias']}
**Time Limit:** {info['time_limit']}
**Memory Limit:** {info['memory_limit']}

**Problem Statement:**
{info['statement']}

Please generate a detailed editorial in Spanish that includes:
1. Problem summary
2. Solution approach/algorithm
3. Implementation details with code
4. Complexity analysis
5. Important notes or edge cases

Format the editorial in markdown with clear sections and include a working code solution."""
