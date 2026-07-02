# AIL — Manual del Paradigma
## Parte 5: Referencia Rápida

---

> Esta sección es el manual condensado. Una IA puede cargar solo esta página para operar bajo el paradigma en situaciones simples. Para trabajo complejo, cargar la parte relevante de las partes 1–4.

---

## El paradigma en una oración

Software es un grafo semántico tipado. Los nodos son unidades de significado. Los edges son relaciones tipadas. El texto fuente es un artefacto de salida, nunca la fuente de verdad.

---

## Los 7 tipos de nodo

| Tipo | Qué contiene | Reemplaza |
|---|---|---|
| `computation` | IR ejecutable + firma tipada | función, método, handler |
| `data` | campos tipados, sin métodos | class/struct/DTO/entity |
| `constraint` | regla de negocio verificable | comentario, aserción, validación embebida |
| `event` | ocurrencia tipada con payload | exception, domain event, mensaje |
| `test` | triplete dado/espera | unit/integration test |
| `boundary` | punto de entrada/salida externo | endpoint, API, puerto |
| `ontology` | concepto del dominio definido | documentación, término DDD |

---

## Los 11 tipos de edge

| Edge | Significa |
|---|---|
| `depends-on` A→B | A necesita B para ejecutar |
| `composed-of` A→B | A tiene un campo de tipo B |
| `constrained-by` A→B | B es una regla que A debe cumplir |
| `tests` A→B | A verifica el comportamiento de B |
| `produces` A→B | A emite eventos del tipo B |
| `consumes` A→B | A procesa eventos del tipo B |
| `dispatches-to` A→B | A puede resolverse como B (polimorfismo) |
| `boundary-exposes` A→B | A expone B externamente |
| `derives-from` A→B | A es versión modificada de B |
| `belongs-to` A→B | A pertenece al dominio/partición B |
| `compensates` A→B | A es la computación compensatoria de B (sagas, spec/07) |

---

## Las reglas en una página

### Identidad (dos niveles)
- semantic_id = sha256(tipo + firma canónica) — estable mientras el contrato no cambie
- version_hash = sha256(semantic_id + IR_hash + pins de dependencias) — nuevo en cada cambio de conducta
- Los edges referencian semantic_id (pin de versión opcional)
- Nombres son aliases en metadata, nunca identidad
- Renombrar = actualizar metadata, sin cambio de ID
- Cambiar conducta = nueva versión, mismo semantic_id — dependientes no se tocan
- Cambiar firma = nuevo semantic_id — breaking change, dependientes deben re-apuntar

### Representación
- Cada artefacto mapea a exactamente un tipo de nodo
- Comportamiento vive en IR binario, nunca en texto fuente
- Reglas de negocio son nodos constraint, nunca comentarios
- Concerns transversales son edges constrained-by, nunca código embebido
- Todas las relaciones son edges explícitos

### Contexto
- Edición local = nodo objetivo + depth-1 neighbors + constraints + tests
- Máximo depth-2. Nunca más.
- Nodos ontology y constraint: anclados al inicio de sesión
- Expandir contexto solo cuando falla compatibilidad de tipos
- Buscar semánticamente antes de expandir

### Cambio
- Los nodos son inmutables — se crean versiones nuevas
- Snapshot siempre antes de modificar
- Dependientes actualizan explícitamente (adoptar / mantener / incompatible)
- Refactor = operación de grafo, nunca búsqueda de texto
- Eliminar = redirigir edges, no acción directa

### Conocimiento
- Una regla = un nodo constraint (sin duplicados)
- Orden: ontology → constraint → data → computation → test → boundary
- Constraint verificable siempre tiene nodo de verificación

### Corrección
- Todo nodo computation tiene ≥1 nodo test
- Tests son datos (dado / espera), no código
- Cobertura mínima para deployment: 80%
- Tipos = compatibilidad de edges, no comparación de texto
- Errores = nodos event con edges produces/consumes

### Runtime (spec/07)
- Efectos ordenados (`seq`); emisión de eventos siempre última dentro de un scope transaccional
- Scopes atómicos nunca cruzan particiones; workflows cross-partición son sagas con edges `compensates`
- Entrega `at-least-once` exige consumidor idempotente — verificado estructuralmente
- Política de retry y dead-letter viven en el edge `consumes`, no en código

### Tiempo
- Unidad de versión = snapshot
- Sin diffs de texto — solo diffs semánticos
- Rollback = restaurar snapshot
- Historial de nodo = cadena de edges derives-from

