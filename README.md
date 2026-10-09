# ORION — Observatorio Inteligente de Oportunidades

MVP de investigación, registro de evidencias y simulación PAPER. **No opera dinero real** y no promete rentabilidad.

## Requisitos
- Python 3.10 o posterior
- Conexión a Internet para consultar fuentes públicas
- Dependencia: `requests`

## Instalación y ejecución
```bash
python -m pip install -r requirements.txt
python main.py
python main.py --research
```

## Persistencia
Por defecto el historial se guarda en `data/orion_history.json`. Para elegir otra carpeta, configure `ORION_DATA_DIR`.
El archivo debe estar en un almacenamiento persistente del entorno donde se ejecute el programa. Un archivo dentro de un contenedor efímero puede perderse al reiniciarlo.

## Investigación
La opción `--research` consulta precios públicos de CoinGecko y Binance. Son referencias informativas, no garantía de que los precios sean ejecutables ni de que haya una oportunidad rentable. Si una fuente falla, ORION registra una advertencia.

## Simulación PAPER y comisiones
La función `record_paper_trade()` admite `fee_rate`; por defecto usa 0,6% por operación como supuesto configurable, **no como afirmación sobre la tarifa vigente de Lemon**. Antes de comparar resultados, confirmar la tarifa aplicable, spread y cualquier otro costo. Las compras y ventas se simulan; no se conecta a una cuenta ni ejecuta órdenes reales.

## Limitaciones del MVP
- No es un agente autónomo continuo ni un modelo que se entrena solo.
- La investigación se inicia manualmente con `--research`.
- Las hipótesis deben validarse explícitamente; el programa no inventa resultados.
- Para una valoración completa de la cartera hay que proporcionar precios para todas las posiciones.
- No incluir claves privadas, contraseñas ni tokens en el repositorio.

## Seguridad y pruebas
Haga una copia del historial antes de cambios importantes. No use dinero real con este MVP. Pruebe primero con operaciones PAPER pequeñas y revise los registros.
