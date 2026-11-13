# 🚀 Agent_Banca - Frontend Moderno & API Gateway

Este directorio y la nueva arquitectura implementan la **Opción A** del Plan de Modernización UX/UI de Agent_Banca.

---

## 🏛 Arquitectura
- **Frontend SPA**: React 19 + TypeScript + Vite + Tailwind CSS v4 + Lucide Icons.
- **Backend API Gateway**: FastAPI (`src/api_server.py`) con endpoints REST y generación de PDFs.
- **Motor Financiero**: Ingesta de 3 fuentes, reconciliación determinista de Pandas y cribado AML.

---

## ⚡ Cómo Ejecutar la Aplicación

### Paso 1: Iniciar el Backend API (FastAPI)
En una terminal:
```powershell
python -m uvicorn src.api_server:app --host 127.0.0.1 --port 8000 --reload
```
Documentación interactiva disponible en: `http://127.0.0.1:8000/docs`

### Paso 2: Iniciar el Frontend (Vite)
En una segunda terminal:
```powershell
cd frontend
npm run dev
```
Abre tu navegador en: `http://localhost:5173`

---

## 💎 Características de UX/UI FinTech Implementadas
1. **Dropzone Inteligente 3-en-1**: Ingesta visual simultánea para extractos de Banco, Pasarela y Libro Mayor con detección de estados y tamaño.
2. **Botón de Muestras PoC en 1-Clic**: Permite ejecutar la conciliación instantáneamente con los fixtures del repositorio sin tener que buscar archivos manualmente.
3. **KPI Cards con Tokens Semánticos**: Métricas de Coincidencias Exactas, Tarifas (Fuzzy Fee), Excepciones, Huérfanas y Alertas AML.
4. **Data Grid Financiero**: Búsqueda en tiempo real por ID de payout o descripción, filtros por severidad y categorías.
5. **Drawer Lateral de Auditoría (Slide-over)**: Inspección granular de cada transacción, reglas aplicadas y visualizador JSON con copia rápida.
6. **Copilot FinTech Studio**: Asistente con prompts sugeridos, skills de `Conciliación & Auditoría`, `Fuentes y formatos`, `Excepciones y evidencia` y `Reportes y trazabilidad`, además de soporte para adjuntar archivos. La guía de UI/UX se conserva para desarrollo, pero no se ofrece como skill del chat.
7. **Exportación Ejecutiva**: Descarga directa de informes explicados en formato PDF y exportación técnica en JSON.
8. **Modo Claro / Oscuro (Dark Mode)**: Diseñado según estándares WCAG 2.1 AA con números tabulares (`tabular-nums`) para evitar descuadres en balances financieros.