---

## Orden de trabajo (siempre)

```
1. Ontology    (conceptos del dominio)
2. Constraint  (reglas de negocio)
3. Data        (estructuras)
4. Computation (comportamiento)
5. Test        (verificación)
6. Boundary    (exposición externa)
7. Snapshot    (validar)
8. Compilar    (solo si snapshot es valid)
```

---

## Protocolo de edición (siempre)

```
1. Identificar nodo objetivo (hash directo o búsqueda semántica)
2. Cargar contexto mínimo (nodo + depth-1 + constraints + tests)
3. Verificar constraints antes de modificar
4. Crear snapshot
5. Crear nuevo nodo con conducta modificada
6. Actualizar/crear test nodes
7. Actualizar edges de dependientes
8. Validar snapshot
```

---

## Lo que no existe en este paradigma

```
✗ Archivos de código fuente como unidad primaria
✗ Carpetas y estructura de directorios
✗ Clases y herencia
✗ Interfaces como artefactos de texto separados
✗ Comentarios explicativos
✗ Documentación mantenida manualmente
✗ Imports / require / use statements
✗ Try/catch embebido en lógica de computación
✗ Getters, setters, constructores
✗ Validación embebida en funciones de negocio
✗ Búsqueda de texto (grep) para navegar el sistema
✗ Diffs de texto para versionar cambios
✗ Commit messages en lenguaje natural
✗ Pull requests como mecanismo de revisión
```

---

## Tabla de decisión rápida

| Situación | Qué hacer |
|---|---|
| Necesito crear una función nueva | Crear nodo `computation` con firma + IR |
| Necesito representar una estructura de datos | Crear nodo `data` con campos tipados |
| Tengo una regla de negocio que documentar | Crear nodo `constraint` (no un comentario) |
| Necesito exponer funcionalidad externamente | Crear nodo `boundary` → `boundary-exposes` → computation |
| Necesito verificar comportamiento | Crear nodo `test` → `tests` → computation |
| Necesito agregar autenticación a algo | Agregar edge `constrained-by → cn:requires-auth`, sin tocar la lógica |
| Necesito encontrar dónde vive una regla | Query: `MATCH (n)-[:constrained-by]->(cn) WHERE cn.enunciado CONTAINS "X"` |
| Necesito entender qué puede fallar | Query: `MATCH (n)-[:produces]->(e:event {subtipo: error}) RETURN e` |
| Necesito ver la historia de un nodo | Traversal de edges `derives-from` hacia atrás |
| Una función necesita cambiar | Protocolo 2 — modificar comportamiento existente |
| Una regla de negocio cambió | Modificar nodo constraint + re-validar constraints |
| El sistema falló en producción | Protocolo 4 — crear test que reproduce el bug, luego corregir |

---

## Métricas de referencia

| Métrica | Objetivo |
|---|---|
| Tokens para edición local | < 800 |
| Tokens para entender todas las reglas de un dominio | < 2,000 |
| Profundidad máxima de contexto | depth-2 |
| Cobertura mínima para deployment | 80% |
| Nodos computation sin constraints | 0 (todos tienen al menos `belongs-to` un dominio) |
| Boundaries sin constraint de auth | 0 |
| Reglas de negocio fuera de nodos constraint | 0 |

Si cualquiera de estos valores está fuera del objetivo, el grafo tiene un problema de diseño que debe resolverse antes de continuar.

---

## Glosario mínimo

| Término | Definición |
|---|---|
| **Nodo semántico** | Unidad atómica de significado en el grafo |
| **Edge tipado** | Relación dirigida con semántica definida entre dos nodos |
| **Content-addressed** | La identidad se deriva del contenido, no de un nombre asignado |
| **IR** | Intermediate Representation — formato binario de conducta compilada |
| **Snapshot** | Estado consistente e inmutable del grafo completo en un punto del tiempo |
| **Delta semántico** | Diferencia entre dos snapshots en términos de nodos y edges, no de texto |
| **Partición** | Subgrafo etiquetado con nodos boundary en sus límites |
| **Alias** | Nombre humano opcional asociado a un nodo, separado de su identidad |
| **Edit locality** | Propiedad: cualquier edición local requiere contexto de profundidad ≤2 |
| **Context budget** | Cantidad máxima de tokens que una operación puede cargar |
| **Constraint verificable** | Regla de negocio con un nodo computation que la verifica automáticamente |
| **Concern transversal** | Auth, logging, rate limiting, caché: viven en edges, no en lógica de computation |
